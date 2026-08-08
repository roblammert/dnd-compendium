from types import SimpleNamespace
from pathlib import Path
from app.player_architect_routes import _auto_entries, _background_choice_notes, _background_attention_notes, CORE_TRAIT_ALIASES

def ent(name, source, benefits):
    return SimpleNamespace(name=name, data_json={'benefits':benefits}, source_display_name=source, source_document=None, game_system_name=None)

def test_2024_background_benefits_parse_as_requested():
    e=ent('Acolyte','5e 2024 Rules',[
      {'desc':'Intelligence, Wisdom, Charisma','name':'Ability Scores','type':'ability_score'},
      {'desc':'Choose A or B: (A) supplies; or (B) 50 GP','name':'Equipment','type':'equipment'},
      {'desc':'Magic Initiate (Cleric)','name':'Feat','type':'feat'},
      {'desc':'Insight and Religion','name':'Skill Proficiencies','type':'skill_proficiency'},
      {'desc':"Calligrapher's Supplies",'name':'Tool Proficiency','type':'tool_proficiency'},
    ])
    rows=_auto_entries(e,'Background')
    triples={(r['modifier'],r['stat']) for r in rows}
    assert ('+1','INT,WIS,CHA') in triples
    assert ('+Insight,Religion','Skill Proficiencies') in triples
    assert ("+Calligrapher's Supplies",'Tool Proficiencies') in triples
    choices=_background_choice_notes(e)
    assert any(x['stat']=='Equipment' for x in choices)
    attention=_background_attention_notes(e)
    assert any(x['stat']=='Feats' and 'Magic Initiate' in x['instruction'] for x in attention)

def test_2014_background_fixed_equipment_is_attention_and_language_choice():
    e=ent('Acolyte','5e 2014 Rules',[
      {'desc':'A holy symbol, prayer book, vestments, common clothes, and 15 gp','name':'Equipment','type':'equipment'},
      {'desc':'Two of your choice','name':'Languages','type':'language'},
      {'desc':'Insight, Religion','name':'Skill Proficiencies','type':'skill_proficiency'},
    ])
    assert ('+Insight,Religion','Skill Proficiencies') in {(r['modifier'],r['stat']) for r in _auto_entries(e,'Background')}
    assert any(x['stat']=='Equipment' for x in _background_attention_notes(e))
    assert any(x['stat']=='Languages' for x in _background_choice_notes(e))

def test_a5e_partial_choice_is_not_partially_applied():
    e=ent('Charlatan',"Adventurer's Guide",[
      {'desc':'+1 to Charisma and one other ability score.','name':'Ability Score Increases','type':'ability_score'},
      {'desc':'Deception, and either Culture, Insight, or Sleight of Hand.','name':'Skill Proficiencies','type':'skill_proficiency'},
      {'desc':'Disguise kit, forgery kit.','name':'Tool Proficiencies','type':'tool_proficiency'},
    ])
    rows=_auto_entries(e,'Background')
    assert not any(r['stat'] in {'CHA','Ability Scores'} for r in rows)
    assert ('+Disguise kit,forgery kit','Tool Proficiencies') in {(r['modifier'],r['stat']) for r in rows}
    choices=_background_choice_notes(e)
    assert any(x['stat']=='Ability Scores' for x in choices)
    assert any(x['stat']=='Skill Proficiencies' for x in choices)

def test_starting_equipment_class_choice_category():
    assert CORE_TRAIT_ALIASES['starting equipment']=='Equipment'

def test_attention_ui_and_background_preview_hooks_exist():
    shell=Path('app/templates/tools_player_architect.html').read_text()
    bg=Path('app/templates/player_architect_steps/background.html').read_text()
    js=Path('app/static/js/player_architect.js').read_text()
    assert 'Player Attention' in shell and 'data-pa-attention-list' in shell
    assert 'data-pa-choice' in bg and 'data-pa-attention' in bg
    assert 'previewAttentionNotes' in js
