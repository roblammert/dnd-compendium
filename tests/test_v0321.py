from pathlib import Path

from app.character_services import class_features_for_level, entity_print_profile, equipment_print_rows
from app.models import Entity


def _entity(entity_type, name, key, data, summary=None):
    return Entity(
        public_id=f"ent_{key}", entity_type=entity_type, name=name, slug=key,
        canonical_key=key, source_kind="open5e", source_document="srd-2024",
        source_display_name="5e 2024 Rules", game_system_key="5e-2024",
        game_system_name="5th Edition 2024", data_json=data, summary=summary,
    )


def test_v0321_species_print_profile_uses_cached_traits_when_summary_missing():
    dwarf = _entity("species", "Dwarf", "dwarf", {
        "traits": [
            {"name": "Darkvision", "desc": "You can see in dim light."},
            {"name": "Dwarven Resilience", "desc": "You have unusual resilience."},
        ]
    })
    profile = entity_print_profile(dwarf, "species")
    assert "Dwarves are sturdy" in profile
    assert "Darkvision" in profile
    assert "Dwarven Resilience" in profile


def test_v0321_class_print_profile_uses_core_traits():
    cleric = _entity("class", "Cleric", "cleric", {
        "core_traits": {
            "primary_ability": "Wisdom",
            "hit_point_die": "D8 per Cleric level",
            "saving_throw_proficiencies": "Wisdom and Charisma",
            "armor_training": "Light and Medium armor and Shields",
        }
    })
    profile = entity_print_profile(cleric, "class")
    assert "divine spellcaster" in profile
    assert "Primary Ability" in profile and "Wisdom" in profile
    assert "Armor Training" in profile


def test_v0321_class_features_remove_column_data_and_structural_rows():
    cleric = _entity("class", "Cleric", "cleric", {
        "features": [
            {"name": "Cantrips", "desc": "[Column data]"},
            {"name": "1st", "desc": "[Column data]"},
            {"name": "Proficiency Bonus", "desc": "[Column data]"},
            {"name": "Channel Divinity", "desc": "You can channel divine energy."},
            {"name": "Cleric Spell List", "desc": "A giant class spell appendix."},
        ]
    })
    features = class_features_for_level(cleric, 5)
    names = [row["name"] for row in features]
    assert names == ["Channel Divinity"]
    assert all("Column data" not in row["description"] for row in features)


def test_v0321_equipment_pairs_into_four_print_columns():
    items = [_entity("item", f"Item {i}", f"item-{i}", {}) for i in range(15)]
    rows = equipment_print_rows(items)
    assert len(rows) == 8
    assert rows[0]["left"].name == "Item 0"
    assert rows[0]["right"].name == "Item 8"
    assert rows[-1]["right"] is None


def test_v0321_print_template_has_safe_paged_footer_and_feature_break():
    template = Path("app/templates/character_print.html").read_text()
    assert '@bottom-left' in template and '@bottom-right' in template
    assert 'counter(page) "/" counter(pages)' in template
    assert 'string(playername)' in template
    assert 'features-section { break-before:page' in template
    assert 'inventory-table compact-four' in template
    assert 'derived.print_profiles.species' in template
    assert 'derived.print_profiles.class' in template
    assert '<footer class="print-footer">' not in template
