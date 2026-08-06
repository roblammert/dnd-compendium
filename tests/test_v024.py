from types import SimpleNamespace

from app.services import (
    build_language_card,
    build_service_card,
    build_size_card,
    build_skill_card,
    build_spell_card,
    build_spell_school_card,
    build_weapon_property_card,
)


def entity(entity_type, name, data):
    return SimpleNamespace(entity_type=entity_type, name=name, data_json=data, summary="")


def test_spell_card_normalizes_school_and_core_metadata():
    card = build_spell_card(entity("spell", "Fire Bolt", {
        "level": 0,
        "school": {"key": "evocation", "name": "Evocation"},
        "casting_time": "1 action",
        "range": 120,
        "components": {"verbal": True, "somatic": True},
        "duration": "Instantaneous",
        "desc": "A mote of fire streaks toward a creature.",
    }))
    assert card["summary_rows"][0]["value"]["url"] == "/compendium/spellschool/evocation"
    assert any(row["label"] == "Level" and row["value"] == "Cantrip" for row in card["summary_rows"])
    assert any(row["label"] == "Components" and row["value"] == "V, S" for row in card["summary_rows"])


def test_reference_cards_have_tailored_metadata():
    assert build_spell_school_card(entity("spellschool", "Abjuration", {"key": "abjuration", "desc": "Protective magic."}))["accent"] == "spell-school"
    prop = build_weapon_property_card(entity("weaponpropertie", "Thrown", {"range": 20, "long_range": 60, "desc": "May be thrown."}))
    assert any(row["label"] == "Range" and row["value"] == "20/60 feet" for row in prop["summary_rows"])
    skill = build_skill_card(entity("skill", "Stealth", {"ability": {"key": "dexterity", "name": "Dexterity"}}))
    assert skill["summary_rows"][0]["value"]["text"] == "Dexterity"
    service = build_service_card(entity("service", "Coach Cab", {"cost": 0.03, "unit": "per mile"}))
    assert any(row["label"] == "Cost" and row["value"] == "3 CP" for row in service["summary_rows"])
    language = build_language_card(entity("language", "Dwarvish", {"script": "Dwarvish", "typical_speakers": ["Dwarves"]}))
    assert language["chips"] == ["Dwarves"]
    size = build_size_card(entity("size", "Large", {"space": 10, "reach": 5}))
    assert any(row["label"] == "Space" and row["value"] == "10 feet" for row in size["summary_rows"])
