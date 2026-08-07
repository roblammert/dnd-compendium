from pathlib import Path
from app.character_rules_2024 import spell_slot_totals
from app.character_services import CORE_CONDITIONS_2024

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "app/templates/character_print.html").read_text()


def test_full_caster_level_five_slots():
    assert spell_slot_totals("Cleric", 5) == {1: 4, 2: 3, 3: 2}


def test_half_and_pact_slot_shapes():
    assert spell_slot_totals("Paladin", 5) == {1: 4, 2: 2}
    assert spell_slot_totals("Warlock", 5) == {3: 2}


def test_core_conditions_are_the_2024_fifteen():
    assert len(CORE_CONDITIONS_2024) == 15
    assert "Exhaustion" in CORE_CONDITIONS_2024
    assert "Unconscious" in CORE_CONDITIONS_2024


def test_print_template_has_hit_dice_pips_condition_tracker_and_currency_note():
    assert "Hit Dice: {{ derived.hit_dice_guide.title }}" in TEMPLATE
    assert "hit-die-pip" in TEMPLATE
    assert "Condition Tracker" in TEMPLATE
    assert "100 CP = 10 SP = 1 GP (PP = 10 GP)" in TEMPLATE


def test_spell_page_uses_empty_prepared_pips_and_slot_totals_and_usage_box():
    assert '<i class="prepared"></i>' in TEMPLATE
    assert 'derived.spell_slots.get(level,0)' in TEMPLATE
    assert "Spell Usage" in TEMPLATE
    assert ".prepared.on { background:#fff; }" in TEMPLATE
