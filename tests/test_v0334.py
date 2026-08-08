from pathlib import Path
from types import SimpleNamespace

from app.player_architect_routes import _auto_entries, _class_choice_notes, _class_rule_pairs


def _entity(desc: str, feature_type: str = "PROFICIENCIES"):
    return SimpleNamespace(name="Monk", data_json={"features": [{"name": "Proficiencies", "feature_type": feature_type, "desc": desc}]})


def test_2014_monk_proficiencies_become_blueprint_and_choices():
    monk = _entity("**Armor:** None\n**Weapons:** Simple weapons, shortswords\n**Tools:** Choose one type of artisan's tools or one musical instrument\n**Saving Throws:** Strength, Dexterity\n**Skills:** Choose two from Acrobatics, Athletics, History, Insight, Religion, and Stealth")
    pairs = dict(_class_rule_pairs(monk))
    assert pairs["Weapons"] == "Simple weapons, shortswords"
    assert pairs["Armor"] == "None"
    entries = _auto_entries(monk, "Class")
    assert any(row["stat"] == "Weapons" and "Simple weapons" in row["modifier"] for row in entries)
    assert any(row["stat"] == "Saving Throws" and "Strength" in row["modifier"] for row in entries)
    notes = _class_choice_notes(monk)
    assert any(row["stat"] == "Tools" and "Choose one" in row["instruction"] for row in notes)
    assert any(row["stat"] == "Skills" and "Choose two" in row["instruction"] for row in notes)


def test_2024_core_traits_table_is_parsed_without_guessing_choices():
    monk = _entity("|||\n|---|---|\n|Primary Ability|Dexterity and Wisdom|\n|Hit Point Die|D8 per Monk level|\n|Saving Throw Proficiencies|Strength and Dexterity|\n|Skill Proficiencies|Choose 2: Acrobatics, Athletics, History, Insight, Religion, or Stealth|\n|Weapon Proficiencies|Simple weapons and Martial weapons that have the Light property|\n|Tool Proficiencies|Choose one type of Artisan's Tools or Musical Instrument|\n|Armor Training|None|\n|Starting Equipment|Choose A or B: (A) Spear, Explorer's Pack; or (B) 50 GP|", "CORE_TRAITS_TABLE")
    entries = _auto_entries(monk, "Class")
    assert any(row["stat"] == "Weapons" and "Martial weapons" in row["modifier"] for row in entries)
    assert any(row["stat"] == "Armor" and row["modifier"] == "None" for row in entries)
    notes = _class_choice_notes(monk)
    assert {row["stat"] for row in notes} >= {"Skills", "Tools", "Other"}


def test_blueprint_drawer_has_player_decision_section_and_extended_stats():
    shell = Path("app/templates/tools_player_architect.html").read_text()
    routes = Path("app/player_architect_routes.py").read_text()
    assert "Needs Your Choice" in shell
    assert "Player Decisions" in shell
    for stat in ["Weapons", "Armor", "Tools", "Saving Throws", "Skills", "Cantrips", "Spells", "Feats"]:
        assert f'"{stat}"' in routes
    assert '_class_choice_notes(cls, "Class") + _class_choice_notes(sub, "Subclass")' in routes


def test_version_0334():
    assert Path("app/version.py").read_text().strip() == 'APP_VERSION = "0.33.4"'
