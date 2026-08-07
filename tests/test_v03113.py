from pathlib import Path


def test_review_ability_modifier_fit_css():
    css = Path("app/static/css/app.css").read_text()
    assert "v0.31.13" in css
    assert ".review-character-step .review-ability-row" in css
    assert "overflow:hidden" in css
    assert "min-width:0;white-space:nowrap" in css


def test_v03113_version_files_are_present():
    assert 'version = ' in Path("pyproject.toml").read_text()
    assert 'from app.version import APP_VERSION' in Path("app/main.py").read_text()
    assert 'APP_VERSION = ' in Path("app/version.py").read_text()
