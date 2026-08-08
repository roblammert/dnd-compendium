from pathlib import Path


def test_printable_character_sheet_preserves_v03114_requirements():
    template = Path("app/templates/character_print.html").read_text()
    assert '<span class="k">AC</span>' in template
    assert 'HP Current / Max' in template and 'Temp HP' in template
    assert 'Hit Dice:' in template and '<span class="k">Prof</span>' in template
    assert '<h2>Traits</h2>' in template
    assert '<h2>Features</h2>' in template
    assert 'render_markdown' in template
    assert '@page {' in template and 'size: Letter;' in template


def test_print_markdown_has_table_and_emphasis_styles():
    template = Path("app/templates/character_print.html").read_text()
    assert '.rich table' in template
    assert '.rich th,.rich td' in template
    assert '.rich strong' in template
    assert '.rich em' in template


def test_version_is_current_or_newer_than_03114():
    assert 'version = "0.33.8"' in Path("pyproject.toml").read_text()
    assert 'APP_VERSION = "0.33.8"' in Path("app/version.py").read_text()
