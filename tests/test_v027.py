from app.models import Entity
from app.services import build_skill_card, build_spell_card, build_weapon_card


def ent(entity_type, name, data):
    return Entity(public_id=f'{entity_type}-1', entity_type=entity_type, name=name, slug=name.lower().replace(' ','-'), canonical_key=name.lower().replace(' ','-'), source_kind='open5e', data_json=data)


def test_weapon_uses_item_cost_and_weight_fallback():
    weapon = ent('weapon', 'Battleaxe', {'damage_dice':'1d8','damage_type':{'key':'slashing','name':'Slashing'}})
    item = ent('item', 'Battleaxe', {'cost':10, 'weight':4})
    card = build_weapon_card(weapon, fallback_item=item)
    stats = {row['label']: row['value'] for row in card['primary_stats']}
    assert stats['Cost'] == '1 PP'
    assert stats['Weight'] == '4.0 lb.'


def test_skill_versioned_descriptions():
    card = build_skill_card(ent('skill','Stealth', {'descriptions':[{'gamesystem':'5e-2014','desc':'Hide quietly.'}]}))
    assert card['description_entries'] == [{'game_system':'5e-2014','text':'Hide quietly.'}]


def test_spell_saving_throw_ability():
    card = build_spell_card(ent('spell','Fireball', {'saving_throw_ability': {'key':'dexterity','name':'Dexterity'}}))
    rows = {row['label']: row['value'] for row in card['summary_rows']}
    assert rows['Saving Throw'] == 'Dexterity'
