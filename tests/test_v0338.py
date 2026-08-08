from pathlib import Path
from types import SimpleNamespace

from app.player_architect_routes import _blueprint_values, _proficiency_step_data


class FakeDB:
    pass


def test_step06_template_is_implemented_and_blueprint_driven():
    text = Path('app/templates/player_architect_steps/proficiencies.html').read_text()
    assert 'Skill Proficiencies' in text
    assert 'Other Proficiencies' in text
    assert 'architect_skill_rows' in text
    assert 'architect_other_proficiencies' in text
    assert 'data-pa-info-url' in text
    assert 'STUB' not in text


def test_step06_is_enabled_and_persists_skill_selection():
    routes = Path('app/player_architect_routes.py').read_text()
    assert '"proficiencies"' in routes.split('implemented_step =', 1)[1].split('\n', 1)[0]
    assert 'elif step=="proficiencies"' in routes
    assert 'form.getlist("skill_proficiencies")' in routes
    assert 'prof["skills"] = selected' in routes


def test_proficiency_reference_targets_requested_entity_types():
    routes = Path('app/player_architect_routes.py').read_text()
    assert "('item', 'itemset', 'armor', 'weapon', 'weapons')" in routes
    assert 'func.lower(Entity.name) == title.casefold()' in routes


def test_step06_css_uses_non_scrolling_responsive_skill_cards():
    css = Path('app/static/css/app.css').read_text()
    assert '.pa-skill-proficiency-list' in css
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in css
    assert '.pa-other-proficiency-card' in css


def test_version_0338():
    assert Path('app/version.py').read_text().strip() == 'APP_VERSION = "0.33.8"'
