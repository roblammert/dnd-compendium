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

# 2024 Player's Handbook subclass -> base-class map.  Open5e sources do not
# always classify these records consistently: some subclass-shaped records may
# arrive through a class-like endpoint.  Character Builder uses this map to
# normalize the UI into exactly twelve primary classes with subclasses nested
# beneath their parent class.
DEFAULT_SUBCLASS_PARENTS = {
    # Barbarian
    "path-of-the-berserker": "barbarian", "berserker": "barbarian",
    "path-of-the-wild-heart": "barbarian", "wild-heart": "barbarian",
    "path-of-the-world-tree": "barbarian", "world-tree": "barbarian",
    "path-of-the-zealot": "barbarian", "zealot": "barbarian",
    # Bard
    "college-of-dance": "bard", "dance": "bard",
    "college-of-glamour": "bard", "glamour": "bard",
    "college-of-lore": "bard", "lore": "bard",
    "college-of-valor": "bard", "college-of-valour": "bard", "valor": "bard", "valour": "bard",
    # Cleric
    "life-domain": "cleric", "life": "cleric",
    "light-domain": "cleric", "light": "cleric",
    "trickery-domain": "cleric", "trickery": "cleric",
    "war-domain": "cleric", "war": "cleric",
    # Druid
    "circle-of-the-land": "druid", "land": "druid",
    "circle-of-the-moon": "druid", "moon": "druid",
    "circle-of-the-sea": "druid", "sea": "druid",
    "circle-of-the-stars": "druid", "stars": "druid",
    # Fighter
    "battle-master": "fighter", "battlemaster": "fighter",
    "champion": "fighter",
    "eldritch-knight": "fighter",
    "psi-warrior": "fighter",
    # Monk
    "warrior-of-mercy": "monk", "mercy": "monk",
    "warrior-of-shadow": "monk", "shadow": "monk",
    "warrior-of-the-elements": "monk", "elements": "monk",
    "warrior-of-the-open-hand": "monk", "open-hand": "monk",
    # Paladin
    "oath-of-devotion": "paladin", "devotion": "paladin",
    "oath-of-glory": "paladin", "glory": "paladin",
    "oath-of-the-ancients": "paladin", "ancients": "paladin",
    "oath-of-vengeance": "paladin", "vengeance": "paladin",
    # Ranger
    "beast-master": "ranger", "beastmaster": "ranger",
    "fey-wanderer": "ranger",
    "gloom-stalker": "ranger",
    "hunter": "ranger",
    # Rogue
    "arcane-trickster": "rogue",
    "assassin": "rogue",
    "soulknife": "rogue", "soul-knife": "rogue",
    "thief": "rogue",
    # Sorcerer
    "aberrant-sorcery": "sorcerer", "aberrant-mind": "sorcerer",
    "clockwork-sorcery": "sorcerer", "clockwork-soul": "sorcerer",
    "draconic-sorcery": "sorcerer", "draconic-bloodline": "sorcerer",
    "wild-magic-sorcery": "sorcerer", "wild-magic": "sorcerer",
    # Warlock
    "archfey-patron": "warlock", "archfey": "warlock", "the-archfey": "warlock",
    "celestial-patron": "warlock", "celestial": "warlock", "the-celestial": "warlock",
    "fiend-patron": "warlock", "fiend": "warlock", "the-fiend": "warlock",
    "great-old-one-patron": "warlock", "great-old-one": "warlock", "the-great-old-one": "warlock",
    # Wizard
    "abjurer": "wizard", "school-of-abjuration": "wizard",
    "diviner": "wizard", "school-of-divination": "wizard",
    "evoker": "wizard", "school-of-evocation": "wizard",
    "illusionist": "wizard", "school-of-illusion": "wizard",
}

STANDARD_LANGUAGES = [
    "Common", "Common Sign Language", "Draconic", "Dwarvish", "Elvish",
    "Giant", "Gnomish", "Goblin", "Halfling", "Orc",
]


# 2024 Basic Rules mechanical metadata used by the Character Builder's gear step.
# These are compact facts, not copied descriptive rules text. Package A is used
# as the automatic starting-equipment package when the cached Open5e class or
# background does not expose structured starting-equipment data.
CLASS_GEAR_RULES: dict[str, dict] = {
    "barbarian": {"armor": ["light", "medium", "shield"], "weapons": ["simple", "martial"], "equipment": ["Greataxe", "Handaxe", "Explorer's Pack"], "gp": 15},
    "bard": {"armor": ["light"], "weapons": ["simple"], "equipment": ["Leather Armor", "Dagger", "Entertainer's Pack"], "gp": 19},
    "cleric": {"armor": ["light", "medium", "shield"], "weapons": ["simple"], "equipment": ["Chain Shirt", "Shield", "Mace", "Holy Symbol", "Priest's Pack"], "gp": 7},
    "druid": {"armor": ["light", "shield"], "weapons": ["simple"], "equipment": ["Leather Armor", "Shield", "Sickle", "Quarterstaff", "Explorer's Pack", "Herbalism Kit"], "gp": 9},
    "fighter": {"armor": ["light", "medium", "heavy", "shield"], "weapons": ["simple", "martial"], "equipment": ["Chain Mail", "Greatsword", "Flail", "Javelin", "Dungeoneer's Pack"], "gp": 4},
    "monk": {"armor": [], "weapons": ["simple", "martial-light"], "equipment": ["Spear", "Dagger", "Explorer's Pack"], "gp": 11},
    "paladin": {"armor": ["light", "medium", "heavy", "shield"], "weapons": ["simple", "martial"], "equipment": ["Chain Mail", "Shield", "Longsword", "Javelin", "Holy Symbol", "Priest's Pack"], "gp": 9},
    "ranger": {"armor": ["light", "medium", "shield"], "weapons": ["simple", "martial"], "equipment": ["Studded Leather Armor", "Scimitar", "Shortsword", "Longbow", "Arrow", "Quiver", "Explorer's Pack"], "gp": 7},
    "rogue": {"armor": ["light"], "weapons": ["simple", "martial-finesse-light"], "equipment": ["Leather Armor", "Dagger", "Shortsword", "Shortbow", "Arrow", "Quiver", "Thieves' Tools", "Burglar's Pack"], "gp": 8},
    "sorcerer": {"armor": [], "weapons": ["simple"], "equipment": ["Spear", "Dagger", "Arcane Focus", "Dungeoneer's Pack"], "gp": 28},
    "warlock": {"armor": ["light"], "weapons": ["simple"], "equipment": ["Leather Armor", "Sickle", "Dagger", "Arcane Focus", "Book", "Scholar's Pack"], "gp": 15},
    "wizard": {"armor": [], "weapons": ["simple"], "equipment": ["Dagger", "Quarterstaff", "Robe", "Spellbook", "Scholar's Pack"], "gp": 5},
}

BACKGROUND_GEAR_RULES: dict[str, dict] = {
    "acolyte": {"equipment": ["Calligrapher's Supplies", "Book", "Holy Symbol", "Parchment", "Robe"], "gp": 8},
    "criminal": {"equipment": ["Dagger", "Thieves' Tools", "Crowbar", "Pouch", "Traveler's Clothes"], "gp": 16},
    "sage": {"equipment": ["Quarterstaff", "Calligrapher's Supplies", "Book", "Parchment", "Robe"], "gp": 8},
    "soldier": {"equipment": ["Spear", "Shortbow", "Arrow", "Gaming Set", "Healer's Kit", "Quiver", "Traveler's Clothes"], "gp": 14},
}

def class_gear_rule(name_or_key: str | None) -> dict:
    return CLASS_GEAR_RULES.get(canonical_rule_key(name_or_key), {})

def background_gear_rule(name_or_key: str | None) -> dict:
    return BACKGROUND_GEAR_RULES.get(canonical_rule_key(name_or_key), {})


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

# Spell-selection limits for the 2024 character builder. Prepared-spell values
# follow the class feature tables; cantrip counts are creation/progression limits.
_FULL_PREPARED = [0,4,5,6,7,9,10,11,12,14,15,16,16,17,17,18,18,19,20,21,22]
_HALF_PREPARED = [0,2,3,4,5,6,6,7,7,9,9,10,10,11,11,12,12,14,14,15,15]
SORCERER_PREPARED = [0,2,4,6,7,9,10,11,12,14,15,16,16,17,17,18,18,19,20,21,22]
WARLOCK_PREPARED = [0,2,3,4,5,6,7,8,9,10,10,11,11,12,12,13,13,14,14,15,15]


# Spell-slot totals for the 2024 single-class character sheet. Full casters use
# the standard 1-20 progression. Paladin/Ranger use an effective caster level
# of ceil(class level / 2). Warlock uses Pact Magic slots, which are all the
# same level and refresh on a Short or Long Rest.
_FULL_SPELL_SLOTS = {
    1:(2,0,0,0,0,0,0,0,0), 2:(3,0,0,0,0,0,0,0,0), 3:(4,2,0,0,0,0,0,0,0),
    4:(4,3,0,0,0,0,0,0,0), 5:(4,3,2,0,0,0,0,0,0), 6:(4,3,3,0,0,0,0,0,0),
    7:(4,3,3,1,0,0,0,0,0), 8:(4,3,3,2,0,0,0,0,0), 9:(4,3,3,3,1,0,0,0,0),
    10:(4,3,3,3,2,0,0,0,0), 11:(4,3,3,3,2,1,0,0,0), 12:(4,3,3,3,2,1,0,0,0),
    13:(4,3,3,3,2,1,1,0,0), 14:(4,3,3,3,2,1,1,0,0), 15:(4,3,3,3,2,1,1,1,0),
    16:(4,3,3,3,2,1,1,1,0), 17:(4,3,3,3,2,1,1,1,1), 18:(4,3,3,3,3,1,1,1,1),
    19:(4,3,3,3,3,2,1,1,1), 20:(4,3,3,3,3,2,2,1,1),
}
_WARLOCK_PACT_SLOTS = {
    1:(1,1), 2:(2,1), 3:(2,2), 4:(2,2), 5:(2,3), 6:(2,3), 7:(2,4), 8:(2,4),
    9:(2,5), 10:(2,5), 11:(3,5), 12:(3,5), 13:(3,5), 14:(3,5), 15:(3,5), 16:(3,5),
    17:(4,5), 18:(4,5), 19:(4,5), 20:(4,5),
}

def spell_slot_totals(class_name_or_key: str | None, level: int) -> dict[int, int]:
    key = canonical_rule_key(class_name_or_key)
    level = max(1, min(20, int(level or 1)))
    if key == "warlock":
        count, slot_level = _WARLOCK_PACT_SLOTS[level]
        return {slot_level: count}
    if key in {"bard", "cleric", "druid", "sorcerer", "wizard"}:
        effective = level
    elif key in {"paladin", "ranger"}:
        effective = (level + 1) // 2
    else:
        return {}
    return {index + 1: count for index, count in enumerate(_FULL_SPELL_SLOTS[effective]) if count}

def spell_selection_limits(class_name_or_key: str | None, level: int) -> dict:
    key=canonical_rule_key(class_name_or_key); level=max(1,min(20,int(level or 1)))
    if key in {"bard","cleric","druid","wizard"}: prepared=_FULL_PREPARED[level]
    elif key in {"paladin","ranger"}: prepared=_HALF_PREPARED[level]
    elif key=="sorcerer": prepared=SORCERER_PREPARED[level]
    elif key=="warlock": prepared=WARLOCK_PREPARED[level]
    else: return {"cantrips":0,"prepared":0,"known":0,"max_spell_level":0}
    cantrip_base={"bard":2,"cleric":3,"druid":2,"sorcerer":4,"warlock":2,"wizard":3}.get(key,0)
    cantrips=cantrip_base + (1 if cantrip_base and level>=4 else 0) + (1 if cantrip_base and level>=10 else 0)
    # Wizards record a spellbook separately from prepared spells. The builder's
    # chosen-spell list represents that book for Wizard characters.
    known=(6 + 2*(level-1)) if key=="wizard" else prepared
    max_spell_level=min(9,(level+1)//2) if key not in {"paladin","ranger","warlock"} else (min(5,(level+1)//2) if key in {"paladin","ranger"} else min(5,(level+1)//2))
    return {"cantrips":cantrips,"prepared":prepared,"known":known,"max_spell_level":max_spell_level}
