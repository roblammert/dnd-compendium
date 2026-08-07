from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v0319_version():
    assert '0.31.9' in (ROOT / 'pyproject.toml').read_text()


def test_dynamic_filter_rows_are_really_hidden():
    css = (ROOT / 'app/static/css/app.css').read_text()
    assert '[data-character-equipment-list] [data-equipment-row][hidden]' in css
    assert '[data-character-spell-list] [data-spell-row][hidden]' in css
    assert 'display: none !important' in css


def test_gear_search_uses_query_and_filter_kind():
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert "q:(search.value||'').trim(), kind:(filter?.value||'all')" in js
    assert "filter?.addEventListener('change',()=>{ applyVisibility(); runSearch(); })" in js


def test_legacy_name_only_character_filters_removed():
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert "document.querySelectorAll('[data-character-equipment-list] [data-equipment-name]')" not in js
    assert "document.querySelectorAll('[data-character-spell-list] [data-spell-name]')" not in js


def test_search_enter_is_not_parent_form_submit():
    js = (ROOT / 'app/static/js/app.js').read_text()
    assert js.count("if(event.key==='Enter'){ event.preventDefault(); event.stopPropagation(); runSearch(); }") >= 2
