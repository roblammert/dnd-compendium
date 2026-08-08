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
STAT_OPTIONS = ["STR","DEX","CON","INT","WIS","CHA","HP","AC","PB","Speed","Hit Dice","Weapon Proficiencies","Armor Proficiencies","Tool Proficiencies","Saving Throws","Skill Proficiencies","Languages","Proficiencies","Cantrips","Spells","Feats","Other"]


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



CORE_TRAIT_ALIASES = {
    "armor": "Armor Proficiencies",
    "armor training": "Armor Proficiencies",
    "armor proficiency": "Armor Proficiencies",
    "armor proficiencies": "Armor Proficiencies",
    "weapon": "Weapon Proficiencies",
    "weapons": "Weapon Proficiencies",
    "weapon proficiency": "Weapon Proficiencies",
    "weapon proficiencies": "Weapon Proficiencies",
    "tool": "Tool Proficiencies",
    "tools": "Tool Proficiencies",
    "tool proficiency": "Tool Proficiencies",
    "tool proficiencies": "Tool Proficiencies",
    "saving throw": "Saving Throws",
    "saving throws": "Saving Throws",
    "saving throw proficiency": "Saving Throws",
    "saving throw proficiencies": "Saving Throws",
    "skill": "Skill Proficiencies",
    "skills": "Skill Proficiencies",
    "skill proficiency": "Skill Proficiencies",
    "skill proficiencies": "Skill Proficiencies",
    "languages": "Languages",
    "language": "Languages",
    "cantrips": "Cantrips",
    "spells": "Spells",
    "feats": "Feats",
    "starting equipment": "Other",
}



def _clean_rule_value(value: Any) -> str:
    text = re.sub(r"\s+", " ", _text(value or "")).strip()
    return text.strip(" |-:")


def _markdown_table_pairs(text: str) -> list[tuple[str, str]]:
    """Extract simple two-column Markdown tables used by Open5e core-trait rows."""
    rows: list[tuple[str, str]] = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or all(re.fullmatch(r"[-: ]+", cell or "-") for cell in cells[:2]):
            continue
        label, value = cells[0], " | ".join(cells[1:]).strip()
        if label and value and label.casefold() not in {"detail", "value"}:
            rows.append((label, value))
    return rows


def _bold_label_pairs(text: str) -> list[tuple[str, str]]:
    """Extract ``**Weapons:** ...`` style proficiency lines from 2014 class data."""
    pairs: list[tuple[str, str]] = []
    for match in re.finditer(r"\*\*([^*:\r\n]+):\*\*\s*([^\r\n]+)", str(text or "")):
        label, value = match.group(1).strip(), match.group(2).strip()
        if label and value:
            pairs.append((label, value))
    return pairs


def _walk_rule_nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_rule_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_rule_nodes(child)


def _class_rule_pairs(entity: Entity | None) -> list[tuple[str, str]]:
    """Collect normalized class rule labels from raw Open5e class JSON.

    This intentionally accepts both older prose proficiency features and newer
    CORE_TRAITS_TABLE Markdown tables.  It is source agnostic because Player
    Architect can use the entire cached compendium.
    """
    if not entity:
        return []
    data = entity.data_json or {}
    pairs: list[tuple[str, str]] = []

    # Direct structured keys found across Open5e and third-party sources.
    direct = {
        "armor proficiencies": ("armor", "armor_training", "armor_proficiencies"),
        "weapon proficiencies": ("weapons", "weapon_proficiencies"),
        "tool proficiencies": ("tools", "tool_proficiencies"),
        "skill proficiencies": ("skills", "skill_proficiencies"),
        "languages": ("languages",),
        "cantrips": ("cantrips",),
        "spells": ("spells", "spellcasting"),
        "feats": ("feats",),
        "starting equipment": ("starting_equipment",),
    }
    for label, keys in direct.items():
        for key in keys:
            if data.get(key) not in (None, "", [], {}):
                pairs.append((label, _clean_rule_value(data[key])))
                break

    # Feature-shaped objects can embed either prose or Markdown tables.
    for node in _walk_rule_nodes(data):
        desc = node.get("desc") or node.get("description")
        if not isinstance(desc, str) or not desc.strip():
            continue
        ftype = str(node.get("feature_type") or node.get("type") or "").casefold()
        name = str(node.get("name") or "").casefold()
        if ftype in {"proficiencies", "core_traits_table", "core traits table"} or "proficien" in name or "core" in name:
            pairs.extend(_markdown_table_pairs(desc))
            pairs.extend(_bold_label_pairs(desc))

    # Some class records store the proficiency/core-traits description at top level.
    top_desc = data.get("desc") or data.get("description")
    if isinstance(top_desc, str):
        pairs.extend(_markdown_table_pairs(top_desc))
        pairs.extend(_bold_label_pairs(top_desc))

    normalized: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, value in pairs:
        label_key = re.sub(r"\s+", " ", str(label).replace("_", " ")).strip().casefold()
        stat = CORE_TRAIT_ALIASES.get(label_key)
        cleaned = _clean_rule_value(value)
        # Class saving throws are authoritative only from data_json.saving_throws.
        if stat == "Saving Throws":
            continue
        if stat and cleaned:
            key = (stat, cleaned.casefold())
            if key not in seen:
                seen.add(key)
                normalized.append((stat, cleaned))
    return normalized


def _requires_choice(text: str) -> bool:
    return bool(re.search(r"\b(choose|choice|select|pick|one of|either\b|or another)\b", str(text or ""), re.I))


def _class_choice_notes(entity: Entity | None, how: str = "Class") -> list[dict[str, str]]:
    if not entity:
        return []
    notes: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for stat, instruction in _class_rule_pairs(entity):
        if _requires_choice(instruction):
            key = (stat, instruction.casefold())
            if key not in seen:
                seen.add(key)
                notes.append({
                    "how": how,
                    "stat": stat,
                    "instruction": instruction,
                    "note": f"{entity.name}: player decision required",
                })
    return notes


def _meaningful_modifier(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.casefold() not in {"none", "n/a", "na", "—", "-", "0", "+0", "0.0", "+0.0"}


def _entity_source(entity: Entity | None) -> str:
    if not entity:
        return "Local Compendium"
    return str(getattr(entity, "source_display_name", None) or getattr(entity, "source_document", None) or getattr(entity, "game_system_name", None) or "Local Compendium")


def _class_hit_dice_entry(entity: Entity | None) -> dict[str, str] | None:
    if not entity:
        return None
    data = entity.data_json or {}
    hp = data.get("hit_points") if isinstance(data.get("hit_points"), dict) else {}
    raw_name = hp.get("hit_dice_name") or ""
    raw_die = hp.get("hit_dice") or data.get("hit_die") or data.get("hit_dice") or ""
    text = str(raw_name or raw_die).strip()
    if not text:
        return None
    m = re.search(r"(\d*d\d+|d\d+)", text, re.I)
    if not m:
        m = re.search(r"(\d+)", text)
        die = f"1d{m.group(1)}" if m else ""
    else:
        die = m.group(1).lower()
        if die.startswith("d"):
            die = "1" + die
    if not die:
        return None
    modifier = f"{die} /{entity.name} Level"
    return {"modifier": modifier, "stat": "Hit Dice", "note": f"{entity.name} Hit Dice"}


def _class_saving_throw_entry(entity: Entity | None) -> dict[str, str] | None:
    if not entity:
        return None
    values = (entity.data_json or {}).get("saving_throws")
    if not isinstance(values, list):
        return None
    names: list[str] = []
    for item in values:
        name = _extract_named(item).strip()
        if name and name.casefold() not in {n.casefold() for n in names}:
            names.append(name)
    if not names:
        return None
    return {"modifier": "+" + ", ".join(names), "stat": "Saving Throws", "note": f"{entity.name} saving throws"}


def _class_proficiency_entries(entity: Entity | None, how: str = "Class") -> list[dict[str, str]]:
    """Convert deterministic class proficiency rules into locked Blueprint rows.

    Saving throws and Hit Dice are parsed separately from their authoritative
    structured JSON fields. Choice rules are surfaced by ``_class_choice_notes``.
    """
    if not entity:
        return []
    result: list[dict[str, str]] = []
    allowed = {"Weapon Proficiencies", "Armor Proficiencies", "Tool Proficiencies", "Skill Proficiencies", "Languages", "Cantrips", "Spells", "Feats"}
    for stat, value in _class_rule_pairs(entity):
        if stat not in allowed or _requires_choice(value) or not _meaningful_modifier(value):
            continue
        modifier = str(value) if str(value).startswith(("+", "-")) else f"+{value}"
        result.append({"modifier": modifier, "stat": stat, "note": f"{entity.name} {stat.lower()}"})
    return result


def _auto_entries(entity: Entity | None, how: str) -> list[dict[str, str]]:
    """Best-effort, source-agnostic modifier extraction from cached compendium JSON."""
    if not entity:
        return []
    data = entity.data_json or {}
    entries: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    source = _entity_source(entity)

    def add(mod: str, stat: str, note: str):
        mod = str(mod or "").strip()
        stat = str(stat or "").strip()
        if not _meaningful_modifier(mod) or not stat:
            return
        key = (mod.casefold(), stat.casefold())
        if key in seen:
            return
        seen.add(key)
        entries.append({"modifier": mod, "stat": stat, "source": source, "note": note})

    # Ability enhancements are meaningful for race/background-style records.
    # Class primary-ability declarations are not modifiers and must not enter the ledger.
    if how not in {"Class", "Subclass"}:
        ability_fields = ["ability_score_increases","ability_score_increase","ability_bonuses","ability_bonus","ability_scores","asi"]
        for field in ability_fields:
            value=data.get(field)
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
                        stat=_ability_key(_extract_named(label_value))
                        if stat and amount not in (None, ""):
                            try: mod=f"{int(amount):+d}"
                            except Exception: mod=str(amount)
                            add(mod, stat, f"{entity.name} {how.lower()} enhancement")

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

    if how in {"Class", "Subclass"}:
        if how == "Class":
            hit = _class_hit_dice_entry(entity)
            if hit:
                add(hit["modifier"], hit["stat"], hit["note"])
            saves = _class_saving_throw_entry(entity)
            if saves:
                add(saves["modifier"], saves["stat"], saves["note"])
        for item in _class_proficiency_entries(entity, how):
            add(item["modifier"], item["stat"], item["note"])
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
            how=how, modifier=item["modifier"], stat=item["stat"], source=item.get("source") or _entity_source(entity), note=item["note"], is_locked=True,
        ))


def _blueprint(db: Session, char: ArchitectCharacter) -> list[ArchitectBlueprintEntry]:
    rows = list(db.scalars(select(ArchitectBlueprintEntry).where(ArchitectBlueprintEntry.architect_character_id == char.id).order_by(ArchitectBlueprintEntry.id)).all())
    result: list[ArchitectBlueprintEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = ((row.how or "").casefold(), (row.modifier or "").casefold(), (row.stat or "").casefold())
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


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
        class_data = class_entity.data_json or {}
        hp_data = class_data.get("hit_points") if isinstance(class_data.get("hit_points"), dict) else {}
        raw = hp_data.get("hit_dice") or class_data.get("hit_die") or class_data.get("hit_dice") or 8
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
        "blueprint_choice_notes":_class_choice_notes(cls, "Class") + _class_choice_notes(sub, "Subclass"),
        "prev_step": prev_step, "next_step": next_step, "implemented_step": implemented_step,
        "derived":_derived(db,char),"race_entity":race,"class_entity":cls,"subclass_entity":sub,"background_entity":bg,"alignment_entity":align,
        "race_rows":_all_entities(db,["species","race"]),"class_rows":primary_classes,"subclass_rows":subclasses,"all_subclass_rows":all_subclasses,
        "auto_entries":_auto_entries,"class_choice_notes":_class_choice_notes,
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
    destination=str(form.get("pa_navigation_destination") or "").strip()
    if destination == "library":
        return RedirectResponse("/tools/player-architect",303)
    if destination in STEP_KEYS:
        return RedirectResponse(f"/tools/player-architect/{row.public_id}?step={destination}",303)
    idx=[key for key,_ in STEPS].index(step); next_step=STEPS[min(idx+1,len(STEPS)-1)][0]
    return RedirectResponse(f"/tools/player-architect/{row.public_id}?step={next_step}",303)


@router.post("/{public_id}/blueprint/add")
async def blueprint_add(request: Request, public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    char=_char_or_404(db,public_id,user); form=await request.form()
    if str(form.get("verified") or "") not in {"1","on","true"}: raise HTTPException(400,"Verify the manual blueprint entry before saving")
    stat=str(form.get("stat") or "").strip(); modifier=str(form.get("modifier") or "").strip(); how=str(form.get("how") or "Manual").strip(); note=str(form.get("note") or "").strip()
    if stat not in STAT_OPTIONS or not modifier: raise HTTPException(400,"Stat and modifier are required")
    db.add(ArchitectBlueprintEntry(public_id=_uid("pab"),architect_character_id=char.id,origin_kind="manual",origin_key=None,how=how,modifier=modifier,stat=stat,source="Manual",note=note,is_locked=False)); db.commit()
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
