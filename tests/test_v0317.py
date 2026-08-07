from pathlib import Path
from app.character_rules_2024 import spell_selection_limits

ROOT=Path(__file__).resolve().parents[1]

def test_v0317_version():
    assert 'version = "' in (ROOT/'pyproject.toml').read_text()

def test_stepper_is_non_clickable_with_movers():
    html=(ROOT/'app/templates/tools_character_builder.html').read_text()
    assert 'character-step-indicator' in html
    assert 'character-step-movers' in html
    assert 'hx-get=' not in html

def test_background_lists_are_non_scrolling_grids():
    css=(ROOT/'app/static/css/app.css').read_text()
    assert '.skill-choice-grid{grid-template-columns:repeat(2' in css
    assert '.token-choice-grid' in css
    assert 'max-height:none;overflow:visible' in css

def test_equipment_search_uses_server_like_and_filter_controls():
    routes=(ROOT/'app/character_routes.py').read_text()
    html=(ROOT/'app/templates/character_steps/gear.html').read_text()
    assert 'Entity.name.ilike(pattern)' in routes
    assert 'cast(Entity.data_json,String).ilike(pattern)' in routes
    assert 'data-character-equipment-filter' in html
    assert '>All Selected<' in html

def test_spells_and_feats_are_source_aware_and_limited():
    html=(ROOT/'app/templates/character_steps/spells.html').read_text()
    routes=(ROOT/'app/character_routes.py').read_text()
    assert 'data-character-spell-level' in html
    assert 'descriptor-pill-source' in html
    assert 'data-reference-url' in html
    assert '_spell_matches_class_explicit' in routes
    assert '_feat_eligibility' in routes
    assert spell_selection_limits('wizard',1)=={'cantrips':3,'prepared':4,'known':6,'max_spell_level':1}
