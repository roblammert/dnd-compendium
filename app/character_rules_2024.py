"""Pinned D&D 2024 character-generation rules used by the Character Builder.

The builder is intentionally not edition-selectable. Open5e remains the local
reference-data cache, while this module supplies stable mechanical defaults for
SRD 5.2.1 / the 2024 fifth-edition rules when an Open5e record omits a field.

Keep this module limited to rules facts/calculation metadata; descriptive rules
text remains in the cached compendium entities.
"""
from __future__ import annotations

RULESET_SOURCE_KEY = "srd-2024"
RULESET_SOURCE_LABEL = "5e 2024 Rules"
RULESET_GAME_SYSTEM_KEY = "5e-2024"
RULESET_GAME_SYSTEM_LABEL = "5th Edition 2024"
RULESET_DISPLAY_NAME = "D&D 5e 2024"

# Core class creation metadata. These values are fallbacks only: when the
# matching srd-2024 Open5e entity exposes structured values, that data wins.
CLASS_RULES: dict[str, dict] = {
    "barbarian": {"hit_die": 12, "saves": ["str", "con"], "skill_count": 2,
        "skills": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]},
    "bard": {"hit_die": 8, "saves": ["dex", "cha"], "skill_count": 3,
        "skills": "any", "spellcasting_ability": "cha"},
    "cleric": {"hit_die": 8, "saves": ["wis", "cha"], "skill_count": 2,
        "skills": ["History", "Insight", "Medicine", "Persuasion", "Religion"], "spellcasting_ability": "wis"},
    "druid": {"hit_die": 8, "saves": ["int", "wis"], "skill_count": 2,
        "skills": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"], "spellcasting_ability": "wis"},
    "fighter": {"hit_die": 10, "saves": ["str", "con"], "skill_count": 2,
        "skills": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"]},
    "monk": {"hit_die": 8, "saves": ["str", "dex"], "skill_count": 2,
        "skills": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"]},
    "paladin": {"hit_die": 10, "saves": ["wis", "cha"], "skill_count": 2,
        "skills": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"], "spellcasting_ability": "cha"},
    "ranger": {"hit_die": 10, "saves": ["str", "dex"], "skill_count": 3,
        "skills": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"], "spellcasting_ability": "wis"},
    "rogue": {"hit_die": 8, "saves": ["dex", "int"], "skill_count": 4,
        "skills": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"]},
    "sorcerer": {"hit_die": 6, "saves": ["con", "cha"], "skill_count": 2,
        "skills": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"], "spellcasting_ability": "cha"},
    "warlock": {"hit_die": 8, "saves": ["wis", "cha"], "skill_count": 2,
        "skills": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"], "spellcasting_ability": "cha"},
    "wizard": {"hit_die": 6, "saves": ["int", "wis"], "skill_count": 2,
        "skills": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Nature", "Religion"], "spellcasting_ability": "int"},
}

# Free Rules / SRD 5.2.1 backgrounds. Mechanical metadata supplements incomplete
# cached records; no long-form copyrighted text is embedded here.
BACKGROUND_RULES: dict[str, dict] = {
    "acolyte": {"abilities": ["int", "wis", "cha"], "skills": ["Insight", "Religion"],
        "tool": "Calligrapher's Supplies", "origin_feat": "Magic Initiate (Cleric)"},
    "criminal": {"abilities": ["dex", "con", "int"], "skills": ["Sleight of Hand", "Stealth"],
        "tool": "Thieves' Tools", "origin_feat": "Alert"},
    "sage": {"abilities": ["con", "int", "wis"], "skills": ["Arcana", "History"],
        "tool": "Calligrapher's Supplies", "origin_feat": "Magic Initiate (Wizard)"},
    "soldier": {"abilities": ["str", "dex", "con"], "skills": ["Athletics", "Intimidation"],
        "tool": "Gaming Set", "origin_feat": "Savage Attacker"},
}

STANDARD_LANGUAGES = [
    "Common", "Common Sign Language", "Draconic", "Dwarvish", "Elvish",
    "Giant", "Gnomish", "Goblin", "Halfling", "Orc",
]

# Minimum XP for each character level under the 2024 rules.
LEVEL_XP = {
    1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500, 6: 14000, 7: 23000,
    8: 34000, 9: 48000, 10: 64000, 11: 85000, 12: 100000,
    13: 120000, 14: 140000, 15: 165000, 16: 195000, 17: 225000,
    18: 265000, 19: 305000, 20: 355000,
}


def canonical_rule_key(name: str | None) -> str:
    return str(name or "").strip().casefold().replace("_", "-").replace(" ", "-")


def class_rule(name_or_key: str | None) -> dict:
    key = canonical_rule_key(name_or_key)
    return CLASS_RULES.get(key, {})


def background_rule(name_or_key: str | None) -> dict:
    key = canonical_rule_key(name_or_key)
    return BACKGROUND_RULES.get(key, {})
