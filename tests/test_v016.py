from types import SimpleNamespace
from app.main import _render_markdown
from app.services import build_item_card, build_magic_item_card, build_species_card


def entity(kind, data):
    return SimpleNamespace(entity_type=kind, data_json=data, summary=None)


def test_markdown_tables_render_as_html_tables():
    html = str(_render_markdown('| d10 | Damage Type |\n|---:|---|\n| 1 | Acid |'))
    assert '<table>' in html
    assert '>d10</th>' in html
    assert '<td>Acid</td>' in html


def test_magic_item_weight_armor_class_and_size_metadata():
    card = build_magic_item_card(entity('magicitem', {
        'weight': 10,
        'armor': {'ac_display': '11 + Dex modifier', 'name': 'Leather'},
        'type': {'name': 'Armor'},
    }))
    assert card['weight'] == '10.0 lb.'
    assert card['armor_class'] == '11 + Dex modifier'
    assert any(row['label'] == 'Armor Class' for row in card['summary_rows'])


def test_species_summary_omits_speed_but_keeps_size():
    card = build_species_card(entity('species', {'size': {'name': 'Small'}, 'speed': {'walk': 30}}))
    labels = [row['label'] for row in card['summary_rows']]
    assert 'Size' in labels
    assert 'Speed' not in labels


def test_item_card_normalizes_item_metadata():
    card = build_item_card(entity('item', {
        'category': {'name': 'Adventuring Gear'},
        'cost': '2 gp',
        'weight': 3,
        'properties': [{'name': 'Utility'}],
        'description': 'A useful item.',
    }))
    assert card['category'] == 'Adventuring Gear'
    assert card['weight'] == '3.0 lb.'
    assert card['properties'] == ['Utility']
