from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Character, Entity
from app.services import build_weapon_card
from app.character_rules_2024 import (
    RULESET_SOURCE_KEY, RULESET_GAME_SYSTEM_KEY, CLASS_RULES, BACKGROUND_RULES,
    SPECIES_SUMMARIES, CLASS_SUMMARIES, BACKGROUND_SUMMARIES, DEFAULT_SUBCLASS_PARENTS,
    class_rule, background_rule, canonical_rule_key,
)

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
ABILITY_NAMES = {
    "str": "Strength", "dex": "Dexterity", "con": "Constitution",
    "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma",
}
SKILL_ABILITIES = {
    "Acrobatics": "dex", "Animal Handling": "wis", "Arcana": "int", "Athletics": "str",
    "Deception": "cha", "History": "int", "Insight": "wis", "Intimidation": "cha",
    "Investigation": "int", "Medicine": "wis", "Nature": "int", "Perception": "wis",
    "Performance": "cha", "Persuasion": "cha", "Religion": "int", "Sleight of Hand": "dex",
    "Stealth": "dex", "Survival": "wis",
}
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
POINT_BUY_COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}


def ability_modifier(score: int) -> int:
    return math.floor((int(score) - 10) / 2)


def proficiency_bonus(level: int) -> int:
    return math.floor((max(1, int(level)) - 1) / 4) + 2


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "label", "title", "key", "value", "desc", "description", "text"):
            if value.get(key) not in (None, ""):
                return _text(value[key])
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return ", ".join(filter(None, (_text(item) for item in value)))
    return str(value)


def _number(value: Any, default: int = 0) -> int:
    if isinstance(value, dict):
        for key in ("value", "score", "amount", "base", "number"):
            if key in value:
                return _number(value[key], default)
    try:
        match = re.search(r"-?\d+", str(value))
        return int(match.group()) if match else default
    except Exception:
        return default


def _nested(data: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = data
        ok = True
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                ok = False
                break
            current = current[key]
        if ok and current not in (None, "", [], {}):
            return current
    return None


def _source_matches(entity: Entity, source_document: str | None, game_system_key: str | None) -> bool:
    if source_document and entity.source_document == source_document:
        return True
    if game_system_key and entity.game_system_key == game_system_key:
        return True
    return not source_document and not game_system_key


def entities_for_character(db: Session, entity_types: list[str], character: Character) -> list[Entity]:
    """Return only 2024-compatible reference entities for Character Builder.

    The general Compendium can contain many editions/sources. Character Builder
    deliberately ignores the user's preferred source and never falls through to
    2014 records. Exact srd-2024 variants win; other records tagged 5e-2024 are
    allowed only when an endpoint has no exact SRD variant.
    """
    rows = list(db.scalars(
        select(Entity).where(Entity.entity_type.in_(entity_types), Entity.is_active.is_(True)).order_by(Entity.name)
    ).all())
    same_source = [r for r in rows if r.source_document == RULESET_SOURCE_KEY]
    if same_source:
        return same_source
    return [r for r in rows if r.game_system_key == RULESET_GAME_SYSTEM_KEY]


def find_character_entity(db: Session, character: Character, entity_types: list[str], key: str | None) -> Entity | None:
    if not key:
        return None
    rows = list(db.scalars(select(Entity).where(
        Entity.entity_type.in_(entity_types), Entity.is_active.is_(True), Entity.canonical_key == key
    )).all())
    if not rows:
        rows = list(db.scalars(select(Entity).where(
            Entity.entity_type.in_(entity_types), Entity.is_active.is_(True), Entity.slug == key
        )).all())
    if not rows:
        return None
    for row in rows:
        if row.source_document == RULESET_SOURCE_KEY:
            return row
    for row in rows:
        if row.game_system_key == RULESET_GAME_SYSTEM_KEY:
            return row
    return None




def find_any_character_entity(db: Session, entity_types: list[str], key: str | None) -> Entity | None:
    if not key:
        return None
    rows = list(db.scalars(select(Entity).where(
        Entity.entity_type.in_(entity_types), Entity.is_active.is_(True),
        (Entity.public_id == key) | (Entity.canonical_key == key) | (Entity.slug == key)
    ).order_by(Entity.id)).all())
    if not rows:
        return None
    return next((r for r in rows if r.source_document == RULESET_SOURCE_KEY), None) or next((r for r in rows if r.game_system_key == RULESET_GAME_SYSTEM_KEY), None) or rows[0]

def entity_summary(entity: Entity | None) -> str:
    if not entity:
        return ""
    data = entity.data_json or {}
    value = data.get("desc") or data.get("description") or entity.summary or ""
    if isinstance(value, list):
        value = "\n\n".join(_text(v) for v in value)
    return _text(value)


def species_bonuses(entity: Entity | None) -> dict[str, int]:
    if not entity:
        return {}
    # Under the 2024 rules, species do not grant ability-score increases;
    # those choices come from the character's background/origin.
    if entity.source_document == RULESET_SOURCE_KEY or entity.game_system_key == RULESET_GAME_SYSTEM_KEY:
        return {}
    data = entity.data_json or {}
    raw = _nested(data, "ability_score_increases", "ability_scores", "ability_score_bonus", "ability_bonuses")
    result: dict[str, int] = {}
    entries = raw if isinstance(raw, list) else ([raw] if raw else [])
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = _text(entry.get("ability") or entry.get("ability_score") or entry.get("name") or entry.get("key")).casefold()
        amount = _number(entry.get("increase") or entry.get("bonus") or entry.get("value"), 0)
        for abbr, full in ABILITY_NAMES.items():
            if abbr == name or full.casefold() in name:
                result[abbr] = result.get(abbr, 0) + amount
    return result


def background_bonuses(entity: Entity | None) -> dict[str, int]:
    if not entity:
        return {}
    data = entity.data_json or {}
    raw = _nested(data, "ability_score_increases", "ability_scores", "ability_score_bonus", "ability_bonuses")
    result: dict[str, int] = {}
    entries = raw if isinstance(raw, list) else ([raw] if raw else [])
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = _text(entry.get("ability") or entry.get("ability_score") or entry.get("name") or entry.get("key")).casefold()
        amount = _number(entry.get("increase") or entry.get("bonus") or entry.get("value"), 0)
        for abbr, full in ABILITY_NAMES.items():
            if abbr == name or full.casefold() in name:
                result[abbr] = result.get(abbr, 0) + amount
    return result


def builder_summary(entity: Entity | None, kind: str = "") -> str:
    summary = entity_summary(entity).strip()
    if summary:
        return summary
    if not entity:
        return "No description is available for this option yet."
    key = canonical_rule_key(entity.canonical_key or entity.slug or entity.name)
    table = SPECIES_SUMMARIES if kind == "species" else CLASS_SUMMARIES if kind == "class" else BACKGROUND_SUMMARIES if kind == "background" else {}
    return table.get(key) or f"{entity.name} is a {kind or entity.entity_type} option available to this character. Open More Info to review the cached compendium record before selecting it."


def subclass_parent_key(entity: Entity | None) -> str | None:
    if not entity:
        return None
    data = entity.data_json or {}
    raw = _nested(data, "class", "parent_class", "parent", "class_key", "base_class")
    text = _text(raw)
    if text:
        key = canonical_rule_key(text)
        for class_key in CLASS_RULES:
            if class_key in key:
                return class_key
    key = canonical_rule_key(entity.canonical_key or entity.slug or entity.name)
    for sub_key, parent in DEFAULT_SUBCLASS_PARENTS.items():
        # Exact matching avoids false positives such as the Cleric "War"
        # domain being detected inside the base class name "Warlock".  A
        # suffix match still supports source-prefixed Open5e keys.
        if key == sub_key or key.endswith(f"-{sub_key}"):
            return parent
    return None



def primary_class_key(entity: Entity | None) -> str | None:
    """Return one of the twelve 2024 base class keys, or None.

    Open5e occasionally exposes subclass-like records through class-shaped
    endpoints.  A primary class is therefore recognized by the canonical key
    or display name matching a core class exactly; subclass names are not
    allowed to leak into the primary-class picker.
    """
    if not entity:
        return None
    candidates = (entity.canonical_key, entity.slug, entity.name)
    for candidate in candidates:
        key = canonical_rule_key(candidate)
        if key in CLASS_RULES:
            return key
        # Source-prefixed keys such as srd-2024_bard normalize with a suffix.
        for class_key in CLASS_RULES:
            if key.endswith(f"-{class_key}"):
                return class_key
    return None


def split_class_catalog(rows: list[Entity]) -> tuple[list[Entity], list[Entity], dict[str, str]]:
    """Normalize mixed Open5e class/subclass rows for the builder UI."""
    primary: list[Entity] = []
    subclasses: list[Entity] = []
    parents: dict[str, str] = {}
    seen_primary: set[str] = set()
    seen_subclasses: set[tuple[str, str]] = set()

    for entity in rows:
        parent = subclass_parent_key(entity)
        base = primary_class_key(entity)
        if parent and not base:
            sub_key = canonical_rule_key(entity.canonical_key or entity.slug or entity.name)
            marker = (parent, sub_key)
            if marker not in seen_subclasses:
                subclasses.append(entity)
                parents[entity.public_id] = parent
                seen_subclasses.add(marker)
            continue
        if base and base not in seen_primary:
            primary.append(entity)
            seen_primary.add(base)

    primary.sort(key=lambda entity: entity.name.casefold())
    subclasses.sort(key=lambda entity: (parents.get(entity.public_id, ""), entity.name.casefold()))
    return primary, subclasses, parents

def background_allowed_abilities(entity: Entity | None) -> list[str]:
    if not entity:
        return list(ABILITIES)
    rule = background_rule(entity.canonical_key or entity.slug or entity.name)
    if rule.get("abilities"):
        return list(rule["abilities"])
    data = entity.data_json or {}
    raw = _nested(data, "ability_scores", "ability_score_options", "ability_score_increases")
    text = _text(raw).casefold()
    detected = [abbr for abbr, full in ABILITY_NAMES.items() if abbr in text or full.casefold() in text]
    # 2024 conversion rule for legacy backgrounds: any abilities may receive the three points.
    return detected or list(ABILITIES)


def class_hit_die(entity: Entity | None) -> int:
    if not entity:
        return 8
    data = entity.data_json or {}
    raw = _nested(data, "hit_die", "hit_dice", "hit_points.hit_die", "core_traits.hit_point_die")
    fallback = int(class_rule(entity.canonical_key or entity.slug or entity.name).get("hit_die", 8))
    return max(4, _number(raw, fallback))


def _ability_key(value: Any) -> str | None:
    text = _text(value).casefold()
    for abbr, full in ABILITY_NAMES.items():
        if text == abbr or full.casefold() in text:
            return abbr
    return None


def class_save_proficiencies(entity: Entity | None) -> list[str]:
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "saving_throws", "saving_throw_proficiencies", "proficiencies.saving_throws", "core_traits.saving_throw_proficiencies")
    items = raw if isinstance(raw, list) else ([raw] if raw else [])
    result = []
    for item in items:
        key = _ability_key(item)
        if key and key not in result:
            result.append(key)
    if result:
        return result
    return list(class_rule(entity.canonical_key or entity.slug or entity.name).get("saves", []))


def class_spellcasting_ability(entity: Entity | None) -> str | None:
    if not entity:
        return None
    data = entity.data_json or {}
    detected = _ability_key(_nested(data, "spellcasting_ability", "spellcasting.ability", "primary_ability", "core_traits.primary_ability"))
    return detected or class_rule(entity.canonical_key or entity.slug or entity.name).get("spellcasting_ability")


def species_speed(entity: Entity | None) -> int:
    if not entity:
        return 30
    data = entity.data_json or {}
    raw = _nested(data, "speed.walk", "speed", "walk_speed", "movement.walk")
    return _number(raw, 30)


def class_skill_choices(entity: Entity | None) -> list[str]:
    if not entity:
        return list(SKILL_ABILITIES)
    data = entity.data_json or {}
    raw = _nested(data, "skill_proficiencies", "skills", "proficiencies.skills", "core_traits.skill_proficiencies")
    text = _text(raw)
    result = [skill for skill in SKILL_ABILITIES if skill.casefold() in text.casefold()]
    if result:
        return result
    fallback = class_rule(entity.canonical_key or entity.slug or entity.name).get("skills")
    return list(SKILL_ABILITIES) if fallback == "any" else list(fallback or SKILL_ABILITIES)




def class_skill_choice_count(entity: Entity | None) -> int | None:
    if not entity:
        return None
    data = entity.data_json or {}
    raw = _nested(data, "skill_proficiencies", "skills", "proficiencies.skills", "core_traits.skill_proficiencies")
    text = _text(raw).casefold()
    word_numbers = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6}
    match = re.search(r"choose\s+(one|two|three|four|five|six|\d+)", text)
    if not match:
        fallback = class_rule(entity.canonical_key or entity.slug or entity.name).get("skill_count")
        return int(fallback) if fallback is not None else None
    token = match.group(1)
    return word_numbers.get(token, int(token) if token.isdigit() else None)


def class_features_for_level(entity: Entity | None, level: int) -> list[dict[str, Any]]:
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "features", "class_features", "levels", "progression")
    items = raw if isinstance(raw, list) else []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        feature_level = _number(item.get("level") or item.get("class_level"), 1)
        if feature_level > level:
            continue
        name = _text(item.get("name") or item.get("feature") or item.get("title")) or f"Level {feature_level} Feature"
        desc = _text(item.get("desc") or item.get("description") or item.get("text") or item.get("detail"))
        result.append({"name": name, "level": feature_level, "description": desc})
    return result

def background_skills(entity: Entity | None) -> list[str]:
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "skill_proficiencies", "skills", "proficiencies.skills")
    text = _text(raw)
    detected = [skill for skill in SKILL_ABILITIES if skill.casefold() in text.casefold()]
    if detected:
        return detected
    return list(background_rule(entity.canonical_key or entity.slug or entity.name).get("skills", []))




def background_other_proficiencies(entity: Entity | None) -> list[str]:
    """Return tool/other proficiencies granted directly by a background."""
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "tool_proficiencies", "tools", "proficiencies.tools", "tool_proficiency")
    text = _text(raw).strip()
    result: list[str] = []
    if text:
        # Structured lists are flattened by _text; retain useful named phrases
        # when possible without treating ability/save abbreviations as tools.
        if isinstance(raw, list):
            for item in raw:
                value = _text(item).strip()
                if value and value not in result:
                    result.append(value)
        elif text:
            result.append(text)
    fallback = background_rule(entity.canonical_key or entity.slug or entity.name).get("tool")
    if fallback and fallback not in result:
        result.append(str(fallback))
    return result

def point_buy_total(scores: dict[str, int]) -> int | None:
    total = 0
    for ability in ABILITIES:
        score = int(scores.get(ability, 8))
        if score not in POINT_BUY_COST:
            return None
        total += POINT_BUY_COST[score]
    return total


def resolve_selected(db: Session, public_ids: list[str]) -> list[Entity]:
    if not public_ids:
        return []
    rows = list(db.scalars(select(Entity).where(Entity.public_id.in_(public_ids), Entity.is_active.is_(True))).all())
    order = {value: index for index, value in enumerate(public_ids)}
    rows.sort(key=lambda row: order.get(row.public_id, 9999))
    return rows


def _armor_values(entity: Entity, dex_mod: int) -> tuple[int | None, bool, int]:
    data = entity.data_json or {}
    armor = data.get("armor") if isinstance(data.get("armor"), dict) else data
    category = _text(armor.get("category") or armor.get("armor_category") or data.get("category")).casefold()
    base = _number(armor.get("base_ac") or armor.get("armor_class") or armor.get("ac"), 0)
    if not base:
        return None, False, 0
    if "heavy" in category:
        ac = base
    elif "medium" in category:
        ac = base + min(2, dex_mod)
    else:
        ac = base + dex_mod
    stealth = bool(armor.get("stealth_disadvantage") or armor.get("stealth_disadvantage_override"))
    strength = _number(armor.get("strength_requirement") or armor.get("strength_score"), 0)
    return ac, stealth, strength


def _weapon_attack(entity: Entity, scores: dict[str, int], prof_bonus: int) -> dict[str, Any]:
    data = entity.data_json or {}
    weapon = data.get("weapon") if isinstance(data.get("weapon"), dict) else data
    props = _text(weapon.get("properties") or data.get("properties")).casefold()
    ranged = bool(_number(weapon.get("range") or data.get("range"), 0)) and "melee" not in _text(weapon.get("category")).casefold()
    finesse = "finesse" in props
    ability = "dex" if ranged or (finesse and scores.get("dex", 10) > scores.get("str", 10)) else "str"
    bonus = ability_modifier(scores.get(ability, 10)) + prof_bonus
    dice = _text(weapon.get("damage_dice") or data.get("damage_dice")) or "—"
    dtype = _text(weapon.get("damage_type") or data.get("damage_type"))
    return {"name": entity.name, "attack_bonus": bonus, "damage": f"{dice} {dtype}".strip(), "entity": entity}


def derive_character(db: Session, character: Character) -> dict[str, Any]:
    species = find_character_entity(db, character, ["species", "race"], character.species_key)
    class_entity = find_character_entity(db, character, ["class", "classe"], character.class_key)
    background = find_any_character_entity(db, ["background"], character.background_key)
    alignment = find_any_character_entity(db, ["alignment"], character.alignment_key)
    subclass = find_character_entity(db, character, ["subclass", "subclasse"], character.subclass_key)

    base_scores = {ability: int((character.ability_scores or {}).get(ability, 10)) for ability in ABILITIES}
    bonuses: dict[str, int] = defaultdict(int)
    # 2014 sources generally place ASIs on race/species; 2024 sources place them on background.
    for key, value in species_bonuses(species).items():
        bonuses[key] += value
    stored_background_bonuses = (character.choices_json or {}).get("background_ability_bonuses", {})
    if isinstance(stored_background_bonuses, dict) and stored_background_bonuses:
        for key, value in stored_background_bonuses.items():
            if key in ABILITIES:
                bonuses[key] += int(value or 0)
    else:
        for key, value in background_bonuses(background).items():
            bonuses[key] += value
    final_scores = {ability: max(1, min(30, base_scores[ability] + bonuses.get(ability, 0))) for ability in ABILITIES}
    modifiers = {ability: ability_modifier(score) for ability, score in final_scores.items()}
    prof = proficiency_bonus(character.level)

    saves = list(dict.fromkeys((character.save_proficiencies or []) + class_save_proficiencies(class_entity)))
    background_skill_list = background_skills(background)
    background_other_list = background_other_proficiencies(background)
    skills_prof = list(dict.fromkeys((character.skill_proficiencies or []) + background_skill_list))
    other_proficiencies = list(dict.fromkeys((character.other_proficiencies or []) + background_other_list))
    skills = []
    for name, ability in SKILL_ABILITIES.items():
        proficient = name in skills_prof
        skills.append({"name": name, "ability": ability, "modifier": modifiers[ability] + (prof if proficient else 0), "proficient": proficient})

    hit_die = class_hit_die(class_entity)
    hp_max = max(1, hit_die + modifiers["con"] + max(0, character.level - 1) * (math.floor(hit_die / 2) + 1 + modifiers["con"]))
    details = character.details_json or {}
    hp_current = int(details.get("current_hp", hp_max) or hp_max)
    temp_hp = int(details.get("temp_hp", 0) or 0)

    equipment = resolve_selected(db, list(character.selected_equipment or []))
    ac = 10 + modifiers["dex"]
    stealth_disadvantage = False
    strength_requirement = 0
    for item in equipment:
        item_ac, item_stealth, item_strength = _armor_values(item, modifiers["dex"])
        if item_ac is not None:
            ac = max(ac, item_ac)
            stealth_disadvantage = stealth_disadvantage or item_stealth
            strength_requirement = max(strength_requirement, item_strength)
    # Shield-like equipment commonly exposes +2 bonus without a base AC.
    for item in equipment:
        data = item.data_json or {}
        name = item.name.casefold()
        if "shield" in name and not _number(data.get("base_ac") or data.get("armor_class"), 0):
            ac += _number(data.get("ac_bonus") or _nested(data, "armor.ac_bonus"), 2)

    attacks = [_weapon_attack(item, final_scores, prof) for item in equipment if item.entity_type == "weapon"]
    spells = resolve_selected(db, list(character.selected_spells or []))
    prepared_set = set(character.prepared_spells or [])
    spells_by_level: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for spell in spells:
        data = spell.data_json or {}
        level = _number(data.get("level"), 0)
        spells_by_level[level].append({"entity": spell, "prepared": spell.public_id in prepared_set})

    spell_ability = class_spellcasting_ability(class_entity)
    spell_save_dc = 8 + prof + modifiers.get(spell_ability or "int", 0) if spell_ability else None
    spell_attack = prof + modifiers.get(spell_ability or "int", 0) if spell_ability else None

    currency = {coin: int((character.currency or {}).get(coin, 0) or 0) for coin in ("cp", "sp", "ep", "gp", "pp")}
    passive_perception = 10 + modifiers["wis"] + (prof if "Perception" in skills_prof else 0)
    save_rows = [{"ability": a, "name": ABILITY_NAMES[a], "modifier": modifiers[a] + (prof if a in saves else 0), "proficient": a in saves} for a in ABILITIES]
    feats = resolve_selected(db, list(character.feats or []))
    class_features = class_features_for_level(class_entity, character.level)
    skill_choice_count = class_skill_choice_count(class_entity)
    warnings = []
    if not species: warnings.append("Choose a species/race.")
    if not class_entity: warnings.append("Choose a class.")
    if character.ability_method == "point_buy":
        pb_total = point_buy_total(base_scores)
        if pb_total is None: warnings.append("Point Buy scores must be between 8 and 15 before bonuses.")
        elif pb_total > 27: warnings.append(f"Point Buy is over budget ({pb_total}/27 points).")
    if skill_choice_count is not None and len(character.skill_proficiencies or []) != skill_choice_count:
        warnings.append(f"Class data indicates {skill_choice_count} skill choice(s); {len(character.skill_proficiencies or [])} selected.")
    if strength_requirement and final_scores["str"] < strength_requirement:
        warnings.append(f"Selected armor has a Strength requirement of {strength_requirement}; current Strength is {final_scores['str']}.")
    if spells and not spell_ability:
        warnings.append("Spells are selected, but the class spellcasting ability could not be derived from cached data.")

    return {
        "character": character,
        "species": species, "class_entity": class_entity, "subclass": subclass,
        "background": background, "alignment": alignment,
        "base_scores": base_scores, "bonuses": dict(bonuses), "scores": final_scores, "modifiers": modifiers,
        "proficiency_bonus": prof, "save_proficiencies": saves, "saves": save_rows,
        "skill_proficiencies": skills_prof, "skills": skills,
        "hit_die": hit_die, "hp_max": hp_max, "current_hp": hp_current, "temp_hp": temp_hp,
        "armor_class": ac, "initiative": modifiers["dex"], "speed": species_speed(species),
        "passive_perception": passive_perception, "equipment": equipment, "attacks": attacks,
        "spells": spells, "spells_by_level": dict(spells_by_level), "spellcasting_ability": spell_ability,
        "spell_save_dc": spell_save_dc, "spell_attack_bonus": spell_attack,
        "currency": currency, "details": details, "stealth_disadvantage": stealth_disadvantage,
        "strength_requirement": strength_requirement,
        "point_buy_total": point_buy_total(base_scores), "feats": feats, "class_features": class_features,
        "skill_choice_count": skill_choice_count, "warnings": warnings,
        "other_proficiencies": other_proficiencies, "background_skills": background_skill_list,
        "background_other_proficiencies": background_other_list,
    }
