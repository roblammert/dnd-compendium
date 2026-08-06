from app.models import Entity
from app.services import build_weapon_card


def entity(entity_type, data, *, source="srd-2014", system="5e-2014", slug="battleaxe-2"):
    return Entity(
        public_id=f"{entity_type}-{source}", entity_type=entity_type,
        name="Battleaxe", slug=slug, canonical_key="battleaxe",
        source_kind="open5e", source_document=source,
        game_system_key=system, data_json=data,
    )


def test_item_fallback_cost_and_weight_are_rendered_in_weapon_summary_table():
    weapon = entity("weapon", {
        "damage_dice": "1d8",
        "damage_type": {"key": "slashing", "name": "Slashing"},
        "properties": [{"property": {"name": "Versatile", "desc": "Two hands."}, "detail": "1d10"}],
        "range": 0,
        "long_range": 0,
    })
    item = entity("item", {"cost": "10.00", "weight": "4.000"}, slug="battleaxe-2")
    card = build_weapon_card(weapon, fallback_item=item)
    primary = {row["label"]: row["value"] for row in card["primary_stats"]}
    summary = {row["label"]: row["value"] for row in card["summary_rows"]}
    assert primary["Damage"] == "1d8 Slashing"
    assert primary["Cost"] == "1 PP"
    assert primary["Weight"] == "4.0 lb."
    assert summary["Cost"] == "1 PP"
    assert summary["Weight"] == "4.0 lb."
