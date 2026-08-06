from pathlib import Path
from app.models import Entity
from app.services import build_weapon_card
from app.endpoint_defaults import endpoint_default

def weapon(data):
    return Entity(public_id="ent_v23",entity_type="weapon",name="Battleaxe",slug="battleaxe",canonical_key="battleaxe",source_kind="open5e",data_json=data)

def test_battleaxe_nested_property_and_links():
    card=build_weapon_card(weapon({"damage_dice":"1d8","damage_type":{"key":"slashing","name":"Slashing"},"properties":[{"detail":"1d10","property":{"name":"Versatile","desc":"This weapon can be used with one or two hands."}}]}))
    damage=next(row for row in card["summary_rows"] if row["label"]=="Damage Type")["value"]
    assert damage["url"] == "/compendium/damagetype/slashing"
    prop=card["properties"][0]
    assert prop["detail"] == "1d10"
    assert prop["description"].startswith("This weapon")
    assert prop["url"] == "/compendium/weaponpropertie/versatile"

def test_endpoint_defaults_are_curated():
    assert endpoint_default("gamesystem")["display"] == "Game System"
    assert endpoint_default("weaponpropertie")["display"] == "Weapon Property"
    assert endpoint_default("monster")["minimum_role"] == "user"

def test_private_lists_are_owner_only_source_code_guard():
    source=Path("app/user_routes.py").read_text()
    assert "row.owner_id!=user.id and row.is_public" in source
    assert "row.owner_id != user.id" in source
