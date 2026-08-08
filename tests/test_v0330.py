from pathlib import Path

ROUTES = Path('app/player_architect_routes.py').read_text()
MODELS = Path('app/models.py').read_text()
SHELL = Path('app/templates/tools_player_architect.html').read_text()
HOME = Path('app/templates/tools_player_architect_home.html').read_text()
TOOLS = Path('app/templates/tools_layout.html').read_text()
CSS = Path('app/static/css/app.css').read_text()
JS = Path('app/static/js/player_architect.js').read_text()


def test_player_architect_is_separate_subsystem():
    assert 'class ArchitectCharacter' in MODELS
    assert 'class ArchitectBlueprintEntry' in MODELS
    assert 'from app.character_services' not in ROUTES
    assert 'from app.character_rules_2024' not in ROUTES
    assert 'APIRouter(prefix="/tools/player-architect")' in ROUTES


def test_tools_sidebar_marks_architect_in_development():
    assert 'Player Architect' in TOOLS
    assert 'IN DEVELOPMENT' in TOOLS
    assert 'href="/tools/player-architect"' in TOOLS


def test_landing_page_is_streamlined_and_icon_driven():
    for heading in ['Name', 'Race / Species', 'Class', 'Level']:
        assert heading in HOME
    assert 'Modify Character' in HOME
    assert 'PDF to Print' in HOME
    assert 'Delete Character' in HOME
    assert 'pa-create-dialog' in HOME


def test_architect_shell_has_fixed_work_areas_and_live_status():
    assert 'pa-step-sidebar' in SHELL
    assert 'Character Blueprint' in SHELL
    assert 'pa-status-bar' in SHELL
    for label in ['HP','AC','PB','Race','Class','Level']:
        assert f'<small>{label}</small>' in SHELL
    assert '.pa-status-bar{position:fixed' in CSS
    assert '.pa-step-sidebar{position:sticky' in CSS


def test_blueprint_supports_locked_and_manual_entries():
    assert 'origin_kind="automated"' in ROUTES
    assert 'is_locked=True' in ROUTES
    assert 'origin_kind="manual"' in ROUTES
    assert 'Verify the manual blueprint entry' in ROUTES
    assert 'Automated blueprint entries cannot be edited' in ROUTES
    assert 'Automated blueprint entries cannot be deleted' in ROUTES


def test_first_five_steps_are_implemented_and_rest_stubbed():
    for name in ['identity','race','class','abilities','background']:
        text=Path(f'app/templates/player_architect_steps/{name}.html').read_text()
        assert 'id="pa-step-form"' in text
    assert 'Next Step' in SHELL and 'Previous Step' in SHELL and 'View Blueprint' in SHELL
    for name in ['proficiencies','languages','feats','spells','details','review']:
        text=Path(f'app/templates/player_architect_steps/{name}.html').read_text()
        assert 'STUB' in text


def test_full_compendium_catalogs_are_not_source_filtered():
    assert '_all_entities(db,["species","race"])' in ROUTES
    assert '_all_entities(db,["background"])' in ROUTES
    assert '_all_entities(db,["alignment"])' in ROUTES
    assert 'source_document ==' not in ROUTES


def test_subclasses_filter_from_parent_relationship():
    assert 'subclass_of' in ROUTES
    assert 'data-parent-text' in Path('app/templates/player_architect_steps/class.html').read_text()
    assert 'function filterSubclasses' in JS


def test_base_abilities_and_blueprint_modifiers_are_separate():
    assert 'base_ability_scores' in MODELS
    assert 'mods={a:0 for a in ABILITIES}' in ROUTES
    assert 'scores={a:base[a]+mods[a]' in ROUTES
    assert 'Minimum requirements not met:' in ROUTES
