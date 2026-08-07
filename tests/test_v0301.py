from pathlib import Path


def test_loot_content_layout_rules_exist():
    css = Path("app/static/css/app.css").read_text()
    assert "v0.30.1 Loot Generator Content Profile layout" in css
    assert ".loot-content-grid>.tactical-fieldset" in css
    assert "grid-template-columns:1.1rem minmax(0,1fr)" in css
    assert "overflow-wrap:anywhere" in css


def test_version_metadata_exists():
    assert 'version = "' in Path("pyproject.toml").read_text()
    assert 'from app.version import APP_VERSION' in Path("app/main.py").read_text()
    assert 'APP_VERSION = "' in Path("app/version.py").read_text()
