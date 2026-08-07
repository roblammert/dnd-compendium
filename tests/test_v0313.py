from pathlib import Path
from types import SimpleNamespace

from app.character_services import builder_summary, subclass_parent_key, background_allowed_abilities


def fake_entity(**kwargs):
    base = dict(name="Dwarf", canonical_key="dwarf", slug="dwarf", entity_type="species", data_json={}, summary="", source_document="srd-2024", game_system_key="5e-2024")
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_species_fallback_summary_is_human_readable():
    text = builder_summary(fake_entity(), "species")
    assert "Dwarves" in text
    assert len(text) > 60


def test_subclass_parent_fallback_detects_core_subclass():
    row = fake_entity(name="Champion", canonical_key="champion", slug="champion", entity_type="subclass")
    assert subclass_parent_key(row) == "fighter"


def test_legacy_background_allows_any_ability_for_2024_conversion():
    row = fake_entity(name="Folk Hero", canonical_key="folk-hero", slug="folk-hero", entity_type="background", source_document="legacy")
    assert set(background_allowed_abilities(row)) == {"str", "dex", "con", "int", "wis", "cha"}


def test_builder_templates_include_requested_interactions():
    root = Path("app/templates/character_steps")
    assert "More Info" in (root / "species.html").read_text()
    assert "data-subclass-parent" in (root / "class.html").read_text()
    assert "data-generate-abilities" in (root / "abilities.html").read_text()
    bg = (root / "background.html").read_text()
    assert "data-background-select" in bg
    assert 'name="languages"' in bg
