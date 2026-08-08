from pathlib import Path
from types import SimpleNamespace

from app.player_architect_routes import _auto_entries

SHELL = Path("app/templates/tools_player_architect.html").read_text()
CSS = Path("app/static/css/app.css").read_text()
JS = Path("app/static/js/player_architect.js").read_text()
IDENTITY = Path("app/templates/player_architect_steps/identity.html").read_text()
ROUTES = Path("app/player_architect_routes.py").read_text()


def test_pa_shell_pins_navigation_actions_and_hides_site_footer():
    assert 'pa-sidebar-actions' in SHELL
    assert 'form="pa-step-form"' in SHELL
    assert 'Previous Step' in SHELL and 'Next Step' in SHELL and 'View Blueprint' in SHELL
    assert 'body.pa-architect-active .site-footer' in CSS
    assert 'height:calc(100dvh - var(--pa-site-header-height,72px))' in CSS
    assert 'grid-template-rows:auto minmax(0,1fr) auto' in CSS


def test_pa_identity_places_level_and_xp_in_same_grid_row():
    assert IDENTITY.index('>Level<') < IDENTITY.index('Experience Points (XP)')
    assert IDENTITY.count('class="wide"') == 2


def test_pa_more_info_and_close_controls_are_visible():
    assert '.pa-more-info{border:2px solid #2f7182!important;color:#2f7182!important' in CSS
    assert '.pa-dialog-x{display:grid!important' in CSS
    assert '<svg viewBox="0 0 24 24"' in SHELL


def test_pa_race_modifier_extraction_handles_open5e_shapes():
    elf = SimpleNamespace(name='Elf', data_json={
        'asi': [{'attributes': ['dex'], 'value': 2}],
        'languages': ['Common', 'Elvish'],
    })
    rows = _auto_entries(elf, 'Race')
    assert any(r['stat'] == 'DEX' and r['modifier'] == '+2' for r in rows)
    assert any(r['stat'] == 'Languages' and r['modifier'] == '+Elvish' for r in rows)

    mapped = SimpleNamespace(name='Wood Folk', data_json={'ability_score_increases': {'dexterity': 2, 'wisdom': 1}})
    rows = _auto_entries(mapped, 'Race')
    assert {(r['stat'], r['modifier']) for r in rows} >= {('DEX', '+2'), ('WIS', '+1')}


def test_pa_primary_classes_are_defined_by_empty_subclass_of_only():
    section = ROUTES[ROUTES.index('def _class_catalog'):ROUTES.index('def _extract_named')]
    assert '_all_entities(db, ["class"])' in section
    assert '.get("subclass_of")' in section
    assert 'entity_type == "subclass"' not in section


def test_pa_live_preview_updates_footer_and_background_descriptions():
    assert 'data-pa-status-race' in SHELL and 'data-pa-status-class' in SHELL
    assert "target.textContent=(option && option.value && option.dataset.description)" in JS
    assert "previewAutomatic(card.dataset.paAutoOrigin" in JS
