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
    class_rule, background_rule, canonical_rule_key, class_gear_rule, background_gear_rule, spell_slot_totals,
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


def _print_block_markdown(value: Any) -> str:
    """Normalize an Open5e descriptive block without exposing table placeholders."""
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        text = value.strip()
        return "" if _is_column_placeholder(text) else text
    if isinstance(value, list):
        parts = [_print_block_markdown(item) for item in value]
        return "\n\n".join(part for part in parts if part)
    if isinstance(value, dict):
        name = _text(value.get("name") or value.get("title") or value.get("label")).strip()
        desc = ""
        for key in ("desc", "description", "text", "detail", "details", "content"):
            if key in value:
                desc = _print_block_markdown(value.get(key))
                if desc:
                    break
        if name and desc and name.casefold() not in desc.casefold()[: max(40, len(name) + 8)]:
            return f"**{name}.** {desc}"
        if desc:
            return desc
        # Some Open5e species traits put prose in nested values without a desc key.
        nested = []
        for key, child in value.items():
            if key in {"name", "title", "label", "key", "slug", "document", "gamesystem"}:
                continue
            text = _print_block_markdown(child)
            if text:
                nested.append(text)
        body = "\n\n".join(dict.fromkeys(nested))
        if name and body:
            return f"**{name}.** {body}"
        return body
    return str(value).strip()


def _markdown_table(rows: list[tuple[str, str]]) -> str:
    rows = [(str(k).strip(), str(v).strip()) for k, v in rows if str(v).strip()]
    if not rows:
        return ""
    body = ["| Detail | Value |", "|---|---|"]
    body.extend(f"| {k.replace('|', '/')} | {v.replace('|', '/')} |" for k, v in rows)
    return "\n".join(body)


def entity_print_profile(entity: Entity | None, kind: str = "") -> str:
    """Return useful printable identity/trait content from the cached Open5e record.

    Printable profiles intentionally differ from the short builder summaries. Species
    can expose their useful text through ``traits`` while classes often store their
    core identity in ``core_traits`` rather than a top-level description.
    """
    if not entity:
        return ""
    data = entity.data_json or {}
    key = canonical_rule_key(entity.canonical_key or entity.slug or entity.name)
    parts: list[str] = []
    summary = entity_summary(entity).strip()
    if not summary:
        if kind == "species":
            summary = SPECIES_SUMMARIES.get(key, "")
        elif kind == "class":
            summary = CLASS_SUMMARIES.get(key, "")
        elif kind == "background":
            summary = BACKGROUND_SUMMARIES.get(key, "")
    if summary:
        parts.append(summary)

    if kind == "species":
        traits = _nested(data, "traits", "species_traits", "racial_traits", "features")
        trait_text = _print_block_markdown(traits)
        if trait_text:
            parts.append(trait_text)

    if kind == "class":
        core = data.get("core_traits") if isinstance(data.get("core_traits"), dict) else {}
        rows: list[tuple[str, str]] = []
        labels = {
            "primary_ability": "Primary Ability",
            "hit_point_die": "Hit Point Die",
            "saving_throw_proficiencies": "Saving Throws",
            "skill_proficiencies": "Skill Proficiencies",
            "weapon_proficiencies": "Weapons",
            "armor_training": "Armor Training",
            "starting_equipment": "Starting Equipment",
        }
        for raw_key, label in labels.items():
            if raw_key in core:
                value = _text(core.get(raw_key)).strip()
                if value and not _is_column_placeholder(value):
                    rows.append((label, value))
        # Older/newer cached shapes may expose the same facts at top level.
        if not rows:
            candidates = [
                ("Hit Point Die", _text(_nested(data, "hit_die", "hit_dice"))),
                ("Primary Ability", _text(_nested(data, "primary_ability", "primary_abilities"))),
                ("Saving Throws", _text(_nested(data, "saving_throw_proficiencies", "saving_throws"))),
                ("Armor Training", _text(_nested(data, "armor_training", "armor_proficiencies"))),
                ("Weapons", _text(_nested(data, "weapon_proficiencies", "weapons"))),
            ]
            rows.extend((label, value) for label, value in candidates if value)
        if not rows:
            rule = class_rule(key)
            fallback_rows = [
                ("Hit Point Die", f"d{rule.get('hit_die')}" if rule.get("hit_die") else ""),
                ("Saving Throws", ", ".join(ABILITY_NAMES.get(a, a.upper()) for a in rule.get("saves", []))),
            ]
            skills = rule.get("skills")
            if skills == "any":
                fallback_rows.append(("Skill Proficiencies", f"Choose {rule.get('skill_count', '')} skills".strip()))
            elif skills:
                fallback_rows.append(("Skill Proficiencies", f"Choose {rule.get('skill_count', '')}: " + ", ".join(skills)))
            rows.extend((label, value) for label, value in fallback_rows if value)
        table = _markdown_table(rows)
        if table:
            parts.append(table)

    if kind == "subclass" and not parts:
        details = _print_block_markdown(_nested(data, "features", "traits", "benefits"))
        if details:
            parts.append(details)

    return "\n\n".join(part for part in parts if part).strip()



def feat_print_profile(entity: Entity | None) -> str:
    """Return complete printable feat prose from summary plus structured benefit fields."""
    if not entity:
        return ""
    data = entity.data_json or {}
    parts: list[str] = []
    for value in (data.get("desc"), data.get("description"), entity.summary):
        text = _print_block_markdown(value)
        if text and text not in parts:
            parts.append(text)
    for key in ("benefits", "benefit", "features", "effects", "descriptions"):
        text = _print_block_markdown(data.get(key))
        if text and text not in parts:
            parts.append(text)
    return "\n\n".join(parts).strip()


def species_hp_per_level_bonus(entity: Entity | None) -> int:
    """Detect a species trait that increases HP maximum once per character level."""
    if not entity:
        return 0
    blob = _text(entity.data_json or {})
    match = re.search(r"Hit Point maximum increases by\s+(\d+).*?whenever you gain a level", blob, re.I | re.S)
    if match:
        return int(match.group(1))
    return 1 if canonical_rule_key(entity.canonical_key or entity.slug or entity.name) == "dwarf" and "Dwarven Toughness" in blob else 0


def hit_dice_print_guide(character: Character, class_entity: Entity | None, species: Entity | None, hit_die: int, con_mod: int) -> dict[str, Any]:
    count = max(1, int(character.level or 1))
    fixed_die = math.floor(hit_die / 2) + 1
    species_bonus = species_hp_per_level_bonus(species)
    class_name = class_entity.name if class_entity else "your class"
    species_note = ""
    if species_bonus:
        species_name = species.name if species else "Your species"
        species_note = f" {species_name} adds +{species_bonus} HP to your maximum at each level; this does not change the die you roll during a Short Rest."
    fixed_gain = fixed_die + con_mod + species_bonus
    roll_extra = con_mod + species_bonus
    return {
        "title": f"{count}d{hit_die}",
        "short_rest": f"You have {count} d{hit_die} Hit Point Dice from {class_name} {count}. During a Short Rest, spend one or more unspent dice. For each die, roll 1d{hit_die} {con_mod:+d}; regain at least 1 HP from that die, and decide after each roll whether to spend another.",
        "long_rest": "After a Long Rest, you regain all lost HP and all spent Hit Point Dice.",
        "level_up": f"When you gain another {class_name} level, add one d{hit_die} Hit Point Die. For maximum HP, the fixed-value method adds {fixed_gain} HP ({fixed_die} + CON {con_mod:+d}{f' + species {species_bonus}' if species_bonus else ''}); if your table rolls, use 1d{hit_die} {roll_extra:+d}.{species_note}"
    }


def roll_reference_rows(skills: list[dict[str, Any]], saves: list[dict[str, Any]], modifiers: dict[str, int]) -> list[dict[str, str]]:
    """Build character-specific d20 guidance for every ability."""
    by_ability: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for skill in skills:
        by_ability[skill["ability"]].append(skill)
    generic = {
        "str": ["lift, push, or break something", "force open a stuck door"],
        "dex": ["balance or move quietly", "perform precise handwork"],
        "con": ["endure harsh conditions", "push through prolonged exertion"],
        "int": ["recall lore", "reason through clues"],
        "wis": ["notice danger", "read a creature's intentions"],
        "cha": ["influence someone", "mislead or intimidate someone"],
    }
    save_map = {row["ability"]: row for row in saves}
    result = []
    for ability in ABILITIES:
        candidates = sorted(by_ability.get(ability, []), key=lambda r: (not r.get("proficient", False), r.get("name", "")))
        examples = []
        for skill in candidates[:2]:
            examples.append(f"{skill['name']} {skill['modifier']:+d}{' (proficient)' if skill.get('proficient') else ''}")
        if not examples:
            examples = [f"{label}: {modifiers[ability]:+d}" for label in generic[ability][:2]]
        elif len(examples) < 2:
            examples.append(f"Other {ABILITY_NAMES[ability]} check {modifiers[ability]:+d}")
        save = save_map[ability]
        result.append({
            "ability": ability.upper(),
            "save": f"d20 {save['modifier']:+d}" + (" (proficient)" if save.get("proficient") else ""),
            "check": f"d20 {modifiers[ability]:+d}",
            "examples": "; ".join(examples[:2]),
        })
    return result


def roll_reference_notes(species: Entity | None) -> list[str]:
    if not species:
        return []
    blob = _text(species.data_json or {})
    notes = []
    if re.search(r"Advantage on saving throws.*?(?:avoid or end).*?Poisoned", blob, re.I | re.S):
        notes.append("Species trait: you have Advantage on saving throws made to avoid or end the Poisoned condition.")
    return notes

def _is_column_placeholder(value: Any) -> bool:
    text = _text(value).strip().casefold()
    return text in {"[column data]", "column data", "[column-data]", "—", "-"}


def equipment_print_rows(equipment: list[Entity]) -> list[dict[str, Entity | None]]:
    """Legacy two-group helper retained for compatibility with older tests/callers."""
    split = (len(equipment) + 1) // 2
    left = equipment[:split]
    right = equipment[split:]
    rows = []
    for index, item in enumerate(left):
        rows.append({"left": item, "right": right[index] if index < len(right) else None})
    return rows


def equipment_weight_data(db: Session, entity: Entity) -> str:
    """Return printable weight, using the same source-aware Item fallback as Weapon cards."""
    from app.services import format_weight, _numeric_value
    data = entity.data_json or {}
    raw = _equipment_value_local(data, "weight")
    if entity.entity_type == "weapon" and _numeric_value(raw) in (None, 0):
        fallback = weapon_item_fallback(db, entity)
        if fallback:
            raw = _equipment_value_local(fallback.data_json or {}, "weight")
    if raw in (None, "", [], {}):
        return ""
    return format_weight(raw, present=True)


def equipment_print_columns(db: Session, equipment: list[Entity], *, groups: int = 3, minimum_rows: int = 8) -> list[list[dict[str, str]]]:
    """Build balanced printable equipment rows across three Item/Type/Weight groups.

    A few blank rows are intentionally retained so the printed sheet can be updated
    during play.
    """
    groups = max(1, int(groups))
    used_rows = math.ceil(len(equipment) / groups) if equipment else 0
    row_count = max(minimum_rows, used_rows)
    columns: list[list[dict[str, str]]] = []
    for group in range(groups):
        group_rows = []
        start = group * used_rows
        group_items = list(equipment[start:start + used_rows]) if used_rows else []
        group_items += [None] * max(0, row_count - len(group_items))
        for item in group_items:
            if item is None:
                group_rows.append({"name": "", "type": "", "weight": ""})
            else:
                group_rows.append({
                    "name": item.name,
                    "type": item.entity_type.replace("_", " ").title(),
                    "weight": equipment_weight_data(db, item),
                })
        columns.append(group_rows)
    rows = []
    for row_index in range(row_count):
        rows.append([columns[group][row_index] for group in range(groups)])
    return rows



CORE_CONDITIONS_2024 = [
    "Blinded", "Charmed", "Deafened", "Exhaustion", "Frightened",
    "Grappled", "Incapacitated", "Invisible", "Paralyzed", "Petrified",
    "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious",
]

def spell_usage_print_guide(character: Character, class_entity: Entity | None, spell_ability: str | None,
                            spell_save_dc: int | None, spell_attack: int | None, slots: dict[int, int],
                            prepared_count: int) -> dict[str, Any]:
    class_key = canonical_rule_key(class_entity.canonical_key or class_entity.slug or class_entity.name) if class_entity else ""
    class_name = class_entity.name if class_entity else "your class"
    ability_name = ABILITY_NAMES.get(spell_ability or "", (spell_ability or "your spellcasting ability").upper())
    pact = class_key == "warlock"
    slot_summary = ", ".join(f"L{level}: {count}" for level, count in sorted(slots.items())) or "No spell slots at this level"
    change_when = "after a Long Rest or when leveling up, as your class permits"
    return {
        "class_name": class_name,
        "ability_name": ability_name,
        "prepared_count": prepared_count,
        "slot_summary": slot_summary,
        "recovery": "Short or Long Rest" if pact else "Long Rest",
        "change_when": change_when,
        "save_dc": spell_save_dc,
        "attack_bonus": spell_attack,
        "pact": pact,
    }

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
    """Normalize actual class features while excluding Open5e progression-table cells.

    Open5e class payloads can mix prose feature records with synthetic table-column
    records whose descriptions are literally ``[Column data]``.  Those cells are
    useful to the web class table but are not character features and must never be
    printed.  Duplicate feature names prefer the entry containing real prose.
    """
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "features", "class_features", "levels", "progression")
    items = raw if isinstance(raw, list) else []
    result_by_name: dict[str, dict[str, Any]] = {}
    structural_names = {"proficiency bonus", "prepared spells"}
    ordinal = re.compile(r"^(?:\d+)(?:st|nd|rd|th)$", re.I)
    for item in items:
        if not isinstance(item, dict):
            continue
        explicit_level = item.get("level") if item.get("level") not in (None, "") else item.get("class_level")
        feature_level = _number(explicit_level, 0) if explicit_level not in (None, "") else 0
        if feature_level and feature_level > level:
            continue
        name = _text(item.get("name") or item.get("feature") or item.get("title")).strip()
        if not name:
            continue
        raw_desc = item.get("desc") or item.get("description") or item.get("text") or item.get("detail")
        if _is_column_placeholder(raw_desc):
            continue
        desc = _print_block_markdown(raw_desc)
        normalized = re.sub(r"\s+", " ", name).strip().casefold()
        if not desc and (normalized in structural_names or ordinal.match(normalized)):
            continue
        # Class spell-list appendices are reference catalogs, not possessed features.
        if normalized.endswith(" spell list"):
            continue
        # Generic subclass-choice rows are structural once a subclass has been selected.
        if normalized.endswith(" subclasses") or normalized == "subclasses":
            continue
        existing = result_by_name.get(normalized)
        candidate = {"name": name, "level": feature_level or 1, "description": desc}
        if existing is None or (not existing.get("description") and desc):
            result_by_name[normalized] = candidate
    return list(result_by_name.values())


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


def background_uses_2024_adjustment(entity: Entity | None) -> bool:
    """Only exact 5e 2024 Rules backgrounds use the 2024 background ASI widget."""
    return bool(entity and entity.source_document == RULESET_SOURCE_KEY)

def _norm_equipment_name(value: str | None) -> str:
    text = canonical_rule_key(value)
    # normalize common Open5e singular/plural/name variants used by package rules
    aliases = {
        "handaxes":"handaxe", "daggers":"dagger", "javelins":"javelin",
        "arrows":"arrow", "pouches":"pouch", "travelers-clothes":"traveler-s-clothes",
        "traveler-s-clothes":"traveler-s-clothes", "chainmail":"chain-mail",
        "studded-leather":"studded-leather-armor", "thieves-tools":"thieves-tools",
    }
    return aliases.get(text, text)

def _starting_names_from_entity(entity: Entity | None) -> list[str]:
    if not entity:
        return []
    data = entity.data_json or {}
    raw = _nested(data, "starting_equipment", "equipment", "core_traits.starting_equipment")
    result: list[str] = []
    def add(value):
        if isinstance(value, dict):
            # Ignore coin-only entries and option wrappers where possible.
            name = _text(value.get("name") or value.get("item") or value.get("equipment") or value.get("choice"))
            if name and not re.search(r"\b[pgsc]p\b", name, re.I): result.append(name)
            for key in ("items","equipment","contents","option_a","a"):
                if key in value: add(value[key])
        elif isinstance(value, list):
            for item in value: add(item)
        elif isinstance(value, str):
            # Extract comma-separated textual package A before an alternate "or" gold option.
            text=value.split(" or ")[0]
            for part in re.split(r",| and ", text):
                part=re.sub(r"^\s*(?:\(A\)\s*)?\d+\s+", "", part).strip(" .()")
                if part and not re.search(r"\b\d+\s*(?:PP|GP|SP|CP)\b", part, re.I): result.append(part)
    add(raw)
    return list(dict.fromkeys(result))

def starting_equipment_names(class_entity: Entity | None, background_entity: Entity | None, species_entity: Entity | None = None) -> dict[str, list[str]]:
    class_names = _starting_names_from_entity(class_entity)
    if not class_names and class_entity:
        class_names = list(class_gear_rule(class_entity.canonical_key or class_entity.slug or class_entity.name).get("equipment", []))
    background_names = _starting_names_from_entity(background_entity)
    if not background_names and background_entity and background_uses_2024_adjustment(background_entity):
        background_names = list(background_gear_rule(background_entity.canonical_key or background_entity.slug or background_entity.name).get("equipment", []))
    species_names = _starting_names_from_entity(species_entity)
    return {"class": class_names, "background": background_names, "species": species_names}

def class_armor_training(entity: Entity | None) -> list[str]:
    if not entity: return []
    data=entity.data_json or {}
    raw=_nested(data,"armor_training","armor_proficiencies","proficiencies.armor","core_traits.armor_training")
    text=_text(raw).casefold()
    result=[]
    for key in ("light","medium","heavy","shield"):
        if key in text: result.append(key)
    if result: return result
    return list(class_gear_rule(entity.canonical_key or entity.slug or entity.name).get("armor", []))

def class_weapon_training(entity: Entity | None) -> list[str]:
    if not entity: return []
    data=entity.data_json or {}
    raw=_nested(data,"weapon_proficiencies","proficiencies.weapons","core_traits.weapon_proficiencies")
    text=_text(raw).casefold()
    result=[]
    if "simple" in text: result.append("simple")
    if "martial" in text: result.append("martial")
    if result: return result
    return list(class_gear_rule(entity.canonical_key or entity.slug or entity.name).get("weapons", []))

def equipment_armor_kind(entity: Entity) -> str:
    if entity.entity_type != "armor" and "armor" not in entity.name.casefold() and "shield" not in entity.name.casefold():
        data=entity.data_json or {}; nested=data.get("armor")
        if not isinstance(nested,dict): return ""
    data=entity.data_json or {}; armor=data.get("armor") if isinstance(data.get("armor"),dict) else data
    text=_text(armor.get("category") or armor.get("armor_category") or data.get("category") or entity.name).casefold()
    if "shield" in text or "shield" in entity.name.casefold(): return "shield"
    for kind in ("light","medium","heavy"):
        if kind in text: return kind
    return "armor" if entity.entity_type=="armor" else ""

def _equipment_value_local(data: dict, *keys: str):
    for key in keys:
        value=data.get(key)
        if value not in (None,"",[],{}): return value
    for wrapper in ("weapon","item","equipment","armor"):
        nested=data.get(wrapper)
        if isinstance(nested,dict):
            for key in keys:
                value=nested.get(key)
                if value not in (None,"",[],{}): return value
    return None

def _item_candidates_for_weapon(db: Session, weapon: Entity) -> list[Entity]:
    rows=list(db.scalars(select(Entity).where(Entity.entity_type=="item",Entity.is_active.is_(True))).all())
    keys={_norm_equipment_name(weapon.name),_norm_equipment_name(weapon.canonical_key),_norm_equipment_name(weapon.slug)}
    return [r for r in rows if {_norm_equipment_name(r.name),_norm_equipment_name(r.canonical_key),_norm_equipment_name(r.slug)} & keys]

def weapon_item_fallback(db: Session, weapon: Entity) -> Entity | None:
    rows=_item_candidates_for_weapon(db,weapon)
    if not rows: return None
    same=[r for r in rows if r.source_document==weapon.source_document]
    if same: return same[0]
    same_system=[r for r in rows if r.game_system_key==weapon.game_system_key]
    if same_system: return same_system[0]
    return rows[0] if len(rows)==1 else rows[0]

def equipment_cost_data(db: Session, entity: Entity) -> dict[str, Any]:
    from app.services import format_cost, _numeric_value
    data=entity.data_json or {}; fallback=None
    raw=_equipment_value_local(data,"cost","price","value")
    if entity.entity_type=="weapon" and _numeric_value(raw) in (None,0):
        fallback=weapon_item_fallback(db,entity)
        if fallback: raw=_equipment_value_local(fallback.data_json or {},"cost","price","value")
    display=format_cost(raw,present=raw not in (None,"",[],{}))
    return {"value":display.get("value") or "—","tooltip":display.get("tooltip") or "","gp":_numeric_value(raw) or 0.0}

def equipment_reference_rows(db: Session, character: Character, endpoint_labels: dict[str,str] | None=None) -> list[dict[str,Any]]:
    endpoint_labels=endpoint_labels or {}
    raw=entities_for_character(db,["equipment","item","weapon","armor"],character)
    # Hide generic item records when a dedicated weapon/armor with the same canonical identity exists.
    dedicated={_norm_equipment_name(e.canonical_key or e.name) for e in raw if e.entity_type in {"weapon","armor"}}
    rows=[]
    for entity in raw:
        if entity.entity_type=="item" and _norm_equipment_name(entity.canonical_key or entity.name) in dedicated:
            continue
        rows.append(entity)
    class_entity=find_character_entity(db,character,["class","classe"],character.class_key)
    background=find_any_character_entity(db,["background"],character.background_key)
    species=find_character_entity(db,character,["species","race"],character.species_key)
    packages=starting_equipment_names(class_entity,background,species)
    lock_names={source:{_norm_equipment_name(v) for v in names} for source,names in packages.items()}
    armor_training=set(class_armor_training(class_entity)); weapon_training=class_weapon_training(class_entity)
    result=[]
    for entity in rows:
        norm={_norm_equipment_name(entity.name),_norm_equipment_name(entity.canonical_key),_norm_equipment_name(entity.slug)}
        locked_source=next((src for src,names in lock_names.items() if norm & names),"")
        kind=equipment_armor_kind(entity)
        trained=(not kind) or kind in armor_training or (kind=="armor" and bool(armor_training))
        data=entity.data_json or {}; blob=_text(_nested(data,"properties","weapon.properties","category","weapon.category")).casefold()+" "+entity.name.casefold()
        if entity.entity_type=="weapon":
            if "martial" in blob:
                weapon_prof="martial" in weapon_training or ("martial-light" in weapon_training and "light" in blob) or ("martial-finesse-light" in weapon_training and ("light" in blob or "finesse" in blob))
            else:
                weapon_prof="simple" in weapon_training
        else: weapon_prof=True
        cost=equipment_cost_data(db,entity)
        semantic_type = "armor" if kind else ("weapon" if entity.entity_type == "weapon" else "item")
        result.append({
            "entity":entity,"type_label":endpoint_labels.get(entity.entity_type,entity.entity_type.replace('_',' ').replace('-',' ').title()),
            "filter_type": semantic_type,
            "locked":bool(locked_source),"locked_source":locked_source,"armor_kind":kind,"armor_trained":trained,
            "weapon_proficient":weapon_prof,"cost":cost["value"],"cost_tooltip":cost["tooltip"],"cost_gp":cost["gp"],
            "summary":builder_summary(entity,entity.entity_type),
        })
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
    subclass = find_character_entity(db, character, ["subclass", "subclasse", "class", "classe"], character.subclass_key)

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
    hp_max = max(1, hit_die + modifiers["con"] + max(0, character.level - 1) * (math.floor(hit_die / 2) + 1 + modifiers["con"]) + species_hp_per_level_bonus(species) * character.level)
    details = character.details_json or {}
    hp_current = int(details.get("current_hp", hp_max) or hp_max)
    temp_hp = int(details.get("temp_hp", 0) or 0)

    gear_rows = equipment_reference_rows(db, character)
    auto_ids = [row["entity"].public_id for row in gear_rows if row["locked"]]
    equipment = resolve_selected(db, list(dict.fromkeys(list(character.selected_equipment or []) + auto_ids)))
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
    spell_slots = spell_slot_totals(class_entity.name if class_entity else None, character.level)

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
        "spell_slots": spell_slots,
        "spell_usage_guide": spell_usage_print_guide(character, class_entity, spell_ability, spell_save_dc, spell_attack, spell_slots, len(prepared_set)),
        "core_conditions": CORE_CONDITIONS_2024,
        "currency": currency, "details": details, "stealth_disadvantage": stealth_disadvantage,
        "strength_requirement": strength_requirement,
        "point_buy_total": point_buy_total(base_scores), "feats": feats, "class_features": class_features,
        "feat_print_profiles": {feat.public_id: feat_print_profile(feat) for feat in feats},
        "hit_dice_guide": hit_dice_print_guide(character, class_entity, species, hit_die, modifiers["con"]),
        "roll_reference_rows": roll_reference_rows(skills, save_rows, modifiers),
        "roll_reference_notes": roll_reference_notes(species),
        "print_profiles": {
            "species": entity_print_profile(species, "species"),
            "class": entity_print_profile(class_entity, "class"),
            "background": entity_print_profile(background, "background"),
            "subclass": entity_print_profile(subclass, "subclass"),
        },
        "equipment_print_rows": equipment_print_rows(equipment),
        "equipment_print_columns": equipment_print_columns(db, equipment),
        "equipment_print_compact": len(equipment) > 10,
        "skill_choice_count": skill_choice_count, "warnings": warnings,
        "other_proficiencies": other_proficiencies, "background_skills": background_skill_list,
        "background_other_proficiencies": background_other_list,
    }
