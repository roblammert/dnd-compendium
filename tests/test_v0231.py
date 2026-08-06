from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from app.models import Entity
from app.services import build_weapon_card


def weapon(data):
    return Entity(
        public_id="ent_v231",
        entity_type="weapon",
        name="Battleaxe",
        slug="battleaxe",
        canonical_key="battleaxe",
        source_kind="open5e",
        data_json=data,
    )


def test_weapon_summary_links_render_as_anchors():
    card = build_weapon_card(
        weapon(
            {
                "damage_dice": "1d8",
                "damage_type": {"key": "slashing", "name": "Slashing"},
                "properties": [
                    {
                        "detail": "1d10",
                        "property": {
                            "name": "Versatile",
                            "desc": "This weapon can be used with one or two hands.",
                        },
                    }
                ],
            }
        )
    )
    row = next(r for r in card["summary_rows"] if r["label"] == "Damage Type")
    assert row["value"]["text"] == "Slashing"
    assert row["value"]["url"] == "/compendium/damagetype/slashing"

    template_source = Path("app/templates/entity_detail.html").read_text()
    assert "row.value is mapping and row.value.url" in template_source
    assert 'href="{{ row.value.url }}"' in template_source


def test_missing_cost_and_weight_do_not_create_empty_bands():
    card = build_weapon_card(weapon({"damage_dice": "1d8"}))
    assert [row["label"] for row in card["primary_stats"]] == ["Damage"]
