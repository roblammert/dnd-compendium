from pathlib import Path

from app.character_services import feat_print_profile, hit_dice_print_guide, roll_reference_rows, species_hp_per_level_bonus
from app.models import Character, Entity


def _entity(entity_type, name, key, data, summary=None):
    return Entity(
        public_id=f"ent_{key}", entity_type=entity_type, name=name, slug=key,
        canonical_key=key, source_kind="open5e", source_document="srd-2024",
        source_display_name="5e 2024 Rules", game_system_key="5e-2024",
        game_system_name="5th Edition 2024", data_json=data, summary=summary,
    )


def test_v0322_feat_print_profile_uses_structured_benefits():
    feat = _entity("feat", "Alert", "alert", {
        "desc": "You gain the following benefits.",
        "benefits": [
            {"name": "Initiative Proficiency", "desc": "Add your Proficiency Bonus to Initiative rolls."},
            {"name": "Initiative Swap", "desc": "You can swap Initiative with a willing ally."},
        ],
    })
    profile = feat_print_profile(feat)
    assert "Initiative Proficiency" in profile
    assert "Initiative Swap" in profile
    assert "You gain the following benefits" in profile


def test_v0322_dwarf_hp_bonus_and_hit_dice_guide_are_character_specific():
    dwarf = _entity("species", "Dwarf", "dwarf", {
        "traits": [{"name": "Dwarven Toughness", "desc": "Your Hit Point maximum increases by 1, and it increases by 1 again whenever you gain a level."}]
    })
    cleric = _entity("class", "Cleric", "cleric", {})
    char = Character(public_id="chr_test", user_id=1, name="Test", level=5, ability_scores={})
    assert species_hp_per_level_bonus(dwarf) == 1
    guide = hit_dice_print_guide(char, cleric, dwarf, 8, 2)
    assert guide["title"] == "5d8"
    assert "1d8 +2" in guide["short_rest"]
    assert "all spent Hit Point Dice" in guide["long_rest"]
    assert "8 HP" in guide["level_up"]


def test_v0322_roll_reference_uses_actual_modifiers_and_proficiency():
    skills = [
        {"name": "Athletics", "ability": "str", "modifier": 4, "proficient": True},
        {"name": "Perception", "ability": "wis", "modifier": 3, "proficient": True},
    ]
    saves = [
        {"ability": a, "modifier": (3 if a == "wis" else 0), "proficient": a == "wis"}
        for a in ("str", "dex", "con", "int", "wis", "cha")
    ]
    rows = roll_reference_rows(skills, saves, {"str":1,"dex":0,"con":2,"int":-1,"wis":0,"cha":3})
    wis = next(row for row in rows if row["ability"] == "WIS")
    assert "d20 +3" in wis["save"]
    assert "Perception +3" in wis["examples"]


def test_v0322_print_template_footer_guides_and_currency():
    template = Path("app/templates/character_print.html").read_text()
    assert "width:3.87in" in template
    assert "Hit Dice &amp; How to Use Them" in template
    assert "How Do I Roll..." in template
    assert "derived.feat_print_profiles" in template
    assert "['cp','sp','gp','pp']" in template
    assert "Species, background, class, and subclass information from the cached compendium record." not in template


def test_v0322_print_timestamp_is_central_time():
    routes = Path("app/character_routes.py").read_text()
    assert 'ZoneInfo("America/Chicago")' in routes
    assert 'strftime("%Y%m%d %H:%M")' in routes
