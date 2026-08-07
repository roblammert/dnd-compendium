from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_background_asi_is_source_gated_and_common_locked():
    html=(ROOT/'app/templates/character_steps/background.html').read_text()
    assert 'data-is-2024' in html
    assert 'data-background-ability-panel' in html
    assert "language=='Common'" in html
    assert 'disabled' in html

def test_gear_workflow_has_rules_and_cost_ui():
    html=(ROOT/'app/templates/character_steps/gear.html').read_text()
    assert 'data-equipment-cost' in html
    assert 'data-armor-kind' in html
    assert 'data-equipment-locked' in html
    assert 'data-reference-url' in html
    assert 'entity-type-pill' in html

def test_live_rail_is_compact_single_row_css():
    css=(ROOT/'app/static/css/app.css').read_text()
    assert 'grid-template-columns:auto 1fr auto' in css
    assert 'width:94px' in css

def test_identity_is_live_and_gear_js_exists():
    js=(ROOT/'app/static/js/app.js').read_text()
    assert "['input','change'].forEach" in js
    assert 'function initGearBuilder' in js
    assert 'chosen.length>=2' in js
