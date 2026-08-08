from pathlib import Path

PRINT = Path("app/templates/character_print.html").read_text()
STEPPER = Path("app/templates/tools_character_builder.html").read_text()
CSS = Path("app/static/css/app.css").read_text()


def test_runtime_version_is_centralized():
    version = Path("app/version.py").read_text()
    assert 'APP_VERSION = "0.33.3"' in version
    for name in ["app/main.py", "app/tools_routes.py", "app/character_routes.py", "app/user_routes.py"]:
        text = Path(name).read_text()
        assert "from app.version import APP_VERSION" in text
        assert 'templates.env.globals["app_version"] = APP_VERSION' in text or name == "app/main.py"
    assert 'templates.env.globals["app_version"] = "' not in Path("app/tools_routes.py").read_text()
    assert 'templates.env.globals["app_version"] = "' not in Path("app/character_routes.py").read_text()


def test_step_movers_use_centered_svg_arrows():
    assert STEPPER.count('class="step-arrow-icon"') == 2
    assert '>↑</a>' not in STEPPER and '>↓</a>' not in STEPPER
    assert '.step-arrow-icon{' in CSS
    assert 'justify-content:center!important' in CSS


def test_spell_boxes_have_ten_equal_fitting_lines():
    assert '{% for _ in range(10) %}<div class="write-line">' in PRINT
    assert 'grid-template-rows:repeat(3,1.69in)' in PRINT
    assert '.write-line { border-bottom:1px dotted #b9a77f; min-height:0; flex:1 1 0;' in PRINT
    assert 'overflow:hidden; display:flex; flex-direction:column;' in PRINT


def test_ability_modifier_separators_are_removed():
    assert '.ability-mod { font-weight:800; font-size:10pt; text-align:center; border-left:0; border-right:0;' in PRINT
    assert '.ability-score { font:700 18pt Georgia,serif; color:#173643; text-align:center; border-left:0; border-right:0;' in PRINT


def test_currency_is_after_at_a_glance_features():
    glance = PRINT.index('>At-a-Glance Features</h2>')
    currency = PRINT.index('<span>Currency</span>')
    assert glance < currency
    assert PRINT.count('<span>Currency</span>') == 1
