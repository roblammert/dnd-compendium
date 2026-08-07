from pathlib import Path


def test_loot_content_layout_rules_exist():
    css = Path("app/static/css/app.css").read_text()
    assert "v0.30.1 Loot Generator Content Profile layout" in css
    assert ".loot-content-grid>.tactical-fieldset" in css
    assert "grid-template-columns:1.1rem minmax(0,1fr)" in css
    assert "overflow-wrap:anywhere" in css


def test_version_is_0301():
    assert 'version = "0.30.1"' in Path("pyproject.toml").read_text()
    assert 'APP_VERSION = "0.30.1"' in Path("app/main.py").read_text()
