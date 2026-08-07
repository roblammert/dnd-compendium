from pathlib import Path


def test_v03114_printable_character_sheet_layout():
    template = Path("app/templates/character_print.html").read_text()
    assert '<span class="label">AC</span>' in template
    assert 'Armor Class</span>' not in template
    assert 'class="hp-row"' in template
    assert 'Current HP' in template and 'Temp HP' in template
    assert template.index('Hit Dice') < template.index('class="hp-row"')
    assert template.index('Proficiency Bonus') < template.index('class="hp-row"')
    assert 'class="attack-equipment-row"' in template
    assert '<h2>Traits</h2>' in template
    assert '<h2>Features</h2>' in template
    assert "feature.description|render_markdown" in template
    assert "feat.summary|render_markdown" in template
    assert 'min-height:2.7em' in template
    assert '@page{size:Letter' in template


def test_v03114_print_markdown_has_table_and_emphasis_styles():
    template = Path("app/templates/character_print.html").read_text()
    assert '.print-rich table' in template
    assert '.print-rich th,.print-rich td' in template
    assert '.print-rich strong' in template
    assert '.print-rich em' in template


def test_version_03114():
    assert 'version = "0.31.14"' in Path("pyproject.toml").read_text()
    assert 'APP_VERSION = "0.31.14"' in Path("app/main.py").read_text()
