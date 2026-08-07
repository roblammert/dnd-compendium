from types import SimpleNamespace

from app.models import Entity
from app.tools_routes import _build_item_index, _loot_row, templates


def _entity(**kwargs):
    defaults = dict(
        id=1,
        public_id="ent_weapon",
        entity_type="weapon",
        name="Battleaxe",
        slug="battleaxe-2",
        canonical_key="battleaxe",
        source_document="srd-2014",
        source_display_name="5e 2014 Rules",
        game_system_key="5e-2014",
        game_system_name="5th Edition 2014",
        is_active=True,
        summary=None,
        data_json={},
    )
    defaults.update(kwargs)
    return Entity(**defaults)


def test_loot_weapon_uses_matching_item_cost_weight_and_tooltip():
    weapon = _entity(data_json={
        "name": "Battleaxe",
        "damage_dice": "1d8",
        "damage_type": {"name": "Slashing", "key": "slashing"},
        "document": {"key": "srd-2014", "gamesystem": {"key": "5e-2014"}},
    })
    item = _entity(
        id=2,
        public_id="ent_item",
        entity_type="item",
        slug="battleaxe-2",
        data_json={
            "name": "Battleaxe",
            "cost": "10.00",
            "weight": "4.000",
            "document": {"key": "srd-2014", "gamesystem": {"key": "5e-2014"}},
        },
    )
    row = _loot_row(
        weapon,
        item_index=_build_item_index([item]),
        lexicon={"weapon": "Arms & Weapons"},
    )
    assert row["cost"] == "1 PP"
    assert row["cost_gp"] == 10.0
    assert row["weight"] == "4.0 lb."
    assert "10 GP" in row["cost_tooltip"]
    assert row["type"] == "Arms & Weapons"


def test_loot_template_disables_rarities_and_preserves_options():
    params = {
        "count_min": 4,
        "count_max": 7,
        "max_value_gp": 40,
        "max_total_value_gp": 600,
        "include_equipment": False,
        "include_items": True,
        "include_magicitems": False,
        "include_weapons": True,
        "rarity": ["Rare"],
    }
    html = templates.get_template("tools_loot_generator.html").render(
        tools_section="loot-generator", rows=[], params=params, total_value_gp=0
    )
    assert 'id="rarityFieldset" disabled' in html
    assert 'name="include_magicitems" value="1" checked' not in html
    assert 'name="include_items" value="1" checked' in html
    assert 'name="include_equipment" value="1" checked' not in html
    assert 'name="include_pp"' not in html
    assert 'name="include_gp"' not in html
    assert 'name="max_total_value_gp"' in html
    assert 'value="40"' in html and 'value="600"' in html
