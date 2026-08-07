from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v0318_version():
    assert 'version = ' in (ROOT / 'pyproject.toml').read_text()


def test_character_navigation_has_dirty_guard():
    html = (ROOT / 'app/templates/tools_character_builder.html').read_text()
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert 'character-unsaved-dialog' in html
    assert 'data-dirty-save' in html
    assert 'data-dirty-discard' in html
    assert 'data-character-nav-target' in html
    assert 'snapshot(currentForm())' in js
    assert 'Save &amp; Move' in html


def test_previous_buttons_do_not_submit_unsaved_forms():
    for path in (ROOT / 'app/templates/character_steps').glob('*.html'):
        text = path.read_text()
        if '>Previous</button>' in text:
            assert 'type="button" class="secondary-action" data-character-nav-target=' in text


def test_background_languages_and_proficiencies_are_rows_without_scroll():
    css = (ROOT / 'app/static/css/app.css').read_text()
    assert '.token-choice-grid{' in css
    assert 'display:flex;' in css
    assert 'flex-direction:column;' in css
    assert 'max-height:none;' in css
    assert 'overflow:visible;' in css


def test_equipment_filter_uses_semantic_type_and_enter_does_not_submit():
    services = (ROOT / 'app/character_services.py').read_text()
    gear = (ROOT / 'app/templates/character_steps/gear.html').read_text()
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert '"filter_type": semantic_type' in services
    assert 'data-equipment-type="{{ row.filter_type }}"' in gear
    assert "filter?.addEventListener('change',()=>{ applyVisibility(); runSearch(); });" in js
    assert "if(event.key==='Enter'){ event.preventDefault(); event.stopPropagation(); runSearch(); }" in js


def test_spell_filter_uses_normalized_levels_and_enter_does_not_submit():
    routes = (ROOT / 'app/character_routes.py').read_text()
    spells = (ROOT / 'app/templates/character_steps/spells.html').read_text()
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert 'context["spell_row_levels"]' in routes
    assert 'data-spell-level="0"' in spells
    assert 'data-character-spell-level' not in spells
    assert '[data-character-equipment-search], [data-character-spell-search]' in js
