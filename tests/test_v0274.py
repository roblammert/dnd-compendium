from types import SimpleNamespace

from app.main import templates
from app.services import build_weapon_card


def test_weapon_cost_has_conversion_tooltip_in_quick_stat_and_metadata_table():
    entity = SimpleNamespace(name="Battleaxe", entity_type="weapon", data_json={})
    weapon_entity = SimpleNamespace(
        name="Battleaxe",
        summary="",
        data_json={"damage_dice": "1d8", "damage_type": {"name": "Slashing"}},
    )
    item_entity = SimpleNamespace(
        name="Battleaxe",
        summary="",
        data_json={"cost": "10.00", "weight": "4.000"},
    )
    weapon = build_weapon_card(weapon_entity, fallback_item=item_entity)
    html = templates.get_template("entity_detail.html").render(
        entity=entity,
        variants=[],
        return_to="/compendium",
        primary_asset=None,
        descriptor_badges=[],
        monster=None,
        magic_item=None,
        species=None,
        item_card=None,
        weapon=weapon,
        reference_card=None,
        shared_assets=[],
        current_user=None,
    )

    tooltip = "1 PP\n10 GP\n100 SP\n1,000 CP"
    # The formatted Cost appears once in the quick-stat band and once in the
    # structured metadata table; both should expose the conversion tooltip.
    assert html.count(f'title="{tooltip}"') == 2
    assert html.count(">1 PP<") >= 2
