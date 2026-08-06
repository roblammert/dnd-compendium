from types import SimpleNamespace
import pytest

from app.services import build_remaining_reference_card


def entity(entity_type, name, data):
    return SimpleNamespace(entity_type=entity_type, name=name, data_json=data, summary="")


@pytest.mark.parametrize("entity_type,name,data,accent", [
    ("abilitie", "Strength", {"abbreviation": "STR", "desc": "Physical power."}, "ability"),
    ("alignment", "Lawful Good", {"abbreviation": "LG", "desc": "Honor and compassion."}, "alignment"),
    ("armor", "Leather", {"ac_display": "11 + Dex modifier", "category": "Light", "weight": 10}, "armor"),
    ("background", "Acolyte", {"skills": ["Insight", "Religion"], "desc": "Temple service."}, "background"),
    ("classe", "Fighter", {"hit_die": "d10", "saving_throws": ["Strength", "Constitution"]}, "class"),
    ("condition", "Blinded", {"desc": "A blinded creature cannot see."}, "condition"),
    ("creatureset", "Forest Creatures", {"creatures": ["Wolf", "Bear"]}, "creature-set"),
    ("creaturetype", "Dragon", {"desc": "Ancient reptilian creatures."}, "creature-type"),
    ("damagetype", "Fire", {"desc": "Burning heat."}, "damage-type"),
    ("document", "SRD 5.2", {"display_name": "5e 2024 Rules", "gamesystem": {"key": "5e-2024", "name": "5th Edition 2024"}}, "document"),
    ("environment", "Forest", {"terrain": ["Woodland"], "climate": ["Temperate"]}, "environment"),
    ("feat", "Alert", {"prerequisite": "Level 4", "repeatable": False}, "feat"),
    ("gamesystem", "5th Edition 2024", {"version": "2024"}, "game-system"),
    ("image", "Goblin Art", {"url": "https://example.com/goblin.jpg", "artist": "Artist"}, "image"),
    ("itemcategorie", "Adventuring Gear", {"desc": "General equipment."}, "item-category"),
    ("itemraritie", "Rare", {"rank": 3}, "item-rarity"),
    ("itemset", "Dragon Set", {"items": ["Helm", "Shield"]}, "item-set"),
    ("license", "CC-BY", {"url": "https://example.com/license", "spdx_id": "CC-BY-4.0"}, "license"),
    ("publisher", "Open Gaming", {"website": "https://example.com"}, "publisher"),
    ("rule", "Cover", {"section": "Combat", "desc": "Cover improves defense."}, "rule"),
    ("ruleset", "Core Rules", {"gamesystem": {"key": "5e-2024", "name": "5th Edition 2024"}}, "ruleset"),
])
def test_all_remaining_open5e_endpoint_types_have_tailored_cards(entity_type, name, data, accent):
    card = build_remaining_reference_card(entity(entity_type, name, data))
    assert card is not None
    assert card["accent"] == accent
    assert "summary_rows" in card
    assert "description" in card


def test_document_and_ruleset_links_use_real_endpoint_keys():
    document = build_remaining_reference_card(entity("document", "SRD", {
        "gamesystem": {"key": "5e-2024", "name": "5th Edition 2024"},
        "publisher": {"key": "wizards-of-the-coast", "name": "Wizards of the Coast"},
    }))
    rows = {row["label"]: row["value"] for row in document["summary_rows"]}
    assert rows["Game System"]["url"] == "/compendium/gamesystem/5e-2024"
    assert rows["Publisher"]["url"] == "/compendium/publisher/wizards-of-the-coast"
