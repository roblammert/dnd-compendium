from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_user
from app.character_services import (
    ABILITIES, ABILITY_NAMES, SKILL_ABILITIES, STANDARD_ARRAY,
    class_save_proficiencies, class_skill_choices, derive_character,
    entities_for_character, entity_summary, find_character_entity, builder_summary,
    subclass_parent_key, background_allowed_abilities, background_skills,
    background_other_proficiencies, split_class_catalog,
)
from app.config import get_settings
from app.db import get_db
from app.models import Character, Entity, User
from app.character_rules_2024 import (
    RULESET_SOURCE_KEY, RULESET_SOURCE_LABEL, RULESET_GAME_SYSTEM_KEY,
    RULESET_GAME_SYSTEM_LABEL, RULESET_DISPLAY_NAME, STANDARD_LANGUAGES, LEVEL_XP,
)

router = APIRouter(prefix="/tools/character-builder")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["app_version"] = "0.31.5"
templates.env.globals["app_name"] = get_settings().app_name
_md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")
templates.env.filters["render_markdown"] = lambda value: Markup(_md.render(str(value or "")))
templates.env.globals["entity_summary"] = entity_summary
templates.env.globals["builder_summary"] = builder_summary
templates.env.globals["background_allowed_abilities"] = background_allowed_abilities
templates.env.globals["background_skills"] = background_skills
templates.env.globals["background_other_proficiencies"] = background_other_proficiencies

STEPS = [
    ("identity", "Identity"),
    ("species", "Species / Race"),
    ("class", "Class & Subclass"),
    ("abilities", "Ability Scores"),
    ("background", "Background & Proficiencies"),
    ("gear", "Equipment & Attacks"),
    ("spells", "Spells & Feats"),
    ("details", "Character Details"),
    ("review", "Review & Sheet"),
]
STEP_KEYS = {key for key, _ in STEPS}


def _uid() -> str:
    return f"chr_{uuid.uuid4().hex[:24]}"


def _character_or_404(db: Session, public_id: str, user: User) -> Character:
    row = db.scalar(select(Character).where(Character.public_id == public_id, Character.user_id == user.id))
    if not row:
        raise HTTPException(404, "Character not found")
    return row


def _enforce_2024_rules(character: Character, *, reset_incompatible: bool = True) -> bool:
    """Pin Character Builder state to the single supported 2024 ruleset.

    Returns True when the row was changed. Existing pre-v0.31.1 characters that
    were explicitly tied to another edition have their source-dependent choices
    cleared once so 2014 entities cannot leak into a 2024 character.
    """
    old_source = character.source_document
    changed = old_source != RULESET_SOURCE_KEY or character.game_system_key != RULESET_GAME_SYSTEM_KEY
    if reset_incompatible and old_source and old_source != RULESET_SOURCE_KEY:
        character.species_key = character.heritage_key = character.class_key = None
        character.subclass_key = character.background_key = None
        character.selected_spells = []
        character.prepared_spells = []
        character.selected_equipment = []
        character.feats = []
        character.skill_proficiencies = []
        character.save_proficiencies = []
    character.source_document = RULESET_SOURCE_KEY
    character.game_system_key = RULESET_GAME_SYSTEM_KEY
    return changed


def _source_options(db: Session) -> list[dict[str, str]]:
    rows = db.execute(
        select(Entity.source_document, Entity.source_display_name, Entity.game_system_key, Entity.game_system_name)
        .where(Entity.is_active.is_(True), Entity.source_document.is_not(None))
        .distinct().order_by(Entity.source_display_name)
    ).all()
    seen, result = set(), []
    for source, display, system, system_name in rows:
        if not source or source in seen:
            continue
        seen.add(source)
        result.append({"key": source, "name": display or source, "game_system_key": system or "", "game_system_name": system_name or system or ""})
    return result


def _spell_matches_class(spell: Entity, class_entity: Entity | None, level: int) -> bool:
    data = spell.data_json or {}
    spell_level = int(re.search(r"\d+", str(data.get("level", 0))).group()) if re.search(r"\d+", str(data.get("level", 0))) else 0
    if spell_level > max(1, min(9, (level + 1) // 2)) and spell_level != 0:
        return False
    if not class_entity:
        return True
    class_name = class_entity.name.casefold()
    blob = " ".join(str(data.get(key, "")) for key in ("classes", "class", "spell_lists", "spell_list")).casefold()
    return not blob or class_name in blob


def _all_active_entities(db: Session, entity_types: list[str]) -> list[Entity]:
    return list(db.scalars(select(Entity).where(
        Entity.entity_type.in_(entity_types), Entity.is_active.is_(True)
    ).order_by(Entity.name, Entity.source_display_name, Entity.id)).all())


def _dedupe_prefer_2024(rows: list[Entity]) -> list[Entity]:
    grouped: dict[str, list[Entity]] = {}
    for row in rows:
        key = row.canonical_key or row.slug or row.name.casefold()
        grouped.setdefault(key, []).append(row)
    result = []
    for variants in grouped.values():
        pick = next((r for r in variants if r.source_document == RULESET_SOURCE_KEY), None)
        pick = pick or next((r for r in variants if r.game_system_key == RULESET_GAME_SYSTEM_KEY), None)
        result.append(pick or variants[0])
    return sorted(result, key=lambda r: r.name.casefold())


def _step_context(db: Session, character: Character, step: str) -> dict[str, Any]:
    derived = derive_character(db, character)
    context: dict[str, Any] = {
        "character": character, "step": step, "steps": STEPS, "derived": derived,
        "ability_names": ABILITY_NAMES, "abilities": ABILITIES, "skill_abilities": SKILL_ABILITIES,
        "standard_array": STANDARD_ARRAY, "level_xp": LEVEL_XP,
        "ruleset_display_name": RULESET_DISPLAY_NAME,
        "ruleset_source_label": RULESET_SOURCE_LABEL,
        "ruleset_game_system_label": RULESET_GAME_SYSTEM_LABEL,
    }
    if step == "species":
        context["species_rows"] = entities_for_character(db, ["species", "race"], character)
        context["selected_species"] = find_character_entity(db, character, ["species", "race"], character.species_key)
    elif step == "class":
        # Some Open5e datasets expose subclass-shaped entries through class-like
        # endpoints.  Build one mixed catalog and normalize it into the twelve
        # primary 2024 classes plus correctly nested subclasses.
        mixed_rows = entities_for_character(db, ["class", "classe", "subclass", "subclasse"], character)
        class_rows, subclass_rows, subclass_parents = split_class_catalog(mixed_rows)
        context["class_rows"] = class_rows
        context["subclass_rows"] = subclass_rows
        context["selected_class"] = find_character_entity(db, character, ["class", "classe"], character.class_key)
        context["subclass_parents"] = subclass_parents
    elif step == "background":
        # 2024 characters may use backgrounds from older books. Prefer the 2024
        # variant when duplicates exist, but expose distinct legacy backgrounds too.
        context["background_rows"] = sorted(_all_active_entities(db, ["background"]), key=lambda r: (r.name.casefold(), 0 if r.source_document == RULESET_SOURCE_KEY else 1, (r.source_display_name or "").casefold()))
        # Alignment is descriptive rather than an edition-specific mechanic, so use
        # the best available cached variant instead of requiring srd-2024 coverage.
        context["alignment_rows"] = _dedupe_prefer_2024(_all_active_entities(db, ["alignment"]))
        context["language_rows"] = _dedupe_prefer_2024(_all_active_entities(db, ["language"]))
        context["language_options"] = sorted(set(STANDARD_LANGUAGES + [r.name for r in context["language_rows"]]))
        context["selected_background"] = next((r for r in context["background_rows"] if r.public_id == character.background_key or (r.canonical_key or r.slug) == character.background_key), None)
        context["selected_background_allowed_abilities"] = background_allowed_abilities(context["selected_background"])
        context["background_locked_skills"] = background_skills(context["selected_background"])
        context["background_locked_proficiencies"] = background_other_proficiencies(context["selected_background"])
        class_entity = derived["class_entity"]
        class_skills = class_skill_choices(class_entity)
        context["class_skill_choices"] = list(dict.fromkeys(class_skills + context["background_locked_skills"]))
        context["class_saves"] = class_save_proficiencies(class_entity)
        suggested = list(dict.fromkeys(list(character.other_proficiencies or []) + context["background_locked_proficiencies"]))
        context["proficiency_options"] = sorted(set(suggested + ["Light Armor", "Medium Armor", "Heavy Armor", "Shields", "Simple Weapons", "Martial Weapons", "Thieves' Tools", "Calligrapher's Supplies", "Gaming Set"]))
    elif step == "gear":
        context["equipment_rows"] = entities_for_character(db, ["equipment", "item", "weapon", "armor"], character)
    elif step == "spells":
        all_spells = entities_for_character(db, ["spell"], character)
        context["spell_rows"] = [s for s in all_spells if _spell_matches_class(s, derived["class_entity"], character.level)]
        context["feat_rows"] = entities_for_character(db, ["feat"], character)
    return context


def _render_stage(request: Request, db: Session, character: Character, step: str):
    return templates.TemplateResponse(request, "character_stage_response.html", _step_context(db, character, step))


@router.get("", response_class=HTMLResponse)
def character_builder_home(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    characters = list(db.scalars(select(Character).where(Character.user_id == user.id).order_by(Character.updated_at.desc())).all())
    return templates.TemplateResponse(request, "tools_character_builder_home.html", {
        "tools_section": "character-builder", "characters": characters,
    })


@router.post("/new")
async def new_character(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    form = await request.form()
    row = Character(
        public_id=_uid(), user_id=user.id, name=str(form.get("name") or "New Character").strip() or "New Character",
        source_document=RULESET_SOURCE_KEY, game_system_key=RULESET_GAME_SYSTEM_KEY,
        ability_scores={ability: 10 for ability in ABILITIES}, currency={"cp":0,"sp":0,"ep":0,"gp":0,"pp":0},
        details_json={}, choices_json={}, selected_spells=[], prepared_spells=[], selected_equipment=[], feats=[],
        skill_proficiencies=[], save_proficiencies=[], languages=[], other_proficiencies=[],
    )
    db.add(row); db.commit()
    return RedirectResponse(f"/tools/character-builder/{row.public_id}", 303)


@router.post("/{public_id}/delete")
def delete_character(public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    row = _character_or_404(db, public_id, user)
    db.delete(row); db.commit()
    return RedirectResponse("/tools/character-builder", 303)


@router.get("/{public_id}", response_class=HTMLResponse)
def edit_character(request: Request, public_id: str, step: str | None = None, user: User = Depends(require_user), db: Session = Depends(get_db)):
    row = _character_or_404(db, public_id, user)
    if _enforce_2024_rules(row):
        db.commit(); db.refresh(row)
    active = step if step in STEP_KEYS else (row.current_step if row.current_step in STEP_KEYS else "identity")
    context = _step_context(db, row, active)
    context.update({"tools_section": "character-builder"})
    return templates.TemplateResponse(request, "tools_character_builder.html", context)


@router.get("/{public_id}/step/{step}", response_class=HTMLResponse)
def get_step(request: Request, public_id: str, step: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if step not in STEP_KEYS:
        raise HTTPException(404)
    row = _character_or_404(db, public_id, user)
    _enforce_2024_rules(row)
    row.current_step = step
    db.commit()

    # Step endpoints are HTMX fragments. If HTMX is unavailable, disabled, or a
    # pushed fragment URL is loaded directly, send the browser back through the
    # full Character Builder shell so the site chrome, CSS, and scripts are
    # always present. This also makes the workflow progressively enhanced.
    if request.headers.get("HX-Request") != "true":
        return RedirectResponse(f"/tools/character-builder/{row.public_id}?step={step}", 303)

    return _render_stage(request, db, row, step)


@router.post("/{public_id}/step/{step}", response_class=HTMLResponse)
async def save_step(request: Request, public_id: str, step: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if step not in STEP_KEYS:
        raise HTTPException(404)
    row = _character_or_404(db, public_id, user)
    _enforce_2024_rules(row)
    form = await request.form()
    next_step = str(form.get("next_step") or step)
    if next_step not in STEP_KEYS:
        next_step = step

    if step == "identity":
        row.name = str(form.get("name") or row.name).strip() or "New Character"
        posted_level = max(1, min(20, int(form.get("level") or row.level)))
        posted_xp = max(0, int(form.get("experience_points") or 0))
        # Identity keeps level and XP coherent. The browser performs the same
        # interaction live; this server normalization prevents crafted/stale
        # submissions from storing an impossible lower XP for the chosen level.
        level_from_xp = max(level for level, minimum in LEVEL_XP.items() if posted_xp >= minimum)
        row.level = max(posted_level, level_from_xp)
        row.experience_points = max(posted_xp, LEVEL_XP[row.level])
        # Source/game-system fields are deliberately ignored. Character Builder
        # is pinned to the 2024 rules and cannot be switched by the client.
        _enforce_2024_rules(row, reset_incompatible=False)
    elif step == "species":
        row.species_key = str(form.get("species_key") or "") or None
        row.heritage_key = str(form.get("heritage_key") or "") or None
    elif step == "class":
        row.class_key = str(form.get("class_key") or "") or None
        row.subclass_key = str(form.get("subclass_key") or "") or None
        class_entity = find_character_entity(db, row, ["class", "classe"], row.class_key)
        row.save_proficiencies = class_save_proficiencies(class_entity)
    elif step == "abilities":
        method = str(form.get("ability_method") or "standard_array")
        row.ability_method = method if method in {"standard_array", "point_buy", "rolled", "manual"} else "manual"
        scores = {}
        for ability in ABILITIES:
            scores[ability] = max(1, min(20, int(form.get(ability) or 10)))
        row.ability_scores = scores
    elif step == "background":
        row.background_key = str(form.get("background_key") or "") or None
        row.alignment_key = str(form.get("alignment_key") or "") or None
        row.skill_proficiencies = list(dict.fromkeys(str(v) for v in form.getlist("skills") if v))
        row.languages = list(dict.fromkeys(str(v).strip() for v in form.getlist("languages") if str(v).strip()))
        row.other_proficiencies = list(dict.fromkeys(str(v).strip() for v in form.getlist("other_proficiencies") if str(v).strip()))
        choices = dict(row.choices_json or {})
        bonuses = {}
        for ability in ABILITIES:
            amount = int(form.get(f"background_bonus_{ability}") or 0)
            if amount:
                bonuses[ability] = amount
        # Enforce the 2024 three-point background adjustment shape. Legacy
        # backgrounds may place the points on any abilities; current backgrounds
        # are constrained in the browser and validated by the total here.
        if sum(bonuses.values()) == 3 and sorted(bonuses.values()) in ([1, 1, 1], [1, 2]):
            choices["background_ability_bonuses"] = bonuses
        else:
            choices.pop("background_ability_bonuses", None)
        row.choices_json = choices
    elif step == "gear":
        row.selected_equipment = list(dict.fromkeys(str(v) for v in form.getlist("equipment") if v))
        row.currency = {coin: max(0, int(form.get(coin) or 0)) for coin in ("cp","sp","ep","gp","pp")}
    elif step == "spells":
        row.selected_spells = list(dict.fromkeys(str(v) for v in form.getlist("spells") if v))
        selected = set(row.selected_spells)
        row.prepared_spells = [str(v) for v in form.getlist("prepared") if str(v) in selected]
        row.feats = list(dict.fromkeys(str(v) for v in form.getlist("feats") if v))
    elif step == "details":
        fields = ["player_name","inspiration","personality_traits","ideals","bonds","flaws","age","height","weight","eyes","skin","hair","appearance","backstory","allies","symbol","treasure","additional_features","notes"]
        details = dict(row.details_json or {})
        for field in fields:
            details[field] = str(form.get(field) or "").strip()
        details["current_hp"] = max(0, int(form.get("current_hp") or derive_character(db,row)["hp_max"]))
        details["temp_hp"] = max(0, int(form.get("temp_hp") or 0))
        row.details_json = details
    elif step == "review":
        row.is_complete = bool(form.get("is_complete"))

    row.current_step = next_step
    db.commit(); db.refresh(row)
    if request.headers.get("HX-Request") == "true":
        response = _render_stage(request, db, row, next_step)
        response.headers["HX-Push-Url"] = f"/tools/character-builder/{row.public_id}?step={next_step}"
        return response
    return RedirectResponse(f"/tools/character-builder/{row.public_id}?step={next_step}", 303)


@router.get("/{public_id}/print", response_class=HTMLResponse)
def print_character(request: Request, public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    row = _character_or_404(db, public_id, user)
    return templates.TemplateResponse(request, "character_print.html", {"derived": derive_character(db, row), "character": row})


@router.get("/{public_id}/pdf")
def character_pdf(request: Request, public_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    row = _character_or_404(db, public_id, user)
    derived = derive_character(db, row)
    html = templates.get_template("character_print.html").render(request=request, derived=derived, character=row, pdf_mode=True)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html, base_url=str(Path(__file__).parent)).write_pdf()
    except Exception as exc:
        raise HTTPException(503, f"PDF export is unavailable: {exc}") from exc
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", row.name).strip("_") or "character"
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe_name}_character_sheet.pdf"'})
