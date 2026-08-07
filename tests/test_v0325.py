from pathlib import Path

PRINT = Path("app/templates/character_print.html").read_text()

def test_spell_summary_stacks_beside_cantrips():
    assert 'class="spell-top"' in PRINT
    assert 'grid-template-columns:minmax(0,1fr) minmax(0,3fr)' in PRINT
    assert 'grid-template-columns:1fr; grid-template-rows:repeat(4,1fr)' in PRINT

def test_each_spell_level_has_nine_writable_lines():
    assert 'for level in range(1,10)' in PRINT
    assert 'for _ in range(9)' in PRINT
