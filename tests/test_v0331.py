from pathlib import Path

ROUTES = Path('app/player_architect_routes.py').read_text()
RACE = Path('app/templates/player_architect_steps/race.html').read_text()
CLASS = Path('app/templates/player_architect_steps/class.html').read_text()
ABIL = Path('app/templates/player_architect_steps/abilities.html').read_text()
BG = Path('app/templates/player_architect_steps/background.html').read_text()
SHELL = Path('app/templates/tools_player_architect.html').read_text()
CSS = Path('app/static/css/app.css').read_text()
JS = Path('app/static/js/player_architect.js').read_text()


def test_pa_race_and_class_use_rows_not_card_grids():
    assert 'pa-choice-list' in RACE and 'pa-choice-row' in RACE
    assert 'pa-card-grid' not in RACE
    assert 'pa-choice-list' in CLASS and 'pa-choice-row' in CLASS


def test_pa_primary_class_catalog_uses_only_subclass_of_for_class_endpoint():
    assert '_all_entities(db, ["classe"])' in ROUTES
    assert 'if "subclass_of" in data and data.get("subclass_of") is not None' in ROUTES
    assert 'parent_class' not in ROUTES[ROUTES.index('def _class_catalog'):ROUTES.index('def _extract_named')]
    assert 'subclass_parent_text' in CLASS


def test_pa_ability_editor_is_compact_and_responsive():
    assert 'pa-ability-card' in ABIL
    assert 'pa-ability-breakdown' in ABIL
    assert '.pa-ability-editor{grid-template-columns:repeat(3' in CSS


def test_pa_background_alignment_are_explicit_stacked_rows():
    assert 'pa-background-stack' in BG
    assert BG.index('>Background<') < BG.index('Background Description') < BG.index('>Alignment<') < BG.index('Alignment Description')
    assert 'data-pa-description-select' in BG


def test_pa_blueprint_is_overlay_drawer_with_collapsed_tab():
    assert 'pa-blueprint-collapsed-tab' in SHELL
    assert 'pa-blueprint-scrim' in SHELL
    assert '--pa-drawer-width:min(70vw,1100px)' in CSS
    assert 'body.pa-blueprint-open .pa-blueprint-drawer' in CSS
    assert "classList.toggle('pa-blueprint-open'" in JS
