from pathlib import Path
from types import SimpleNamespace

from app.player_architect_routes import _auto_entries, _class_choice_notes


def entity(name="Fighter", source="5e 2024 Rules", data=None):
    return SimpleNamespace(
        name=name,
        source_display_name=source,
        source_document="srd-2024",
        game_system_name="5th Edition 2024",
        data_json=data or {},
    )


def test_2024_fighter_structured_parser_uses_authoritative_fields():
    fighter = entity(data={
        "hit_points": {
            "hit_dice": "D10",
            "hit_dice_name": "1D10 per Fighter level",
            "hit_points_at_1st_level": "10 + your Constitution modifier",
        },
        "saving_throws": [{"name": "Dexterity"}, {"name": "Strength"}],
        "features": [{
            "name": "Core Fighter Traits",
            "feature_type": "CORE_TRAITS_TABLE",
            "desc": "|||\n|---|---|\n|Primary Ability|Strength or Dexterity|\n|Saving Throw Proficiencies|Strength and Constitution|\n|Weapon Proficiencies|Simple weapons and Martial weapons|\n|Armor Training|Light, Medium, and Heavy armor and Shields|\n|Tool Proficiencies|None|\n|Skill Proficiencies|Choose 2: Acrobatics, Animal Handling, Athletics|",
        }],
    })
    rows = _auto_entries(fighter, "Class")
    triples = {(r["modifier"], r["stat"], r["source"]) for r in rows}
    assert ("1d10 /Fighter Level", "Hit Dice", "5e 2024 Rules") in triples
    assert ("+Dexterity, Strength", "Saving Throws", "5e 2024 Rules") in triples
    assert any(r["stat"] == "Weapon Proficiencies" and "Simple weapons" in r["modifier"] for r in rows)
    assert any(r["stat"] == "Armor Proficiencies" and "Heavy armor" in r["modifier"] for r in rows)
    assert not any(r["stat"] == "Tool Proficiencies" for r in rows)
    assert not any("Primary Ability" in r["note"] for r in rows)
    assert len({(r["modifier"].casefold(), r["stat"].casefold()) for r in rows}) == len(rows)


def test_2014_fighter_saving_throws_only_from_dedicated_array():
    fighter = entity(source="5e 2014 Rules", data={
        "hit_points": {"hit_dice": "D10", "hit_dice_name": "1D10 per Fighter level"},
        "saving_throws": [{"name": "Constitution"}, {"name": "Strength"}],
        "features": [{
            "name": "Proficiencies",
            "feature_type": "PROFICIENCIES",
            "desc": "**Armor:** All armor, shields\n**Weapons:** Simple weapons, martial weapons\n**Tools:** None\n**Saving Throws:** Strength, Constitution\n**Skills:** Choose two from Acrobatics, Animal Handling, Athletics",
        }],
    })
    rows = _auto_entries(fighter, "Class")
    saves = [r for r in rows if r["stat"] == "Saving Throws"]
    assert len(saves) == 1
    assert saves[0]["modifier"] == "+Constitution, Strength"
    assert not any(r["modifier"].casefold() in {"none", "0", "+0"} for r in rows)
    assert any(r["stat"] == "Weapon Proficiencies" for r in rows)
    assert any(r["stat"] == "Armor Proficiencies" for r in rows)


def test_choice_notes_still_capture_unresolved_skills():
    fighter = entity(data={"features": [{"name": "Proficiencies", "feature_type": "PROFICIENCIES", "desc": "**Skills:** Choose two from Acrobatics, Athletics, History"}]})
    notes = _class_choice_notes(fighter)
    assert any(n["stat"] == "Skill Proficiencies" and "Choose two" in n["instruction"] for n in notes)


def test_ledger_has_source_column_and_manual_button_precedes_table():
    shell = Path("app/templates/tools_player_architect.html").read_text()
    assert "<th>Source</th>" in shell
    assert shell.index("+ Manual Blueprint Entry") < shell.index('class="pa-blueprint-table-wrap"')
    assert "row.source" in shell


def test_schema_adds_blueprint_source_column():
    model = Path("app/models.py").read_text()
    db = Path("app/db.py").read_text()
    assert "source: Mapped[str | None]" in model
    assert "ALTER TABLE architect_blueprint_entries ADD COLUMN source" in db


def test_version_0335():
    assert Path("app/version.py").read_text().strip() == 'APP_VERSION = "0.33.7"'
