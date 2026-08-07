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


# Concise UI copy used only when cached Open5e records do not provide a usable
# summary. These are paraphrased builder hints, not replacement rules text.
SPECIES_SUMMARIES = {
    "dragonborn": "Dragonborn carry draconic ancestry into an adventuring life, pairing a humanoid frame with elemental breath and other traits tied to their lineage. They suit players who want a visibly magical heritage with strong combat identity.",
    "dwarf": "Dwarves are sturdy, enduring folk with a deep cultural connection to stone, craft, and ancestral traditions. Their traits emphasize resilience and unusual awareness of stonework and the earth beneath them.",
    "elf": "Elves are graceful, long-lived people whose lineages blend keen senses with innate magic. Their lineage choice further shapes movement, senses, and spells as the character advances.",
    "gnome": "Gnomes are small, clever, magically touched folk known for curiosity and mental resilience. Their traits reward inventive characters and grant distinctive supernatural talents tied to their lineage.",
    "goliath": "Goliaths descend from giant-kind and combine imposing stature with supernatural gifts that echo different giant ancestries. They are especially suited to characters who want physical presence and dramatic once-per-turn abilities.",
    "halfling": "Halflings are small, nimble adventurers with remarkable luck and courage. Their traits make them reliable under pressure and unusually good at slipping through dangerous situations.",
    "human": "Humans are adaptable and broadly capable, with traits that emphasize versatility rather than a narrow specialization. They are an excellent choice when you want extra flexibility in how the character develops.",
    "orc": "Orcs are powerful, relentless humanoids whose traits emphasize endurance, speed, and aggressive movement. They fit characters who want to close distance quickly and stay standing when a fight becomes brutal.",
    "tiefling": "Tieflings carry a supernatural legacy connected to the Lower Planes, expressed through resistance and innate magic. Their chosen fiendish legacy determines the flavor and progression of those magical traits.",
}

CLASS_SUMMARIES = {
    "barbarian": "A durable front-line warrior who channels Rage to hit harder and withstand punishment. Barbarians are straightforward to run in combat while still offering meaningful tactical choices through subclass and weapon use.",
    "bard": "A versatile spellcaster and expert who supports allies, solves problems with skills, and manipulates the battlefield with magic. Bards reward players who enjoy flexibility and social as well as tactical play.",
    "cleric": "A divine spellcaster who can heal, protect, control, and punish foes while remaining durable enough for the front line. Domain choices shape which divine role the character emphasizes.",
    "druid": "A nature-focused spellcaster who blends healing, battlefield control, elemental magic, and transformation. Druids suit players who want a broad toolset and strong exploration utility.",
    "fighter": "A highly adaptable martial specialist with excellent weapon and armor access. Fighters are easy to understand at the core but support deep customization through fighting style, mastery choices, feats, and subclass.",
    "monk": "A mobile martial artist who fights with rapid strikes, disciplined movement, and supernatural focus. Monks reward positioning and resource management rather than heavy armor or large weapons.",
    "paladin": "A heavily armored champion who combines martial combat with divine magic, protective auras, and powerful smites. Paladins excel when defending allies while threatening dangerous enemies up close.",
    "ranger": "A martial explorer who combines weapons, survival expertise, and nature magic. Rangers are well suited to players who want strong exploration identity without giving up reliable combat options.",
    "rogue": "A precision-based expert built around skills, mobility, and devastating Sneak Attacks. Rogues shine when the player enjoys positioning, infiltration, and solving problems through expertise.",
    "sorcerer": "An innate arcane spellcaster who reshapes magic through personal power and Metamagic. Sorcerers trade the wizard's breadth for a focused spell list they can manipulate in distinctive ways.",
    "warlock": "An occult spellcaster whose pact grants unusual magic, invocations, and highly customizable supernatural abilities. Warlocks reward players who enjoy building a character from modular magical choices.",
    "wizard": "A scholarly arcane spellcaster with the broadest spellbook-driven toolkit. Wizards reward preparation, experimentation, and players who enjoy choosing the right spell for a difficult problem.",
}

BACKGROUND_SUMMARIES = {
    "acolyte": "A life of religious service taught you ritual, study, and the practical responsibilities of faith. This background naturally supports perceptive, scholarly, and divine-minded characters.",
    "artisan": "You learned a trade through apprenticeship and practical craft, along with the social instincts needed to work with customers and patrons. It suits capable makers and detail-oriented adventurers.",
    "charlatan": "You learned how to read people, sell a convincing story, and survive by deception or questionable deals. It fits characters built around confidence, improvisation, and social manipulation.",
    "criminal": "You survived through theft, illicit work, or connections to the underworld. Criminal characters tend to bring stealth, caution, and practical knowledge of getting into places they should not be.",
    "entertainer": "You developed your talents in front of an audience and learned how to hold attention under pressure. This background fits expressive characters who thrive on performance and presence.",
    "farmer": "You grew up working land or livestock and learned endurance, practicality, and respect for the natural world. It suits grounded characters who are tougher than their humble origins suggest.",
    "guard": "You spent years watching for trouble and responding when it arrived. Guards bring vigilance, discipline, and experience recognizing danger before others do.",
    "guide": "You made a living navigating wilderness and helping others survive it. Guides naturally complement exploration-focused characters and those comfortable far from civilization.",
    "hermit": "You spent significant time apart from ordinary society in contemplation, study, or spiritual isolation. Hermits fit introspective characters whose insight comes from patience and unusual experience.",
    "merchant": "Trade taught you how to judge value, negotiate terms, and endure long journeys between markets. Merchants make practical, socially capable adventurers with strong logistical instincts.",
    "noble": "You were raised around wealth, etiquette, hierarchy, and political expectations. Nobles fit characters comfortable with leadership, courtly intrigue, and the pressures of reputation.",
    "sage": "Years of study gave you a habit of research and an appetite for difficult questions. Sages naturally support knowledge-focused characters and aspiring spellcasters.",
    "sailor": "Life on the water taught you teamwork, endurance, and respect for dangerous weather and stranger shores. Sailors fit adaptable adventurers comfortable with travel and physical risk.",
    "scribe": "Your work revolved around records, copying, correspondence, and careful attention to written detail. Scribes fit observant characters who value information and precision.",
    "soldier": "Military training gave you discipline, battlefield habits, and familiarity with weapons and command. Soldiers fit characters whose adventuring instincts were forged through organized conflict.",
    "wayfarer": "You learned to survive without the security most people take for granted, relying on adaptability, street sense, and stubborn hope. Wayfarers fit resourceful characters who make their own opportunities.",
}

DEFAULT_SUBCLASS_PARENTS = {
    "berserker": "barbarian", "lore": "bard", "life": "cleric", "land": "druid",
    "champion": "fighter", "open-hand": "monk", "devotion": "paladin", "hunter": "ranger",
    "thief": "rogue", "draconic-sorcery": "sorcerer", "fiend": "warlock", "evoker": "wizard",
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
