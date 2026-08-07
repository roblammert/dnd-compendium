
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
from app.models import Entity
from app.services import build_monster_card, format_cost, format_weight

router = APIRouter(prefix="/tools")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["app_version"] = "0.28.0"
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
def loot_generator(request: Request, generate:int=0, count_min:int=8, count_max:int=12, max_value_gp:float=500, include_pp:int=1, include_gp:int=1, include_sp:int=1, include_cp:int=1, include_equipment:int=1, include_items:int=1, include_magicitems:int=1, include_weapons:int=1, rarity:list[str]=Query(default=[]), keep:list[str]=Query(default=[]), db:Session=Depends(get_db)):
    kept=[]
    if keep:
        kept=list(db.scalars(select(Entity).where(Entity.public_id.in_(keep),Entity.is_active==True)).all())
    rows=[]
    for e in kept: rows.append(_loot_row(e, kept=True))
    target=random.randint(max(1,count_min),max(count_min,count_max)) if generate else 0
    types=[]
    if include_items or include_equipment: types.append("item")
    if include_magicitems: types.extend(["magicitem","magic-item"])
    if include_weapons: types.append("weapon")
    pool=list(db.scalars(select(Entity).where(Entity.entity_type.in_(types or ["__none__"]),Entity.is_active==True).order_by(func.random()).limit(500)).all())
    seen={r["public_id"] for r in rows}
    for e in pool:
        if len(rows)>=target: break
        if e.public_id in seen: continue
        if e.entity_type in {"magicitem","magic-item"} and rarity:
            raw=str((e.data_json or {}).get("rarity","")).casefold()
            if not any(r.casefold() in raw for r in rarity): continue
        row=_loot_row(e)
        if row["cost_gp"] is not None and row["cost_gp"]>max_value_gp: continue
        rows.append(row); seen.add(e.public_id)
    coin_types=[]
    if include_pp: coin_types.append(("PP",10))
    if include_gp: coin_types.append(("GP",1))
    if include_sp: coin_types.append(("SP",.1))
    if include_cp: coin_types.append(("CP",.01))
    while len(rows)<target and coin_types:
        coin,mult=random.choice(coin_types); amount=random.randint(1,max(1,int(max_value_gp/max(mult,.01))))
        rows.append({"public_id":"","name":f"{amount:,} {coin}","type":"Coin","cost":f"{amount:,} {coin}","cost_gp":amount*mult,"weight":"","rarity":"","url":"","kept":False})
    return templates.TemplateResponse(request,"tools_loot_generator.html",_tool_context("loot-generator",rows=rows,params=locals()))

def _loot_row(entity, kept=False):
    data=entity.data_json or {}; cost_raw=data.get("cost"); weight_raw=data.get("weight")
    cost=format_cost(cost_raw,present="cost" in data); cost_gp=None
    try:
        from app.services import _numeric_value
        cost_gp=_numeric_value(cost_raw)
    except Exception: pass
    rarity=data.get("rarity",""); rarity=rarity.get("name","") if isinstance(rarity,dict) else rarity
    return {"public_id":entity.public_id,"name":entity.name,"type":entity.entity_type.replace("-"," ").title(),"cost":cost["value"],"cost_gp":cost_gp,"weight":format_weight(weight_raw,present="weight" in data),"rarity":rarity or "","url":f"/compendium/{entity.entity_type}/{entity.canonical_key or entity.slug}","kept":kept}
