from pathlib import Path
from types import SimpleNamespace

from app.character_services import primary_class_key, split_class_catalog, subclass_parent_key


def entity(name, key, entity_type="class", public_id=None):
    return SimpleNamespace(
        public_id=public_id or f"ent_{key}",
        name=name,
        canonical_key=key,
        slug=key,
        entity_type=entity_type,
        data_json={},
        source_document="srd-2024",
        game_system_key="5e-2024",
    )


def test_subclass_names_are_not_primary_classes():
    rows = [
        entity("Bard", "bard"),
        entity("College of Lore", "college-of-lore"),
        entity("Druid", "druid"),
        entity("Circle of the Land", "circle-of-the-land"),
        entity("Warlock", "warlock"),
    ]
    primary, subclasses, parents = split_class_catalog(rows)
    assert [row.name for row in primary] == ["Bard", "Druid", "Warlock"]
    assert {row.name for row in subclasses} == {"College of Lore", "Circle of the Land"}
    assert parents["ent_college-of-lore"] == "bard"
    assert parents["ent_circle-of-the-land"] == "druid"


def test_warlock_is_not_mistaken_for_war_domain():
    row = entity("Warlock", "warlock")
    assert primary_class_key(row) == "warlock"
    assert subclass_parent_key(row) is None


def test_extended_2024_subclass_parent_examples():
    examples = {
        "path-of-the-world-tree": "barbarian",
        "college-of-dance": "bard",
        "war-domain": "cleric",
        "circle-of-the-sea": "druid",
        "eldritch-knight": "fighter",
        "warrior-of-the-elements": "monk",
        "oath-of-the-ancients": "paladin",
        "gloom-stalker": "ranger",
        "soulknife": "rogue",
        "clockwork-sorcery": "sorcerer",
        "great-old-one-patron": "warlock",
        "illusionist": "wizard",
    }
    for key, parent in examples.items():
        assert subclass_parent_key(entity(key.replace("-", " ").title(), key)) == parent


def test_background_context_does_not_shadow_template_helper():
    routes = Path("app/character_routes.py").read_text()
    assert 'context["selected_background_allowed_abilities"]' in routes
    assert 'context["background_allowed_abilities"] =' not in routes
    background = Path("app/templates/character_steps/background.html").read_text()
    assert "background_allowed_abilities(entity)" in background


def test_character_reference_modal_strips_full_card_actions():
    js = Path("app/static/js/app.js").read_text()
    for selector in (
        ".raw-json-panel",
        ".entity-user-actions",
        ".asset-tools",
        ".shared-assets-panel",
        "#add-to-list-dialog",
        "[data-open-list-dialog]",
    ):
        assert selector in js
