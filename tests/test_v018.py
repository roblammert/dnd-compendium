from types import SimpleNamespace

from app.main import templates
from app.services import build_weapon_card


def weapon_entity(data):
    return SimpleNamespace(data_json=data, summary="", name="Longbow")


def test_weapon_card_normalizes_common_open5e_fields():
    card = build_weapon_card(weapon_entity({
        "category": {"name": "Martial Ranged Weapon"},
        "damage_dice": "1d8",
        "damage_type": {"name": "Piercing"},
        "range": 150,
        "long_range": 600,
        "cost": "50 gp",
        "weight": 2,
        "properties": [{"name": "Ammunition"}, {"name": "Heavy"}, {"name": "Two-Handed"}],
        "mastery": {"name": "Slow"},
        "description": "A **powerful** ranged weapon.",
    }))
    assert card["primary_stats"][0]["value"] == "1d8 Piercing"
    assert card["primary_stats"][2]["value"] == "2.0 lb."
    assert any(row["label"] == "Range" and row["value"] == "150/600 feet" for row in card["summary_rows"])
    assert [item["name"] for item in card["properties"]] == ["Ammunition", "Heavy", "Two-Handed"]
    assert card["mastery"] == "Slow"


def test_weapon_template_renders_dedicated_layout_and_markdown():
    template = templates.get_template("entity_detail.html")
    entity = SimpleNamespace(name="Longbow", entity_type="weapon", data_json={"description": "A **powerful** weapon."})
    weapon = build_weapon_card(weapon_entity({"damage_dice": "1d8", "damage_type": "piercing", "description": "A **powerful** weapon."}))
    html = template.render(
        entity=entity, variants=[], return_to="/compendium", primary_asset=None,
        descriptor_badges=[], monster=None, magic_item=None, species=None, item_card=None,
        weapon=weapon, shared_assets=[],
    )
    assert 'class="compendium-stat-card weapon-stat-card"' in html
    assert "Weapon statistics" in html
    assert "1d8 Piercing" in html
    assert "<strong>powerful</strong>" in html
