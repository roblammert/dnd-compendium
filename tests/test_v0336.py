from pathlib import Path


def test_pa_ability_equation_and_live_modifier_markup():
    text=Path('app/templates/player_architect_steps/abilities.html').read_text()
    assert 'data-pa-ability-calc' in text
    assert 'Roll (' in text
    assert 'Blueprint (' in text
    assert 'pa-ability-modifier' in text


def test_pa_guarded_navigation_and_labels():
    text=Path('app/templates/tools_player_architect.html').read_text()
    assert 'data-pa-nav' in text
    assert 'Save & Next Step' in text
    assert 'pa-dirty-dialog' in text
    assert 'Save & Continue' in text
    assert 'Discard Changes' in text
    assert 'Character Library' in text


def test_pa_dirty_navigation_script():
    js=Path('app/static/js/player_architect.js').read_text()
    assert 'paIsDirty' in js
    assert 'pa_navigation_destination' in js
    assert 'paNavigateWithSave' in js
    assert 'data-pa-dirty-discard' in js
    assert 'data-pa-ability-calc' in js


def test_pa_route_honors_navigation_destination():
    code=Path('app/player_architect_routes.py').read_text()
    assert 'pa_navigation_destination' in code
    assert 'destination == "library"' in code
    assert 'destination in STEP_KEYS' in code


def test_release_version_v0336():
    assert Path('app/version.py').read_text().strip() == 'APP_VERSION = "0.33.8"'
    assert 'version = "0.33.8"' in Path('pyproject.toml').read_text()
