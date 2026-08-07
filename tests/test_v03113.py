from pathlib import Path


def test_review_ability_modifier_fit_css():
    css = Path("app/static/css/app.css").read_text()
    assert "v0.31.13" in css
    assert ".review-character-step .review-ability-row" in css
    assert "overflow:hidden" in css
    assert "min-width:0;white-space:nowrap" in css


def test_version_03113():
    assert 'version = "0.31.13"' in Path("pyproject.toml").read_text()
    assert 'APP_VERSION = "0.31.13"' in Path("app/main.py").read_text()
