from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import require_user
from app.config import get_settings
from app.db import get_db
from app.models import ArchitectBlueprintEntry, ArchitectCharacter, Entity, User
from app.version import APP_VERSION

router = APIRouter(prefix="/tools/player-architect")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals.update(app_version=APP_VERSION, app_name=get_settings().app_name)
_md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")
templates.env.filters["architect_markdown"] = lambda value: Markup(_md.render(str(value or "")))

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
ABILITY_LABELS = {"str":"STR","dex":"DEX","con":"CON","int":"INT","wis":"WIS","cha":"CHA"}
ABILITY_NAMES = {"str":"Strength","dex":"Dexterity","con":"Constitution","int":"Intelligence","wis":"Wisdom","cha":"Charisma"}
LEVEL_XP = {1:0,2:300,3:900,4:2700,5:6500,6:14000,7:23000,8:34000,9:48000,10:64000,11:85000,12:100000,13:120000,14:140000,15:165000,16:195000,17:225000,18:265000,19:305000,20:355000}
STEPS = [
    ("identity", "Identity"),
    ("race", "Race / Species"),
    ("class", "Class & Subclass"),
    ("abilities", "Ability Scores"),
    ("background", "Background & Alignment"),
    ("proficiencies", "Proficiencies"),
    ("languages", "Languages"),
    ("feats", "Feats"),
    ("spells", "Cantrips & Spells"),
    ("details", "Character Details"),
    ("review", "Review & Sheet"),
]
STEP_KEYS = {key for key, _ in STEPS}
STAT_OPTIONS = ["STR","DEX","CON","INT","WIS","CHA","HP","AC","PB","Speed","Languages","Proficiencies","Other"]


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def _char_or_404(db: Session, public_id: str, user: User) -> ArchitectCharacter:
    row = db.scalar(select(ArchitectCharacter).where(ArchitectCharacter.public_id == public_id, ArchitectCharacter.user_id == user.id))
    if not row:
        raise HTTPException(404, "Architect character not found")
    return row


def _entity(db: Session, entity_id: int | None) -> Entity | None:
    return db.get(Entity, entity_id) if entity_id else None


def _text(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n\n".join(filter(None, (_text(item).strip() for item in value)))
    if isinstance(value, dict):
        for key in ("desc", "description", "text", "detail", "benefits"):
            if value.get(key) not in (None, "", [], {}):
                return _text(value[key])
        return "\n".join(f"**{k.replace('_',' ').title()}:** {_text(v)}" for k,v in value.items() if k not in {"document","key","id"} and v not in (None,"",[],{}))
    return str(value)


def _entity_description(entity: Entity | None, limit: int = 360) -> str:
    if not entity:
        return ""
    data = entity.data_json or {}
    raw = entity.summary or _text(data.get("desc") or data.get("description") or data.get("descriptions") or data.get("traits") or data.get("features"))
    plain = re.sub(r"\s+", " ", re.sub(r"[*_#`>|]", "", raw or "")).strip()
    return plain if len(plain) <= limit else plain[:limit-1].rstrip() + "…"


def _all_entities(db: Session, kinds: list[str]) -> list[Entity]:
    return list(db.scalars(select(Entity).where(Entity.entity_type.in_(kinds), Entity.is_active.is_(True)).order_by(Entity.name, Entity.source_display_name, Entity.id)).all())


def _subclass_parent_parts(entity: Entity) -> tuple[str, str]:
    """Return normalized parent identifiers from a populated subclass_of key."""
    parent = (entity.data_json or {}).get("subclass_of")
    if isinstance(parent, dict):
        return (str(parent.get("key") or "").casefold(), str(parent.get("name") or "").casefold())
    text = str(parent or "").casefold().strip()
    return (text, text)

def _subclass_parent(entity: Entity) -> str:
    key, name = _subclass_parent_parts(entity)
    return " ".join(part for part in (key, name) if part).strip()


def _subclass_parent_text(entity: Entity) -> str:
    key, name = _subclass_parent_parts(entity)
    return " ".join(dict.fromkeys(part for part in (key, name) if part))


def _class_catalog(db: Session) -> tuple[list[Entity], list[Entity]]:
    """Split the PA class endpoint strictly by the Open5e ``subclass_of`` field.

    Player Architect consumes the cached Open5e ``classe`` endpoint. This
    mirrors the database query used to identify subclasses exactly:

        json_type(data_json, '$.subclass_of') IS NOT NULL
        AND json_type(data_json, '$.subclass_of') <> 'null'
        AND entity_type = 'classe'

    In Python terms, a row is a subclass when the ``subclass_of`` key exists
    and its JSON value is not null. Primary classes are the exact inverse:
    the key is absent or its value is JSON null. No other metadata participates
    in this classification.
    """
    rows = _all_entities(db, ["classe"])
    primary, subclasses = [], []
    for row in rows:
        data = row.data_json or {}
        if "subclass_of" in data and data.get("subclass_of") is not None:
            subclasses.append(row)
        else:
            primary.append(row)
    return primary, subclasses


def _extract_named(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("key") or value.get("label") or "")
    return str(value or "")


def _ability_key(text: str) -> str | None:
    t = text.casefold().strip()
    for short, name in ABILITY_NAMES.items():
        if t in {short, name.casefold()} or name.casefold() in t:
            return short.upper()
    return None


def _auto_entries(entity: Entity | None, how: str) -> list[dict[str, str]]:
    """Best-effort, source-agnostic modifier extraction from cached compendium JSON."""
    if not entity:
        return []
    data = entity.data_json or {}
    entries: list[dict[str, str]] = []
    seen: set[tuple[str,str,str]] = set()

    def add(mod: str, stat: str, note: str):
        key=(mod,stat,note)
        if mod and stat and key not in seen:
            seen.add(key); entries.append({"modifier":mod,"stat":stat,"note":note})

    ability_fields = ["ability_score_increases","ability_score_increase","ability_bonuses","ability_bonus","ability_scores","asi"]
    for field in ability_fields:
        value=data.get(field)
        # Common Open5e/third-party shape: {"dexterity": 2, "wisdom": 1}.
        if isinstance(value, dict) and not any(k in value for k in ("ability","ability_score","attribute","attributes","stat","name","key","bonus","value","modifier","amount")):
            for label, amount in value.items():
                stat=_ability_key(str(label))
                if stat and amount not in (None, ""):
                    try: mod=f"{int(amount):+d}"
                    except Exception: mod=str(amount)
                    add(mod, stat, f"{entity.name} {how.lower()} enhancement")
            value=[]
        if isinstance(value, dict): value=[value]
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                labels = item.get("attributes") or item.get("attribute") or item.get("ability") or item.get("ability_score") or item.get("stat") or item.get("name") or item.get("key")
                labels = labels if isinstance(labels, list) else [labels]
                amount=item.get("bonus", item.get("value", item.get("modifier", item.get("amount"))))
                for label_value in labels:
                    label=_extract_named(label_value)
                    stat=_ability_key(label)
                    if stat and amount not in (None, ""):
                        try: mod=f"{int(amount):+d}"
                        except Exception: mod=str(amount)
                        add(mod, stat, f"{entity.name} {how.lower()} enhancement")
    # Many sources put race bonuses only in prose. Support both compact
    # "+2 Dexterity" wording and SRD-style "Dexterity score increases by 2".
    blob=" ".join([_text(data.get(k)) for k in ("desc","description","traits","benefits","features") if data.get(k)])
    patterns = [
        r"([+-]\d+)\s+(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)",
        r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)(?: score)?\s+(?:increases?|is increased)\s+by\s+(\d+)",
    ]
    for pattern_index, pattern in enumerate(patterns):
        for first, second in re.findall(pattern, blob, re.I):
            if pattern_index == 0:
                amount, ability = first, second
            else:
                ability, amount = first, f"+{second}"
            stat=_ability_key(ability)
            if stat: add(amount,stat,f"{entity.name} {how.lower()} enhancement")

    languages=data.get("languages") or data.get("language")
    values=languages if isinstance(languages,list) else ([languages] if languages else [])
    for value in values:
        name=_extract_named(value)
        if name and name.casefold() not in {"any","choice","choose"}:
            add(f"+{name}","Languages",f"{entity.name} language")

    if how == "Class":
        hit=data.get("hit_die") or data.get("hit_dice")
        if hit:
            text=str(hit); text = text if text.lower().startswith("d") else f"d{text}"
            add(text,"HP",f"{entity.name} class Hit Die")
        saves=data.get("saving_throws") or data.get("saving_throw_proficiencies")
        if saves:
            names=", ".join(_extract_named(x) for x in (saves if isinstance(saves,list) else [saves]) if _extract_named(x))
            if names: add(f"+{names}","Proficiencies",f"{entity.name} saving throw proficiencies")
    return entries


def _sync_auto_blueprint(db: Session, char: ArchitectCharacter, origin_key: str, how: str, entity: Entity | None):
    db.execute(delete(ArchitectBlueprintEntry).where(
        ArchitectBlueprintEntry.architect_character_id == char.id,
        ArchitectBlueprintEntry.origin_kind == "automated",
        ArchitectBlueprintEntry.origin_key == origin_key,
    ))
    for item in _auto_entries(entity, how):
        db.add(ArchitectBlueprintEntry(
            public_id=_uid("pab"), architect_character_id=char.id, origin_kind="automated", origin_key=origin_key,
            how=how, modifier=item["modifier"], stat=item["stat"], note=item["note"], is_locked=True,
        ))


def _blueprint(db: Session, char: ArchitectCharacter) -> list[ArchitectBlueprintEntry]:
    return list(db.scalars(select(ArchitectBlueprintEntry).where(ArchitectBlueprintEntry.architect_character_id == char.id).order_by(ArchitectBlueprintEntry.id)).all())


def _numeric_mod(value: str) -> int:
    m=re.fullmatch(r"\s*([+-]?\d+)\s*", str(value or ""))
    return int(m.group(1)) if m else 0


def _derived(db: Session, char: ArchitectCharacter) -> dict[str, Any]:
    base={a:int((char.base_ability_scores or {}).get(a,10) or 10) for a in ABILITIES}
    mods={a:0 for a in ABILITIES}
    extra={"HP":0,"AC":0,"PB":0,"Speed":0}
    for entry in _blueprint(db,char):
        stat=(entry.stat or "").upper()
        if stat.casefold() in ABILITIES:
            mods[stat.casefold()] += _numeric_mod(entry.modifier)
        elif stat in extra:
            extra[stat] += _numeric_mod(entry.modifier)
    scores={a:base[a]+mods[a] for a in ABILITIES}
    ability_mods={a:math.floor((scores[a]-10)/2) for a in ABILITIES}
    level=max(1,int(char.level or 1)); pb=math.floor((level-1)/4)+2+extra["PB"]
    ac=10+ability_mods["dex"]+extra["AC"]
    # Conservative live HP preview. Exact class features remain blueprint-driven.
    class_entity=_entity(db,char.class_entity_id); hit_die=8
    if class_entity:
        raw=(class_entity.data_json or {}).get("hit_die") or 8
        m=re.search(r"\d+",str(raw)); hit_die=int(m.group()) if m else 8
    hp=max(1, hit_die + ability_mods["con"] + (level-1)*(max(1, hit_die//2+1+ability_mods["con"])) + extra["HP"])
    return {"base":base,"score_mods":mods,"scores":scores,"ability_mods":ability_mods,"pb":pb,"ac":ac,"hp":hp}


def _minimum_requirements(entity: Entity | None) -> dict[str,int]:
    if not entity: return {}
    data=entity.data_json or {}; req={}
    for key in ("minimum_ability_scores","ability_requirements","requirements","prerequisites"):
        value=data.get(key)
        text=json.dumps(value) if value not in (None,"",[],{}) else ""
        for ability, number in re.findall(r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma|STR|DEX|CON|INT|WIS|CHA)[^0-9]{0,20}(\d{1,2})", text, re.I):
            short=_ability_key(ability)
            if short: req[short.casefold()]=max(req.get(short.casefold(),0),int(number))
    return req


def _context(db: Session, char: ArchitectCharacter, step: str, **extra):
    race=_entity(db,char.race_entity_id); cls=_entity(db,char.class_entity_id); sub=_entity(db,char.subclass_entity_id)
    bg=_entity(db,char.background_entity_id); align=_entity(db,char.alignment_entity_id)
    primary_classes, all_subclasses = _class_catalog(db)
    selected_parent_tokens={str(char.class_entity_id or ""), (cls.name if cls else "").casefold(), (cls.canonical_key if cls else "") or "", (cls.slug if cls else "") or ""}
    subclasses=[]
    if cls:
        for row in all_subclasses:
            parent=_subclass_parent(row)
            if any(token and token.casefold() in parent for token in selected_parent_tokens): subclasses.append(row)
    step_index = [key for key, _ in STEPS].index(step)
    prev_step = STEPS[step_index - 1][0] if step_index > 0 else None
    next_step = STEPS[step_index + 1][0] if step_index + 1 < len(STEPS) else None
    implemented_step = step in {"identity", "race", "class", "abilities", "background"}
    return {
        "tools_section":"player-architect","character":char,"step":step,"steps":STEPS,"blueprint_rows":_blueprint(db,char),
        "prev_step": prev_step, "next_step": next_step, "implemented_step": implemented_step,
        "derived":_derived(db,char),"race_entity":race,"class_entity":cls,"subclass_entity":sub,"background_entity":bg,"alignment_entity":align,
        "race_rows":_all_entities(db,["species","race"]),"class_rows":primary_classes,"subclass_rows":subclasses,"all_subclass_rows":all_subclasses,
        "auto_entries":_auto_entries,
        "background_rows":_all_entities(db,["background"]),"alignment_rows":_all_entities(db,["alignment"]),
        "ability_labels":ABILITY_LABELS,"ability_names":ABILITY_NAMES,"abilities":ABILITIES,"level_xp":LEVEL_XP,"stat_options":STAT_OPTIONS,
        "entity_description":_entity_description,"subclass_parent_text":_subclass_parent_text, **extra,
    }


@router.get("", response_class=HTMLResponse)
def architect_home(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    rows=list(db.scalars(select(ArchitectCharacter).where(ArchitectCharacter.user_id==user.id).order_by(ArchitectCharacter.updated_at.desc())).all())
    display=[]
    for row in rows:
        display.append({"row":row,"race":_entity(db,row.race_entity_id),"class":_entity(db,row.class_entity_id)})
    return templates.TemplateResponse(request,"tools_player_architect_home.html",{"tools_section":"player-architect","characters":display})


@router.post("/new")
async def architect_new(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    form=await request.form(); name=str(form.get("name") or "").strip() or "New Character"
    row=ArchitectCharacter(public_id=_uid("pa"),user_id=user.id,name=name,base_ability_scores={a:10 for a in ABILITIES},notes_json={})
    db.add(row); db.commit(); db.refresh(row)
    return RedirectResponse(f"/tools/player-architect/{row.public_id}?step=identity",303)


@router.post("/{public_id}/delete")
def architect_delete(public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    row=_char_or_404(db,public_id,user); db.delete(row); db.commit(); return RedirectResponse("/tools/player-architect",303)


@router.get("/{public_id}", response_class=HTMLResponse)
def architect_edit(request: Request, public_id: str, step: str="identity", user: User = Depends(require_user), db: Session = Depends(get_db)):
    row=_char_or_404(db,public_id,user); active=step if step in STEP_KEYS else "identity"; row.current_step=active; db.commit()
    return templates.TemplateResponse(request,"tools_player_architect.html",_context(db,row,active))


@router.post("/{public_id}/step/{step}")
async def architect_save_step(request: Request, public_id: str, step: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if step not in STEP_KEYS: raise HTTPException(404)
    row=_char_or_404(db,public_id,user); form=await request.form(); error=None
    if step=="identity":
        row.name=str(form.get("name") or row.name).strip() or row.name
        row.brief_description=str(form.get("brief_description") or "").strip() or None
        row.level=max(1,min(20,int(form.get("level") or 1))); row.experience_points=max(int(form.get("experience_points") or 0),LEVEL_XP[row.level])
    elif step=="race":
        entity_id=int(form.get("race_entity_id") or 0) or None; row.race_entity_id=entity_id; _sync_auto_blueprint(db,row,"race","Race",_entity(db,entity_id))
    elif step=="class":
        class_id=int(form.get("class_entity_id") or 0) or None; subclass_id=int(form.get("subclass_entity_id") or 0) or None
        row.class_entity_id=class_id; row.subclass_entity_id=subclass_id
        _sync_auto_blueprint(db,row,"class","Class",_entity(db,class_id)); _sync_auto_blueprint(db,row,"subclass","Subclass",_entity(db,subclass_id))
    elif step=="abilities":
        row.ability_method=str(form.get("ability_method") or "manual")
        row.base_ability_scores={a:max(1,min(30,int(form.get(a) or 10))) for a in ABILITIES}
        db.flush(); derived=_derived(db,row); requirements={}
        for ent in (_entity(db,row.race_entity_id),_entity(db,row.class_entity_id),_entity(db,row.subclass_entity_id)):
            for ability,value in _minimum_requirements(ent).items(): requirements[ability]=max(requirements.get(ability,0),value)
        missing=[f"{ABILITY_NAMES[a]} {value}+" for a,value in requirements.items() if derived["scores"].get(a,0)<value]
        if missing: error="Minimum requirements not met: "+", ".join(missing)
    elif step=="background":
        bg_id=int(form.get("background_entity_id") or 0) or None; al_id=int(form.get("alignment_entity_id") or 0) or None
        row.background_entity_id=bg_id; row.alignment_entity_id=al_id; _sync_auto_blueprint(db,row,"background","Background",_entity(db,bg_id))
    row.current_step=step; db.commit(); db.refresh(row)
    if error:
        return templates.TemplateResponse(request,"tools_player_architect.html",_context(db,row,step,error=error),status_code=422)
    idx=[key for key,_ in STEPS].index(step); next_step=STEPS[min(idx+1,len(STEPS)-1)][0]
    return RedirectResponse(f"/tools/player-architect/{row.public_id}?step={next_step}",303)


@router.post("/{public_id}/blueprint/add")
async def blueprint_add(request: Request, public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    char=_char_or_404(db,public_id,user); form=await request.form()
    if str(form.get("verified") or "") not in {"1","on","true"}: raise HTTPException(400,"Verify the manual blueprint entry before saving")
    stat=str(form.get("stat") or "").strip(); modifier=str(form.get("modifier") or "").strip(); how=str(form.get("how") or "Manual").strip(); note=str(form.get("note") or "").strip()
    if stat not in STAT_OPTIONS or not modifier: raise HTTPException(400,"Stat and modifier are required")
    db.add(ArchitectBlueprintEntry(public_id=_uid("pab"),architect_character_id=char.id,origin_kind="manual",origin_key=None,how=how,modifier=modifier,stat=stat,note=note,is_locked=False)); db.commit()
    return RedirectResponse(f"/tools/player-architect/{char.public_id}?step={char.current_step}",303)


@router.post("/{public_id}/blueprint/{entry_id}/edit")
async def blueprint_edit(request: Request, public_id: str, entry_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    char=_char_or_404(db,public_id,user); entry=db.scalar(select(ArchitectBlueprintEntry).where(ArchitectBlueprintEntry.public_id==entry_id,ArchitectBlueprintEntry.architect_character_id==char.id))
    if not entry or entry.is_locked: raise HTTPException(403,"Automated blueprint entries cannot be edited")
    form=await request.form(); stat=str(form.get("stat") or entry.stat); modifier=str(form.get("modifier") or entry.modifier).strip(); note=str(form.get("note") or "").strip()
    if stat not in STAT_OPTIONS or not modifier: raise HTTPException(400)
    entry.stat=stat; entry.modifier=modifier; entry.how=str(form.get("how") or entry.how); entry.note=note; db.commit()
    return RedirectResponse(f"/tools/player-architect/{char.public_id}?step={char.current_step}",303)


@router.post("/{public_id}/blueprint/{entry_id}/delete")
def blueprint_delete(public_id: str, entry_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    char=_char_or_404(db,public_id,user); entry=db.scalar(select(ArchitectBlueprintEntry).where(ArchitectBlueprintEntry.public_id==entry_id,ArchitectBlueprintEntry.architect_character_id==char.id))
    if not entry or entry.is_locked: raise HTTPException(403,"Automated blueprint entries cannot be deleted")
    db.delete(entry); db.commit(); return RedirectResponse(f"/tools/player-architect/{char.public_id}?step={char.current_step}",303)


@router.get("/entity/{entity_id}/info", response_class=HTMLResponse)
def architect_entity_info(request: Request, entity_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    entity=db.get(Entity,entity_id)
    if not entity or not entity.is_active: raise HTTPException(404)
    data=entity.data_json or {}; body=_text(data.get("desc") or data.get("description") or data.get("descriptions") or data.get("traits") or data.get("features") or entity.summary)
    return templates.TemplateResponse(request,"player_architect_entity_info.html",{"entity":entity,"body":body})
