
from __future__ import annotations
import json, random, re
from fractions import Fraction
from pathlib import Path
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db
from app.models import Entity, LexiconTerm
from app.services import build_monster_card, build_weapon_card, format_cost, format_weight, _numeric_value

router = APIRouter(prefix="/tools")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["app_version"] = "0.28.1"
templates.env.globals["app_name"] = get_settings().app_name

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

@router.get("/loadout-generator", response_class=HTMLResponse)
def loadout_generator(request: Request):
    return templates.TemplateResponse(request,"tools_deferred.html",_tool_context("loadout-generator",title="Loadout Generator",description="Player loadout generation is reserved for a later release."))

@router.get("/encounter-builder", response_class=HTMLResponse)
def encounter_builder(request: Request, mode:str="random_cr", cr_min:float=0, cr_max:float=5, monster_count:int=4, party_level:int=5, party_size:int=4, difficulty:str="medium", scale_mode:str="none", baseline_party_size:int=4, manual_q:str="", db:Session=Depends(get_db)):
    monsters=list(db.scalars(select(Entity).where(Entity.entity_type=="monster",Entity.is_active==True).order_by(Entity.name)).all())
    rows=[_monster_row(e) for e in monsters]
    selected=[]; budget=None
    if mode=="random_cr":
        pool=[r for r in rows if cr_min <= r["cr"] <= cr_max]
        selected=random.sample(pool,min(max(monster_count,1),len(pool))) if pool else []
    elif mode=="xp_budget":
        level=max(1,min(20,party_level)); diff=difficulty if difficulty in DIFFICULTY_INDEX else "medium"
        budget=XP_THRESHOLDS[level][DIFFICULTY_INDEX[diff]]*max(1,party_size)
        pool=[r for r in rows if r["xp"]>0 and r["xp"]<=budget]
        random.shuffle(pool); total=0
        for row in sorted(pool,key=lambda r:r["xp"],reverse=True):
            if total+row["xp"]<=budget and len(selected)<20:
                selected.append(row); total+=row["xp"]
    elif mode=="manual" and manual_q.strip():
        term=manual_q.casefold(); selected=[r for r in rows if term in r["entity"].name.casefold()][:50]
    ratio=max(1,party_size)/max(1,baseline_party_size)
    for row in selected:
        row["scaled_hp"] = round(_number(row["hp"])*ratio) if scale_mode=="variable" and _number(row["hp"]) else row["hp"]
        row["scaled_ac"] = round(_number(row["ac"])+(ratio-1)/0.5) if scale_mode=="variable" and _number(row["ac"]) else row["ac"]
    total_cr=sum(r["cr"] for r in selected); total_levels=max(1,party_size)*max(1,party_level)
    lazy_limit=(0.25 if party_level<=4 else 0.5)*total_levels
    return templates.TemplateResponse(request,"tools_encounter_builder.html",_tool_context("encounter-builder",selected=selected,budget=budget,total_xp=sum(r["xp"] for r in selected),total_cr=total_cr,lazy_limit=lazy_limit,ratio=ratio,params={"mode":mode,"cr_min":cr_min,"cr_max":cr_max,"monster_count":monster_count,"party_level":party_level,"party_size":party_size,"difficulty":difficulty,"scale_mode":scale_mode,"baseline_party_size":baseline_party_size,"manual_q":manual_q}))

@router.get("/loot-generator", response_class=HTMLResponse)
def loot_generator(
    request: Request,
    generate: int = 0,
    count_min: int = 8,
    count_max: int = 12,
    max_value_gp: float = 500,
    include_pp: int | None = None,
    include_gp: int | None = None,
    include_sp: int | None = None,
    include_cp: int | None = None,
    include_equipment: int | None = None,
    include_items: int | None = None,
    include_magicitems: int | None = None,
    include_weapons: int | None = None,
    rarity: list[str] = Query(default=[]),
    keep: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    # On the first visit, start with every inclusion option selected. On a
    # generated request, an omitted checkbox means false rather than reverting
    # to the route's defaults.
    initial = not bool(generate)
    selected = {
        "include_pp": True if initial else bool(include_pp),
        "include_gp": True if initial else bool(include_gp),
        "include_sp": True if initial else bool(include_sp),
        "include_cp": True if initial else bool(include_cp),
        "include_equipment": True if initial else bool(include_equipment),
        "include_items": True if initial else bool(include_items),
        "include_magicitems": True if initial else bool(include_magicitems),
        "include_weapons": True if initial else bool(include_weapons),
    }
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

    target = random.randint(max(1, count_min), max(count_min, count_max)) if generate else 0
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
            .limit(500)
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
        if row["cost_gp"] is not None and row["cost_gp"] > max_value_gp:
            continue
        rows.append(row)
        seen.add(entity.public_id)

    coin_types = []
    if selected["include_pp"]:
        coin_types.append(("PP", 10))
    if selected["include_gp"]:
        coin_types.append(("GP", 1))
    if selected["include_sp"]:
        coin_types.append(("SP", .1))
    if selected["include_cp"]:
        coin_types.append(("CP", .01))
    while len(rows) < target and coin_types:
        coin, multiplier = random.choice(coin_types)
        amount = random.randint(1, max(1, int(max_value_gp / max(multiplier, .01))))
        rows.append({
            "public_id": "",
            "name": f"{amount:,} {coin}",
            "type": "Coin",
            "cost": f"{amount:,} {coin}",
            "cost_tooltip": "",
            "cost_gp": amount * multiplier,
            "weight": "",
            "rarity": "",
            "url": "",
            "kept": False,
        })

    params = {
        "count_min": count_min,
        "count_max": count_max,
        "max_value_gp": max_value_gp,
        "rarity": rarity,
        **selected,
    }
    return templates.TemplateResponse(
        request,
        "tools_loot_generator.html",
        _tool_context("loot-generator", rows=rows, params=params),
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

