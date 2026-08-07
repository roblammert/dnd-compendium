
from __future__ import annotations
import json, random, re
from fractions import Fraction
from pathlib import Path
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.models import Entity, LexiconTerm, UserEntityList
from app.services import build_monster_card, build_weapon_card, format_cost, format_weight, _numeric_value

router = APIRouter(prefix="/tools")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["app_version"] = "0.31.3"
templates.env.globals["app_name"] = get_settings().app_name

_tool_markdown = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": False}).enable("table")

def _render_tool_markdown(value):
    if value in (None, ""):
        return Markup("")
    return Markup(_tool_markdown.render(str(value)))

templates.env.filters["render_markdown"] = _render_tool_markdown

def _structured_markdown(value) -> str:
    """Turn Open5e list/dict description payloads into readable Markdown."""
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        blocks = [_structured_markdown(item).strip() for item in value]
        return "\n\n".join(block for block in blocks if block)
    if isinstance(value, dict):
        title = value.get("name") or value.get("title") or value.get("label")
        text = value.get("desc") or value.get("description") or value.get("text") or value.get("detail")
        if text is not None:
            body = _structured_markdown(text).strip()
            return f"**{title}.** {body}" if title and body else (body or str(title or ""))
        ignored = {"document", "gamesystem", "key", "id", "url", "slug"}
        lines = []
        for key, item in value.items():
            if key in ignored or item in (None, "", [], {}):
                continue
            rendered = _structured_markdown(item).strip()
            if rendered:
                lines.append(f"**{key.replace('_', ' ').title()}:** {rendered}")
        return "\n\n".join(lines)
    return str(value)

XP_THRESHOLDS = {
1:(25,50,75,100),2:(50,100,150,200),3:(75,150,225,400),4:(125,250,375,500),
5:(250,500,750,1100),6:(300,600,900,1400),7:(350,750,1100,1700),8:(450,900,1400,2100),
9:(550,1100,1600,2400),10:(600,1200,1900,2800),11:(800,1600,2400,3600),12:(1000,2000,3000,4500),
13:(1100,2200,3400,5100),14:(1250,2500,3800,5700),15:(1400,2800,4300,6400),16:(1600,3200,4800,7200),
17:(2000,3900,5900,8800),18:(2100,4200,6300,9500),19:(2400,4900,7300,10900),20:(2800,5700,8500,12700),
}
DIFFICULTY_INDEX={"easy":0,"medium":1,"hard":2,"deadly":3}

def _number(value, default=0.0):
    if isinstance(value, dict):
        for key in ("value","amount","score","rating","xp"):
            if key in value: return _number(value[key], default)
    if value in (None,""): return default
    try:
        text=str(value).strip()
        return float(Fraction(text)) if "/" in text else float(re.search(r"-?\d+(?:\.\d+)?", text).group())
    except Exception: return default

def _monster_row(entity):
    data=entity.data_json or {}; card=build_monster_card(entity)
    cr=_number(data.get("challenge_rating", data.get("cr", 0)))
    xp=_number(data.get("xp", data.get("experience_points", 0)))
    return {"entity":entity,"cr":cr,"xp":int(xp),"hp":card.get("hit_points","—"),"ac":card.get("armor_class","—")}

def _tool_context(section, **extra):
    return {"tools_section":section, **extra}

@router.get("")
def tools_home(): return RedirectResponse("/tools/coin-converter",303)

@router.get("/coin-converter", response_class=HTMLResponse)
def coin_converter(request: Request):
    return templates.TemplateResponse(request,"tools_coin_converter.html",_tool_context("coin-converter"))

def _owned_lists(request: Request, db: Session):
    user = getattr(request.state, "user", None)
    if not user: return []
    return list(db.scalars(select(UserEntityList).where(UserEntityList.owner_id == user.id).order_by(UserEntityList.name)).all())


def _extract_named(value):
    if isinstance(value, dict): return value.get("name") or value.get("key") or ""
    return value or ""


def _loadout_row(entity: Entity, *, kept=False, item_index=None):
    data = entity.data_json or {}
    fallback = None
    if entity.entity_type == "weapon" and item_index is not None:
        fallback = _select_item_fallback(entity, _matching_item_candidates(entity, item_index))
    card = build_weapon_card(entity, fallback_item=fallback) if entity.entity_type == "weapon" else None
    cost_raw = _equipment_value(data, "cost")
    weight_raw = _equipment_value(data, "weight")
    if fallback is not None:
        fdata = fallback.data_json or {}
        if _numeric_value(cost_raw) in (None, 0): cost_raw = _equipment_value(fdata, "cost")
        if _numeric_value(weight_raw) in (None, 0): weight_raw = _equipment_value(fdata, "weight")
    cost = format_cost(cost_raw, present=cost_raw not in (None, "", [], {}))
    weight = format_weight(weight_raw, present=weight_raw not in (None, "", [], {}))
    armor = data.get("armor") if isinstance(data.get("armor"), dict) else data
    ac = _number(armor.get("base_ac", armor.get("armor_class", armor.get("ac", 0)))) if isinstance(armor, dict) else 0
    stealth = bool(armor.get("stealth_disadvantage") or armor.get("stealth_disadvantage_override")) if isinstance(armor, dict) else False
    strength = _number(armor.get("strength_requirement", armor.get("strength_score", 0))) if isinstance(armor, dict) else 0
    return {"entity":entity,"kept":kept,"cost":cost.get("value", "Unknown"),"cost_tooltip":cost.get("tooltip", ""),"cost_gp":_numeric_value(cost_raw) or 0,"weight":weight,"weight_value":_numeric_value(weight_raw) or 0,"ac":int(ac) if ac else "—","stealth":stealth,"strength":int(strength) if strength else "—"}


@router.get("/loadout-generator", response_class=HTMLResponse)
def loadout_generator(request: Request, generate: int = 0, count: int = 8, max_cost_gp: float = 100, max_weight: float = 100, generation_basis: str = "both", include_weapons: int | None = None, include_equipment: int | None = None, keep: list[str] = Query(default=[]), db: Session = Depends(get_db)):
    initial = not bool(generate)
    include_weapons = True if initial else bool(include_weapons)
    include_equipment = True if initial else bool(include_equipment)
    count=max(1,min(30,count)); max_cost_gp=max(0,max_cost_gp); max_weight=max(0,max_weight)
    generation_basis = generation_basis if generation_basis in {"cost","weight","both"} else "both"
    item_entities=list(db.scalars(select(Entity).where(Entity.entity_type=="item",Entity.is_active.is_(True))).all()); item_index=_build_item_index(item_entities)
    entities=list(db.scalars(select(Entity).where(Entity.entity_type.in_(["item","weapon"]),Entity.is_active.is_(True)).order_by(func.random()).limit(1500)).all())
    by_id={e.public_id:e for e in entities}; rows=[]; seen=set()
    for pid in keep:
        if pid in by_id and pid not in seen: rows.append(_loadout_row(by_id[pid],kept=True,item_index=item_index)); seen.add(pid)
    if generate:
        for entity in entities:
            if len(rows)>=count: break
            if entity.public_id in seen: continue
            if entity.entity_type=="weapon" and not include_weapons: continue
            if entity.entity_type=="item" and not include_equipment: continue
            row=_loadout_row(entity,item_index=item_index)
            if generation_basis in {"cost","both"} and row["cost_gp"]>max_cost_gp: continue
            if generation_basis in {"weight","both"} and row["weight_value"]>max_weight: continue
            rows.append(row); seen.add(entity.public_id)
    params={"count":count,"max_cost_gp":max_cost_gp,"max_weight":max_weight,"generation_basis":generation_basis,"include_weapons":include_weapons,"include_equipment":include_equipment}
    return templates.TemplateResponse(request,"tools_loadout_generator.html",_tool_context("loadout-generator",rows=rows,params=params,total_weight=sum(r["weight_value"] for r in rows),total_cost=sum(r["cost_gp"] for r in rows),best_ac=max([r["ac"] for r in rows if isinstance(r["ac"],int)] or [0]),stealth_count=sum(1 for r in rows if r["stealth"]),user_lists=_owned_lists(request,db)))


@router.get("/feat-evaluator", response_class=HTMLResponse)
def feat_evaluator(request: Request, character_level: int = 1, strength: int = 10, dexterity: int = 10, constitution: int = 10, intelligence: int = 10, wisdom: int = 10, charisma: int = 10, proficiency: str = "", db: Session = Depends(get_db)):
    scores={"strength":strength,"dexterity":dexterity,"constitution":constitution,"intelligence":intelligence,"wisdom":wisdom,"charisma":charisma}
    feats=list(db.scalars(select(Entity).where(Entity.entity_type=="feat",Entity.is_active.is_(True)).order_by(Entity.name)).all()); rows=[]
    for feat in feats:
        data=feat.data_json or {}; prereq=data.get("prerequisites") or data.get("prerequisite") or []
        text=json.dumps(prereq).casefold() if prereq else ""; eligible=True; reasons=[]
        level_match=re.search(r"level[^0-9]*(\d+)",text)
        if level_match and character_level<int(level_match.group(1)): eligible=False; reasons.append(f"Level {level_match.group(1)}")
        for ability,score in scores.items():
            m=re.search(rf"{ability}[^0-9]*(\d+)",text)
            if m and score<int(m.group(1)): eligible=False; reasons.append(f"{ability.title()} {m.group(1)}")
        if proficiency and "proficien" in text and proficiency.casefold() not in text: eligible=False; reasons.append(proficiency)
        benefits=data.get("benefits") or data.get("desc") or data.get("description") or ""
        summary = _structured_markdown(benefits)
        requirements = ", ".join(reasons) if reasons else ("None detected" if not text else _structured_markdown(prereq))
        rows.append({"entity":feat,"eligible":eligible,"requirements":requirements,"summary":summary})
    return templates.TemplateResponse(request,"tools_feat_evaluator.html",_tool_context("feat-evaluator",rows=rows,params={"character_level":character_level,**scores,"proficiency":proficiency}))


@router.get("/weapon-evaluator", response_class=HTMLResponse)
def weapon_evaluator(request: Request, search: str = "", game_system: str = "", compare: list[str] = Query(default=[]), db: Session = Depends(get_db)):
    all_weapons=list(db.scalars(select(Entity).where(Entity.entity_type=="weapon",Entity.is_active.is_(True)).order_by(Entity.name)).all()); item_entities=list(db.scalars(select(Entity).where(Entity.entity_type=="item",Entity.is_active.is_(True))).all()); item_index=_build_item_index(item_entities)
    systems_by_key = {}
    for weapon in all_weapons:
        key = (weapon.game_system_key or "").strip()
        name = (weapon.game_system_name or key or "Unknown").strip()
        if key:
            systems_by_key.setdefault(key, name)
    game_systems = [{"key": key, "name": systems_by_key[key]} for key in sorted(systems_by_key, key=lambda value: systems_by_key[value].casefold())]
    weapons=all_weapons
    initially_visible = [w for w in weapons if (not search or search.casefold() in w.name.casefold()) and (not game_system or (w.game_system_key or "") == game_system)]
    chosen=[w for w in all_weapons if w.public_id in compare][:6] if compare else initially_visible[:4]
    rows=[]
    for entity in chosen:
        data=entity.data_json or {}; fallback=_select_item_fallback(entity,_matching_item_candidates(entity,item_index)); card=build_weapon_card(entity,fallback_item=fallback)
        damage=data.get("damage_dice") or _equipment_value(data,"damage_dice") or "—"; damage_type=_extract_named(data.get("damage_type") or _equipment_value(data,"damage_type"))
        props=data.get("properties") or _equipment_value(data,"properties") or []; prop_names=[]
        for prop in props if isinstance(props,list) else [props]:
            pobj=prop.get("property",prop) if isinstance(prop,dict) else prop; prop_names.append(str(_extract_named(pobj)))
        cost=_summary_value(card,"Cost") or {}; cost_value=cost.get("value") if isinstance(cost,dict) else cost
        if isinstance(cost_value,dict): cost_value=cost_value.get("value") or cost_value.get("text")
        rows.append({"entity":entity,"damage":f"{damage} {damage_type}".strip(),"properties":", ".join(filter(None,prop_names)) or "—","range":f"{data.get('range',0)}/{data.get('long_range',0)} {data.get('distance_unit','feet')}","cost":cost_value or "Unknown","cost_tooltip":cost.get("tooltip","") if isinstance(cost,dict) else ""})
    return templates.TemplateResponse(request,"tools_weapon_evaluator.html",_tool_context("weapon-evaluator",weapons=weapons,rows=rows,search=search,game_system=game_system,game_systems=game_systems,compare=compare))

@router.get("/encounter-builder", response_class=HTMLResponse)
def encounter_builder(
    request: Request,
    generate: int = 0,
    mode: str = "xp_budget",
    cr_min: float = 0,
    cr_max: float = 5,
    monster_count: int = 4,
    party_size: int = 4,
    average_party_level: int = 5,
    party_level: list[int] = Query(default=[]),
    difficulty: str = "medium",
    scale_mode: str = "none",
    baseline_party_size: int = 4,
    composition: str = "mixed",
    objective: str = "defeat",
    terrain: str = "open",
    pace: str = "standard",
    creature_type: str = "any",
    keep: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    valid_modes = {"random_cr", "xp_budget", "adjusted_xp", "lazy_story", "composition"}
    mode = mode if mode in valid_modes else "xp_budget"
    difficulty = difficulty if difficulty in {"medium", "hard", "deadly"} else "medium"
    scale_mode = scale_mode if scale_mode in {"none", "variable", "lazy_dm"} else "none"
    composition = composition if composition in {"solo", "duo", "mixed", "patrol", "horde"} else "mixed"
    objective = objective if objective in {"defeat", "survive", "protect", "escape", "control", "interrupt"} else "defeat"
    terrain = terrain if terrain in {"open", "tight", "vertical", "hazardous", "aquatic", "dark"} else "open"
    pace = pace if pace in {"quick", "standard", "set_piece"} else "standard"

    submitted_levels = [max(1, min(20, int(level))) for level in party_level if int(level) > 0]
    needs_exact_party = mode in {"xp_budget", "adjusted_xp", "lazy_story", "composition"}
    if needs_exact_party:
        levels = submitted_levels or [5, 5, 5, 5]
    else:
        party_size = max(1, min(20, party_size))
        average_party_level = max(1, min(20, average_party_level))
        levels = [average_party_level] * party_size

    monsters = list(db.scalars(select(Entity).where(Entity.entity_type == "monster", Entity.is_active.is_(True)).order_by(Entity.name)).all())
    all_rows = [_monster_row(entity) for entity in monsters]
    for row in all_rows:
        data = row["entity"].data_json or {}
        kind = data.get("type") or data.get("creature_type") or "Unknown"
        if isinstance(kind, dict): kind = kind.get("name") or kind.get("key") or "Unknown"
        row["creature_type"] = str(kind).title()
    creature_types = sorted({row["creature_type"] for row in all_rows if row["creature_type"] != "Unknown"})
    if creature_type != "any":
        filtered_rows = [row for row in all_rows if row["creature_type"].casefold() == creature_type.casefold()]
    else:
        filtered_rows = all_rows
    row_by_id = {row["entity"].public_id: row for row in all_rows}

    selected, seen = [], set()
    for public_id in keep:
        row = row_by_id.get(public_id)
        if row and public_id not in seen:
            selected.append(dict(row, kept=True)); seen.add(public_id)

    difficulty_index = DIFFICULTY_INDEX[difficulty]
    budget_breakdown = []
    budget = None
    if mode in {"xp_budget", "adjusted_xp"}:
        for index, level in enumerate(levels, start=1):
            threshold = XP_THRESHOLDS[level][difficulty_index]
            budget_breakdown.append({"member": index, "level": level, "xp": threshold})
        budget = sum(entry["xp"] for entry in budget_breakdown)

    party_size = len(levels)
    total_party_levels = sum(levels)
    average_level = total_party_levels / max(1, party_size)
    ratio = party_size / max(1, baseline_party_size)
    lazy_multiplier = 0.25 if average_level < 5 else 0.5
    lazy_limit = lazy_multiplier * total_party_levels

    def encounter_multiplier(count: int) -> float:
        if count <= 1: mult = 1
        elif count == 2: mult = 1.5
        elif count <= 6: mult = 2
        elif count <= 10: mult = 2.5
        elif count <= 14: mult = 3
        else: mult = 4
        if party_size < 3: mult = min(5, mult + .5)
        elif party_size > 5: mult = max(1, mult - .5)
        return mult

    def adjusted_xp(rows):
        return round(sum(row["xp"] for row in rows) * encounter_multiplier(len(rows)))

    def add_random(pool, count):
        random.shuffle(pool)
        for row in pool[:max(0, count)]:
            if row["entity"].public_id not in seen:
                selected.append(dict(row, kept=False)); seen.add(row["entity"].public_id)

    target_count = max(1, min(30, monster_count))
    if mode == "composition":
        target_count = {"solo":1,"duo":2,"mixed":4,"patrol":6,"horde":10}[composition]

    if generate:
        available = [row for row in filtered_rows if row["entity"].public_id not in seen]
        slots_remaining = max(0, target_count - len(selected))
        if mode == "random_cr":
            pool = [row for row in available if cr_min <= row["cr"] <= cr_max]
            add_random(pool, slots_remaining)
        elif mode == "xp_budget":
            remaining = max(0, (budget or 0) - sum(row["xp"] for row in selected))
            pool = sorted([row for row in available if 0 < row["xp"] <= remaining], key=lambda r:r["xp"], reverse=True)
            while pool and remaining > 0 and len(selected) < target_count:
                eligible = [row for row in pool if row["xp"] <= remaining]
                if not eligible: break
                row = random.choice(eligible[:min(10,len(eligible))])
                selected.append(dict(row, kept=False)); seen.add(row["entity"].public_id)
                remaining -= row["xp"]; pool.remove(row)
        elif mode == "adjusted_xp":
            pool = [row for row in available if row["xp"] > 0]
            random.shuffle(pool); pool.sort(key=lambda r:r["xp"], reverse=True)
            for row in pool:
                trial = selected + [row]
                if adjusted_xp(trial) <= (budget or 0):
                    selected.append(dict(row, kept=False)); seen.add(row["entity"].public_id)
                if len(selected) >= target_count: break
        elif mode == "lazy_story":
            target = lazy_limit * {"medium":.65,"hard":.85,"deadly":1.0}[difficulty]
            pool = [row for row in available if row["cr"] > 0 and row["cr"] <= max(target, .25)]
            random.shuffle(pool); pool.sort(key=lambda r:r["cr"], reverse=True)
            for row in pool:
                if sum(r["cr"] for r in selected) + row["cr"] <= target:
                    selected.append(dict(row, kept=False)); seen.add(row["entity"].public_id)
                if len(selected) >= target_count: break
        elif mode == "composition":
            profile = target_count
            target_cr = max(.125, average_level / {"solo":1.1,"duo":1.8,"mixed":3.2,"patrol":5,"horde":8}[composition])
            pool = sorted(available, key=lambda r: abs(r["cr"]-target_cr))
            window = pool[:max(profile*4, 12)]
            add_random(window, max(0, profile-len(selected)))

    raw_xp = sum(row["xp"] for row in selected)
    multiplier = encounter_multiplier(len(selected))
    adjusted_total = adjusted_xp(selected) if selected else 0
    total_cr = sum(row["cr"] for row in selected)
    active_total = adjusted_total if mode == "adjusted_xp" else raw_xp
    budget_status = None
    if budget is not None:
        if active_total > budget: budget_status = "Over budget"
        elif active_total >= budget * .85: budget_status = "On target"
        else: budget_status = "Under budget"
    lazy_status = "Within benchmark" if total_cr <= lazy_limit else "Above benchmark"

    objective_notes = {
        "defeat":"Straightforward elimination; reserve terrain features for movement and cover.",
        "survive":"Build pressure in waves and define a visible round limit.",
        "protect":"Give enemies routes and priorities beyond attacking the characters.",
        "escape":"Use pursuit pressure, exits, and escalating environmental obstacles.",
        "control":"Add interactable zones whose ownership changes the fight.",
        "interrupt":"Give the opposition a countdown, ritual, device, or escape plan.",
    }
    terrain_notes = {
        "open":"Favor mobility, ranged lines, and scattered cover.","tight":"Limit frontage and emphasize chokepoints.",
        "vertical":"Add elevation, falling risk, ladders, ledges, or flight.","hazardous":"Use recurring environmental effects with clear telegraphs.",
        "aquatic":"Account for swim speeds, visibility, and three-dimensional movement.","dark":"Use concealment, light sources, and ambush routes.",
    }
    pace_targets = {"quick":"2–3 rounds", "standard":"3–5 rounds", "set_piece":"5–7 rounds"}

    for row in selected:
        row["scaled_hp"], row["scaled_ac"], row["scale_note"] = row["hp"], row["ac"], "Original"
        if scale_mode == "variable":
            hp, ac = _number(row["hp"]), _number(row["ac"])
            row["scaled_hp"] = round(hp * ratio) if hp else row["hp"]
            row["scaled_ac"] = round(ac + ((ratio - 1) / .5)) if ac else row["ac"]
            row["scale_note"] = f"R {ratio:.2f}"
        elif scale_mode == "lazy_dm": row["scale_note"] = "Benchmark only"

    params = {"mode":mode,"cr_min":cr_min,"cr_max":cr_max,"monster_count":monster_count,"party_size":party_size,
              "average_party_level":average_party_level,"party_levels":levels,"difficulty":difficulty,"scale_mode":scale_mode,
              "baseline_party_size":baseline_party_size,"composition":composition,"objective":objective,"terrain":terrain,
              "pace":pace,"creature_type":creature_type,"target_count":target_count}
    return templates.TemplateResponse(request,"tools_encounter_builder.html",_tool_context("encounter-builder",
        selected=selected,budget=budget,budget_breakdown=budget_breakdown,budget_status=budget_status,total_xp=raw_xp,
        adjusted_xp=adjusted_total,encounter_multiplier=multiplier,total_cr=total_cr,lazy_limit=lazy_limit,lazy_status=lazy_status,
        ratio=ratio,party_size=party_size,total_party_levels=total_party_levels,average_level=average_level,params=params,
        creature_types=creature_types,objective_note=objective_notes[objective],terrain_note=terrain_notes[terrain],
        pace_target=pace_targets[pace],user_lists=_owned_lists(request,db)))


@router.get("/loot-generator", response_class=HTMLResponse)
def loot_generator(
    request: Request,
    generate: int = 0,
    count_min: int = 8,
    count_max: int = 12,
    max_value_gp: float = 40,
    max_total_value_gp: float = 600,
    include_equipment: int | None = None,
    include_items: int | None = None,
    include_magicitems: int | None = None,
    include_weapons: int | None = None,
    rarity: list[str] = Query(default=[]),
    keep: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    initial = not bool(generate)
    selected = {
        "include_equipment": True if initial else bool(include_equipment),
        "include_items": True if initial else bool(include_items),
        "include_magicitems": True if initial else bool(include_magicitems),
        "include_weapons": True if initial else bool(include_weapons),
    }
    count_min = max(1, min(100, count_min))
    count_max = max(count_min, min(100, count_max))
    max_value_gp = max(0, max_value_gp)
    max_total_value_gp = max(0, max_total_value_gp)

    lexicon = {
        row.original_term.casefold(): row.display_term
        for row in db.scalars(select(LexiconTerm)).all()
    }
    item_entities = list(
        db.scalars(
            select(Entity).where(Entity.entity_type == "item", Entity.is_active.is_(True))
        ).all()
    )
    item_index = _build_item_index(item_entities)

    kept = []
    if keep:
        kept = list(
            db.scalars(
                select(Entity).where(Entity.public_id.in_(keep), Entity.is_active.is_(True))
            ).all()
        )
    rows = [
        _loot_row(entity, kept=True, item_index=item_index, lexicon=lexicon)
        for entity in kept
    ]
    running_total_gp = sum(row["cost_gp"] or 0 for row in rows)

    target = random.randint(count_min, count_max) if generate else 0
    types: list[str] = []
    if selected["include_items"] or selected["include_equipment"]:
        types.append("item")
    if selected["include_magicitems"]:
        types.extend(["magicitem", "magic-item"])
    if selected["include_weapons"]:
        types.append("weapon")

    pool = list(
        db.scalars(
            select(Entity)
            .where(Entity.entity_type.in_(types or ["__none__"]), Entity.is_active.is_(True))
            .order_by(func.random())
            .limit(1000)
        ).all()
    )
    seen = {row["public_id"] for row in rows}
    for entity in pool:
        if len(rows) >= target:
            break
        if entity.public_id in seen:
            continue
        if entity.entity_type in {"magicitem", "magic-item"} and rarity:
            raw = str((entity.data_json or {}).get("rarity", "")).casefold()
            if not any(value.casefold() in raw for value in rarity):
                continue
        row = _loot_row(entity, item_index=item_index, lexicon=lexicon)
        row_value = row["cost_gp"] or 0
        if row["cost_gp"] is not None and row_value > max_value_gp:
            continue
        if running_total_gp + row_value > max_total_value_gp:
            continue
        rows.append(row)
        seen.add(entity.public_id)
        running_total_gp += row_value

    params = {
        "count_min": count_min,
        "count_max": count_max,
        "max_value_gp": max_value_gp,
        "max_total_value_gp": max_total_value_gp,
        "rarity": rarity,
        **selected,
    }
    return templates.TemplateResponse(
        request,
        "tools_loot_generator.html",
        _tool_context(
            "loot-generator",
            rows=rows,
            total_value_gp=running_total_gp,
            params=params,
            user_lists=_owned_lists(request,db),
        ),
    )


def _entity_source_document_key(entity: Entity) -> str:
    if entity.source_document:
        return str(entity.source_document).strip().casefold()
    data = entity.data_json or {}
    document = data.get("document") if isinstance(data.get("document"), dict) else {}
    return str(document.get("key") or document.get("slug") or "").strip().casefold()


def _entity_game_system_key(entity: Entity) -> str:
    if entity.game_system_key:
        return str(entity.game_system_key).strip().casefold()
    data = entity.data_json or {}
    document = data.get("document") if isinstance(data.get("document"), dict) else {}
    gamesystem = document.get("gamesystem") if isinstance(document.get("gamesystem"), dict) else {}
    return str(gamesystem.get("key") or data.get("gamesystem") or "").strip().casefold()


def _build_item_index(items: list[Entity]) -> dict[str, list[Entity]]:
    index: dict[str, list[Entity]] = {}
    for item in items:
        keys = {
            str(item.canonical_key or "").strip().casefold(),
            str(item.slug or "").strip().casefold(),
            str(item.name or "").strip().casefold(),
        }
        for key in keys - {""}:
            index.setdefault(key, []).append(item)
    return index


def _matching_item_candidates(weapon: Entity, item_index: dict[str, list[Entity]]) -> list[Entity]:
    keys = {
        str(weapon.canonical_key or "").strip().casefold(),
        str(weapon.slug or "").strip().casefold(),
        str(weapon.name or "").strip().casefold(),
    }
    candidates: list[Entity] = []
    seen: set[int] = set()
    for key in keys - {""}:
        for item in item_index.get(key, []):
            if item.id not in seen:
                candidates.append(item)
                seen.add(item.id)
    return candidates


def _select_item_fallback(weapon: Entity, candidates: list[Entity]) -> Entity | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    source = _entity_source_document_key(weapon)
    if source:
        for item in candidates:
            if _entity_source_document_key(item) == source:
                return item
    system = _entity_game_system_key(weapon)
    if system:
        for item in candidates:
            if _entity_game_system_key(item) == system:
                return item
    return candidates[0]


def _equipment_value(data: dict, *keys: str):
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    for wrapper in ("weapon", "item", "equipment"):
        nested = data.get(wrapper)
        if isinstance(nested, dict):
            for key in keys:
                value = nested.get(key)
                if value not in (None, "", [], {}):
                    return value
    return None


def _summary_value(card: dict, label: str):
    for row in card.get("summary_rows", []):
        if row.get("label") == label:
            return row
    for row in card.get("primary_stats", []):
        if row.get("label") == label:
            return row
    return None


def _loot_row(entity: Entity, kept: bool = False, *, item_index: dict[str, list[Entity]], lexicon: dict[str, str]):
    data = entity.data_json or {}
    cost_raw = _equipment_value(data, "cost")
    weight_raw = _equipment_value(data, "weight")
    cost_present = cost_raw not in (None, "", [], {})
    weight_present = weight_raw not in (None, "", [], {})
    cost_display = format_cost(cost_raw, present=cost_present)
    weight_display = format_weight(weight_raw, present=weight_present)

    if entity.entity_type == "weapon":
        candidates = _matching_item_candidates(entity, item_index)
        fallback = _select_item_fallback(entity, candidates)
        card = build_weapon_card(entity, fallback_item=fallback)
        rendered_cost = _summary_value(card, "Cost")
        rendered_weight = _summary_value(card, "Weight")
        if isinstance(rendered_cost, dict):
            value = rendered_cost.get("value")
            if isinstance(value, dict):
                value = value.get("value") or value.get("text")
            cost_display = {
                "value": value or rendered_cost.get("text") or "Unknown",
                "tooltip": rendered_cost.get("tooltip") or "",
            }
        elif rendered_cost:
            cost_display = {"value": str(rendered_cost), "tooltip": ""}
        if isinstance(rendered_weight, dict):
            value = rendered_weight.get("value")
            if isinstance(value, dict):
                value = value.get("value") or value.get("text")
            weight_display = str(value or rendered_weight.get("text") or "Unknown")
        elif rendered_weight:
            weight_display = str(rendered_weight)

        source_data = data
        if fallback is not None:
            fallback_data = fallback.data_json or {}
            if _numeric_value(cost_raw) in (None, 0):
                source_data = fallback_data
                cost_raw = _equipment_value(fallback_data, "cost")
            if _numeric_value(weight_raw) in (None, 0):
                weight_raw = _equipment_value(fallback_data, "weight")
        cost_gp = _numeric_value(cost_raw)
    else:
        cost_gp = _numeric_value(cost_raw)

    rarity = data.get("rarity", "")
    rarity = rarity.get("name", "") if isinstance(rarity, dict) else rarity
    raw_type = entity.entity_type
    type_label = lexicon.get(raw_type.casefold(), raw_type.replace("-", " ").replace("_", " ").title())
    return {
        "public_id": entity.public_id,
        "name": entity.name,
        "type": type_label,
        "cost": cost_display.get("value", ""),
        "cost_tooltip": cost_display.get("tooltip", ""),
        "cost_gp": cost_gp,
        "weight": weight_display,
        "rarity": rarity or "",
        "url": f"/compendium/{entity.entity_type}/{entity.canonical_key or entity.slug}",
        "kept": kept,
    }

