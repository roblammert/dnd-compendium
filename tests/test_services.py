from app.services import canonical_checksum, slugify

def test_slugify(): assert slugify("Ancient Red Dragon!")=="ancient-red-dragon"
def test_checksum_is_stable(): assert canonical_checksum({"b":2,"a":1})==canonical_checksum({"a":1,"b":2})

from types import SimpleNamespace
from app.services import build_monster_card


def _monster(data):
    return SimpleNamespace(data_json=data, summary=None)


def test_monster_abilities_from_nested_mapping():
    card = build_monster_card(_monster({
        "abilities": {
            "strength": 8, "dexterity": 14, "constitution": 12,
            "intelligence": 10, "wisdom": 9, "charisma": 7,
        }
    }))
    assert [(a["score"], a["modifier"]) for a in card["abilities"]] == [
        (8, "-1"), (14, "+2"), (12, "+1"), (10, "+0"), (9, "-1"), (7, "-2")
    ]


def test_monster_abilities_from_open5e_list_shape():
    card = build_monster_card(_monster({
        "ability_scores": [
            {"ability": {"key": "str"}, "score": 13},
            {"ability": {"key": "dex"}, "value": 18},
            {"ability": {"key": "con"}, "score": 14},
            {"ability": {"key": "int"}, "score": 10},
            {"ability": {"key": "wis"}, "score": 7},
            {"ability": {"key": "cha"}, "score": 11},
        ]
    }))
    assert [a["score"] for a in card["abilities"]] == [13, 18, 14, 10, 7, 11]


def test_monster_open5e_reference_fields_speed_saves_and_languages():
    card = build_monster_card(_monster({
        "size": {"name": "Small", "key": "small"},
        "type": {"name": "Humanoid", "key": "humanoid"},
        "alignment": "chaotic evil",
        "speed": {"walk": 30, "unit": "feet"},
        "strength": 8, "dexterity": 18, "constitution": 10,
        "intelligence": 10, "wisdom": 8, "charisma": 8,
        "saving_throws": {
            "strength": -1, "dexterity": 4, "constitution": 0,
            "intelligence": 0, "wisdom": -1, "charisma": -1,
        },
        "languages": {
            "as_string": "Common,Goblin",
            "data": [
                {"name": "Common", "key": "common", "desc": "Typical speakers are Humans"},
                {"name": "Goblin", "key": "goblin", "desc": "Typical speakers are goblinoids."},
            ],
        },
    }))
    assert [badge["value"] for badge in card["identity_badges"]] == ["Small", "Humanoid", "Chaotic Evil"]
    assert card["speed"] == "Walk 30 feet"
    assert [save["modifier"] for save in card["saving_throw_modifiers"]] == ["-1", "+4", "+0", "+0", "-1", "-1"]
    assert card["languages"] == [
        {"name": "Common", "description": "Typical speakers are Humans."},
        {"name": "Goblin", "description": "Typical speakers are goblinoids."},
    ]


def test_monster_nested_speed_measurement():
    card = build_monster_card(_monster({"speed": {"walk": {"value": 30, "unit": "feet"}}}))
    assert card["speed"] == "Walk 30 feet"


def test_skill_bonus_normalization():
    card = build_monster_card(_monster({
        "skills": {
            "stealth": 6,
            "animal_handling": {"bonus": 2},
        }
    }))
    assert card["skill_bonuses"] == [
        {"name": "Animal Handling", "modifier": "+2"},
        {"name": "Stealth", "modifier": "+6"},
    ]

def test_alignment_badge_is_title_case_and_semantic():
    card = build_monster_card(_monster({"alignment": "chaotic evil"}))
    badge = next(item for item in card["identity_badges"] if item["kind"] == "alignment")
    assert badge["value"] == "Chaotic Evil"
    assert "--badge-h:4" in badge["style"]


def test_monster_summary_stats_and_resistances():
    card = build_monster_card(_monster({
        "hit_points": 45,
        "armor_class": 15,
        "xp": 1100,
        "initiative_bonus": 3,
        "proficiency_bonus": 2,
        "passive_perception": 13,
        "type": {"name": "Fiend"},
        "size": {"name": "Large"},
        "alignment": "lawful evil",
        "damage_resistances": [{"name": "Cold"}, {"name": "Fire"}],
        "damage_immunities": "Poison",
        "condition_immunities": {"data": [{"name": "Poisoned"}]},
    }))
    assert card["hit_points"] == "45"
    assert card["xp"] == "1100"
    assert card["initiative_bonus"] == "+3"
    assert card["proficiency_bonus"] == "+2"
    assert card["passive_perception"] == "13"
    assert card["creature_type"] == "Fiend"
    assert card["resistance_rows"] == [
        {"category": "Damage Resistances", "items": ["Cold", "Fire"]},
        {"category": "Damage Immunities", "items": ["Poison"]},
        {"category": "Condition Immunities", "items": ["Poisoned"]},
    ]


def test_hit_dice_is_not_exposed_in_monster_card():
    card = build_monster_card(_monster({"hit_points": 12, "hit_dice": "2d6+4"}))
    assert "hit_dice" not in card


def test_combined_resistances_and_immunities_structure():
    card = build_monster_card(_monster({
        "resistances_and_immunities": {
            "damage_resistances": [{"name": "Cold"}, {"name": "Fire"}],
            "damage_immunities": [{"name": "Poison"}],
            "condition_immunities": {"data": [{"name": "Charmed"}]},
        }
    }))
    assert card["resistance_rows"] == [
        {"category": "Damage Resistances", "items": ["Cold", "Fire"]},
        {"category": "Damage Immunities", "items": ["Poison"]},
        {"category": "Condition Immunities", "items": ["Charmed"]},
    ]


def test_combined_defense_list_with_category_rows():
    card = build_monster_card(_monster({
        "resistances_and_immunities": [
            {"type": "resistance", "values": [{"name": "Necrotic"}]},
            {"type": "damage immunity", "damage_type": {"name": "Poison"}},
            {"type": "condition immunity", "condition": {"name": "Prone"}},
        ]
    }))
    assert card["resistance_rows"] == [
        {"category": "Damage Resistances", "items": ["Necrotic"]},
        {"category": "Damage Immunities", "items": ["Poison"]},
        {"category": "Condition Immunities", "items": ["Prone"]},
    ]


def test_entity_detail_template_renders_resistance_rows():
    """Regression: Jinja must not resolve row.items as dict.items()."""
    from pathlib import Path
    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).parents[1] / "app" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    from app.main import _render_markdown
    env.filters["render_markdown"] = _render_markdown
    template = env.get_template("entity_detail.html")
    entity = SimpleNamespace(
        id=1,
        public_id="ent-test",
        entity_type="monster",
        name="Darakhul",
        data_json={"name": "Darakhul"},
    )
    monster = build_monster_card(_monster({
        "name": "Darakhul",
        "damage_resistances": ["Necrotic"],
        "damage_immunities": ["Poison"],
    }))
    html = template.render(
        entity=entity,
        monster=monster,
        variants=[entity],
        primary_asset=None,
        descriptor_badges=[],
        return_to="/compendium?page=21",
    )
    assert "Resistances and Immunities" in html
    assert "Damage Resistances" in html
    assert "Necrotic" in html
    assert "Damage Immunities" in html
    assert "Poison" in html
