from app.models import Entity
from app.services import build_weapon_card


def ent(entity_type, data, *, source_document="srd-2014", game_system_key="5e-2014"):
    return Entity(public_id=f"{entity_type}-battleaxe", entity_type=entity_type, name="Battleaxe", slug="battleaxe", canonical_key="battleaxe", source_kind="open5e", source_document=source_document, game_system_key=game_system_key, data_json=data)


def test_weapon_fallback_reads_nested_item_equipment_values():
    weapon = ent("weapon", {"damage_dice": "1d8", "cost": 0, "weight": ""})
    item = ent("item", {"equipment": {"cost": {"quantity": 10, "unit": {"name": "gp"}}, "weight": {"value": 4, "unit": "lb"}}})
    card = build_weapon_card(weapon, fallback_item=item)
    stats = {row["label"]: row["value"] for row in card["primary_stats"]}
    assert stats["Cost"] == "1 PP"
    assert stats["Weight"] == "4.0 lb."


def test_weapon_fallback_supports_full_coin_unit_names():
    weapon = ent("weapon", {"damage_dice": "1d8"})
    item = ent("item", {"item": {"cost": {"amount": 10, "unit": {"name": "Gold Pieces"}}, "weight": 4}})
    card = build_weapon_card(weapon, fallback_item=item)
    stats = {row["label"]: row["value"] for row in card["primary_stats"]}
    assert stats["Cost"] == "1 PP"
    assert stats["Weight"] == "4.0 lb."
