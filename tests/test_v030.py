from pathlib import Path
from app.tools_routes import templates

def test_player_tools_and_bulk_list_actions_are_present():
    layout=Path('app/templates/tools_layout.html').read_text()
    assert 'Feat Evaluator' in layout
    assert 'Weapons Evaluator' in layout
    assert Path('app/templates/tools_loadout_generator.html').exists()
    assert Path('app/templates/tools_feat_evaluator.html').exists()
    assert Path('app/templates/tools_weapon_evaluator.html').exists()
    assert 'data-add-results-to-list' in Path('app/templates/tools_loot_generator.html').read_text()
    assert 'data-add-results-to-list' in Path('app/templates/tools_encounter_builder.html').read_text()
    assert '@router.post("/lists/bulk-add")' in Path('app/user_routes.py').read_text()

def test_lists_page_uses_modal_and_public_sections():
    html=Path('app/templates/lists.html').read_text()
    assert 'id="createListModal"' in html
    assert "Other's Lists" in html
    assert '>My Lists<' in html
