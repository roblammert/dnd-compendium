from pathlib import Path

from app.tools_routes import DIFFICULTY_INDEX, XP_THRESHOLDS, templates


def test_mixed_level_party_medium_budget_is_sum_of_member_thresholds():
    levels = [2, 4, 6, 7, 8, 10]
    budget = sum(XP_THRESHOLDS[level][DIFFICULTY_INDEX["medium"]] for level in levels)
    assert budget == 3800


def test_encounter_builder_has_only_supported_build_modes_and_keep_controls():
    params = {
        "mode": "xp_budget", "cr_min": 0, "cr_max": 5, "monster_count": 4,
        "party_levels": [2, 4, 6, 7, 8, 10], "difficulty": "medium",
        "scale_mode": "lazy_dm", "baseline_party_size": 4, "party_size": 6, "average_party_level": 6,
        "composition": "mixed", "objective": "defeat", "terrain": "open", "pace": "standard", "creature_type": "any",
    }
    html = templates.get_template("tools_encounter_builder.html").render(
        tools_section="encounter-builder", selected=[], budget=3800,
        budget_breakdown=[], budget_status="Under budget", total_xp=0, total_cr=0,
        lazy_limit=18.5, lazy_status="Within benchmark", ratio=1.5, party_size=6,
        total_party_levels=37, average_level=37/6, params=params, adjusted_xp=0, encounter_multiplier=1,
        creature_types=[], objective_note="", terrain_note="", pace_target="3–5 rounds",
    )
    assert 'value="random_cr"' in html
    assert 'value="xp_budget"' in html
    assert 'value="manual"' not in html
    assert 'Manual search' not in html
    assert 'value="lazy_dm" selected' in html
    assert 'class="keep-checkbox"' in Path('app/templates/tools_encounter_builder.html').read_text()
    assert 'name="party_level"' in html


def test_loot_generator_has_two_value_sliders_and_no_coin_includes():
    params = {
        "count_min": 8, "count_max": 12, "max_value_gp": 40,
        "max_total_value_gp": 600, "include_equipment": True,
        "include_items": True, "include_magicitems": True,
        "include_weapons": True, "rarity": [],
    }
    html = templates.get_template("tools_loot_generator.html").render(
        tools_section="loot-generator", rows=[], params=params, total_value_gp=0
    )
    assert html.count('type="range"') == 2
    assert 'name="max_value_gp"' in html
    assert 'name="max_total_value_gp"' in html
    for coin in ("include_pp", "include_gp", "include_sp", "include_cp"):
        assert f'name="{coin}"' not in html
