from app.tools_routes import templates

def test_encounter_workbench_exposes_multiple_online_methods():
    params={"mode":"adjusted_xp","cr_min":0,"cr_max":5,"monster_count":4,"party_levels":[5]*4,"difficulty":"hard","scale_mode":"none","baseline_party_size":4,"party_size":4,"average_party_level":5,"composition":"mixed","objective":"defeat","terrain":"open","pace":"standard","creature_type":"any"}
    html=templates.get_template('tools_encounter_builder.html').render(tools_section='encounter-builder',selected=[],budget=3000,budget_breakdown=[],budget_status='Under budget',total_xp=0,adjusted_xp=0,encounter_multiplier=1,total_cr=0,lazy_limit=10,lazy_status='Within benchmark',ratio=1,party_size=4,total_party_levels=20,average_level=5,params=params,creature_types=[],objective_note='',terrain_note='',pace_target='3–5 rounds')
    for mode in ('xp_budget','adjusted_xp','lazy_story','composition','random_cr'):
        assert f'value="{mode}"' in html
    assert 'Encounter Roster' in html
    assert 'name="keep"' in __import__('pathlib').Path('app/templates/tools_encounter_builder.html').read_text()
    assert 'Scenario Parameters' in html
