
from types import SimpleNamespace
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.main import _render_markdown
from app.services import build_magic_item_card, build_species_card


def entity(kind, data):
    return SimpleNamespace(entity_type=kind, data_json=data, summary=None)


def test_magic_item_card_normalizes_core_metadata():
    card=build_magic_item_card(entity("magicitem", {
        "rarity":{"name":"Very Rare"}, "type":{"name":"Wondrous Item"},
        "requires_attunement":True, "weight":2, "charges":7,
        "description":"A remarkable relic.",
        "properties":[{"name":"Flame","desc":"It sheds bright light."}],
    }))
    assert card["rarity"] == "Very Rare"
    assert card["item_type"] == "Wondrous Item"
    assert card["attunement"] == "Required"
    assert card["weight"] == "2.0 lb."
    assert card["charges"] == "7"
    assert card["properties"][0]["name"] == "Flame"


def test_species_card_normalizes_traits_languages_and_bonuses():
    card=build_species_card(entity("species", {
        "size":{"name":"Medium"}, "type":{"name":"Humanoid"},
        "speed":{"walk":30,"unit":"feet"}, "darkvision":60,
        "languages":{"data":[{"name":"Common","desc":"Used throughout the realms"}]},
        "ability_score_increases":{"dexterity":2,"wisdom":1},
        "traits":[{"name":"Keen Senses","desc":"You have proficiency in Perception."}],
    }))
    assert card["speed"] == "Walk 30 feet"
    assert card["darkvision"] == "60 feet"
    assert card["languages"][0]["name"] == "Common"
    assert {row["name"] for row in card["ability_bonuses"]} == {"Dexterity","Wisdom"}
    assert card["traits"][0]["name"] == "Keen Senses"


def test_entity_template_renders_magic_item_and_species_cards():
    env=Environment(loader=FileSystemLoader(Path(__file__).parents[1]/"app"/"templates"))
    env.filters["render_markdown"] = _render_markdown
    template=env.get_template("entity_detail.html")
    common=dict(variants=[],primary_asset=None,descriptor_badges=[],return_to="/compendium",monster=None)
    magic_entity=SimpleNamespace(id=1,public_id="m",entity_type="magicitem",name="Flame Tongue",data_json={})
    html=template.render(entity=magic_entity,magic_item=build_magic_item_card(entity("magicitem",{"rarity":"Rare","description":"Flame."})),species=None,**common)
    assert "magic-item-stat-card" in html and "Rarity" in html
    species_entity=SimpleNamespace(id=2,public_id="s",entity_type="species",name="Elf",data_json={})
    html=template.render(entity=species_entity,species=build_species_card(entity("species",{"size":"Medium","traits":[{"name":"Trance","desc":"Rest deeply."}]})),magic_item=None,**common)
    assert "species-stat-card" in html and "Species Traits" in html
