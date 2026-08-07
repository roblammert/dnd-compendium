from pathlib import Path
from app.tools_routes import templates


def base_context(template):
    params={"mode":"xp_budget","cr_min":0,"cr_max":5,"monster_count":6,"target_count":6,"party_levels":[5]*4,"difficulty":"hard","scale_mode":"none","baseline_party_size":4,"party_size":4,"average_party_level":5,"composition":"mixed","objective":"defeat","terrain":"open","pace":"standard","creature_type":"any","count_min":8,"count_max":12,"max_value_gp":40,"max_total_value_gp":600,"rarity":[],"include_equipment":True,"include_items":True,"include_magicitems":True,"include_weapons":True}
    context=dict(tools_section='encounter-builder',selected=[],rows=[],budget=3000,budget_breakdown=[],budget_status='Under budget',total_xp=0,adjusted_xp=0,encounter_multiplier=1,total_cr=0,lazy_limit=10,lazy_status='Within benchmark',ratio=1,party_size=4,total_party_levels=20,average_level=5,params=params,creature_types=[],objective_note='',terrain_note='',pace_target='3–5 rounds',total_value_gp=0)
    return templates.get_template(template).render(**context)


def test_target_monster_count_is_available_to_budget_modes():
    html=base_context('tools_encounter_builder.html')
    assert 'Target monster count' in html
    assert 'name="monster_count"' in html
    source=Path('app/tools_routes.py').read_text()
    assert 'len(selected) < target_count' in source
    assert 'slots_remaining = max(0, target_count - len(selected))' in source


def test_scenario_controls_use_non_overflowing_cards():
    html=base_context('tools_encounter_builder.html')
    assert html.count('class="scenario-card"') == 4
    css=Path('app/static/css/app.css').read_text()
    assert '.scenario-card select' in css
    assert 'max-width:100%' in css


def test_loot_generator_uses_tactical_workbench_design():
    html=base_context('tools_loot_generator.html')
    assert 'Treasure Design Suite' in html
    assert 'Value Envelope' in html
    assert 'Content Profile' in html
    assert 'encounter-dashboard loot-dashboard' in html
