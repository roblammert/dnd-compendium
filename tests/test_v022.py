from pathlib import Path
from app.services import build_weapon_card, format_cost
from app.models import Entity


def entity(data):
    return Entity(public_id="ent_v22", entity_type="weapon", name="Dagger", slug="dagger", canonical_key="dagger", source_kind="open5e", data_json=data)


def test_weapon_properties_preserve_description_range_and_link():
    card=build_weapon_card(entity({"properties":[{"name":"Thrown","desc":"Throw this weapon.","range":{"normal":20,"long":60,"unit":"feet"},"permalink":"https://example.test/thrown"}]}))
    prop=card["properties"][0]
    assert prop["name"] == "Thrown"
    assert prop["description"] == "Throw this weapon."
    assert prop["range"] == "20/60 feet"
    assert prop["url"].endswith("/thrown")


def test_cost_uses_simplest_coin_and_tooltip():
    cost=format_cost(0.05)
    assert cost["value"] == "5 CP"
    assert "0.005 PP" in cost["tooltip"]
    assert "0.05 GP" in cost["tooltip"]
    assert "0.5 SP" in cost["tooltip"]
    assert "5 CP" in cost["tooltip"]


def test_local_defaults_are_relative():
    env=Path('.env.example').read_text()
    assert 'DATABASE_URL=sqlite:///./data/compendium.sqlite3' in env
    assert 'ASSET_ROOT=./data/assets' in env


def test_endpoint_management_is_combined_and_inline():
    main=Path('app/main.py').read_text()
    template=Path('app/templates/settings_endpoint_management.html').read_text()
    assert '/settings/endpoint-management/{term}' in main
    assert 'data-endpoint-row-form' in Path('app/templates/fragments/endpoint_management_row.html').read_text()
    assert 'Endpoint Management' in template
