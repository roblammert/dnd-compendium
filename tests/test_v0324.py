from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROUTES=(ROOT/'app/character_routes.py').read_text()
STEP=(ROOT/'app/templates/character_steps/spells.html').read_text()
PRINT=(ROOT/'app/templates/character_print.html').read_text()
JS=(ROOT/'app/static/js/app.js').read_text()


def test_builder_is_cantrip_only_and_locks_on_completion():
    assert 'Cantrips & Feats' in ROUTES
    assert 'if level == 0: cantrips.append(pid)' in ROUTES
    assert 'row.prepared_spells=[]' in ROUTES
    assert 'choices["cantrips_locked"] = True' in ROUTES
    assert 'Level 1+ spells are not chosen here' in STEP
    assert 'permanently locked when the character is marked complete' in STEP
    assert 'name="prepared"' not in STEP


def test_spell_print_page_has_eight_cantrip_lines_and_nine_writable_levels():
    assert 'for i in range(8)' in PRINT
    assert 'for level in range(1,10)' in PRINT
    assert 'spell-level-grid' in PRINT
    assert 'range(4)' in PRINT
    assert 'Prepared level 1+ spells' in PRINT
    assert 'Prepared spells are not selected in the Character Builder' in PRINT
    assert 'fixed when this character was generated and cannot be changed afterward' in PRINT


def test_spell_usage_is_bottom_anchored_and_slots_are_calculated():
    assert '.spell-page { min-height:9.42in; display:flex; flex-direction:column; }' in PRINT
    assert '.spell-workspace { flex:1 1 auto; min-height:0; }' in PRINT
    assert 'derived.spell_slots.get(level,0)' in PRINT
    assert 'Spell Usage' in PRINT


def test_spell_js_has_no_prepared_or_level_selection_logic():
    assert 'preparedLimit' not in JS
    assert 'input[name="prepared"]' not in JS
    assert 'levelFilter' not in JS[JS.index('function initSpellBuilder'):JS.index('function initCharacterEnhancements')]
