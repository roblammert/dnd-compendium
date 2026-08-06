from app.main import _select_item_fallback
from app.models import Entity


def ent(entity_type, source, system, data=None):
    return Entity(public_id=f"{entity_type}-{source}", entity_type=entity_type, name="Battleaxe", slug="battleaxe", canonical_key="battleaxe", source_kind="open5e", source_document=source, game_system_key=system, data_json=data or {})


def test_single_item_variant_is_reused_for_all_weapon_variants():
    item = ent("item", "srd-2014", "5e-2014", {"cost": 10, "weight": 4})
    weapon_2014 = ent("weapon", "srd-2014", "5e-2014")
    weapon_2024 = ent("weapon", "srd-2024", "5e-2024")
    assert _select_item_fallback(weapon_2014, [item]) is item
    assert _select_item_fallback(weapon_2024, [item]) is item


def test_multiple_item_variants_match_weapon_source_first():
    item_2014 = ent("item", "srd-2014", "5e-2014")
    item_2024 = ent("item", "srd-2024", "5e-2024")
    weapon = ent("weapon", "srd-2024", "5e-2024")
    assert _select_item_fallback(weapon, [item_2014, item_2024]) is item_2024


def test_nested_document_metadata_is_used_when_columns_are_blank():
    item = ent("item", "", "", {"document": {"key": "srd-2024", "gamesystem": {"key": "5e-2024"}}})
    weapon = ent("weapon", "", "", {"document": {"key": "srd-2024", "gamesystem": {"key": "5e-2024"}}})
    other = ent("item", "srd-2014", "5e-2014")
    assert _select_item_fallback(weapon, [other, item]) is item
