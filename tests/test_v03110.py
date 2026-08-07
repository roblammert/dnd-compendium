from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v03110_version():
    assert 'version = ' in (ROOT / 'pyproject.toml').read_text()


def test_character_builder_feats_are_rows_without_inline_descriptions():
    template = (ROOT / 'app/templates/character_steps/spells.html').read_text()
    assert 'feat-choice-list' in template
    assert 'feat-builder-row' in template
    assert 'feat-choice-grid' not in template
    assert 'feat-brief' not in template
    assert 'row.summary[:180]' not in template
    assert 'More Info' in template


def test_feat_rows_have_compact_layout():
    css = (ROOT / 'app/static/css/app.css').read_text()
    assert '.feat-choice-list{display:grid;grid-template-columns:1fr' in css
    assert '.feat-builder-row{display:grid' in css
    assert '.feat-builder-status' in css
