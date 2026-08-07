from pathlib import Path
from types import SimpleNamespace

from app.character_rules_2024 import LEVEL_XP
from app.character_services import background_other_proficiencies, background_skills


def background(name="Acolyte", key="acolyte", data=None, source="srd-2024"):
    return SimpleNamespace(
        name=name, canonical_key=key, slug=key, entity_type="background",
        data_json=data or {}, summary="", source_document=source,
        game_system_key="5e-2024" if source == "srd-2024" else "5e-2014",
    )


def test_2024_level_xp_thresholds_cover_character_levels():
    assert LEVEL_XP[1] == 0
    assert LEVEL_XP[5] == 6500
    assert LEVEL_XP[10] == 64000
    assert LEVEL_XP[20] == 355000


def test_background_fallback_grants_skills_and_tool():
    row = background()
    assert background_skills(row) == ["Insight", "Religion"]
    assert "Calligrapher's Supplies" in background_other_proficiencies(row)


def test_background_template_marks_grants_read_only_and_source_specific():
    html = Path("app/templates/character_steps/background.html").read_text()
    assert 'value="{{ entity.public_id }}"' in html
    assert 'data-skills=' in html
    assert 'data-proficiencies=' in html
    assert 'class="grant-lock"' in html
    assert 'disabled' in html


def test_live_rail_is_single_right_side_component_with_stats():
    rail = Path("app/templates/character_ability_rail.html").read_text()
    assert "LIVE STATS" in rail
    assert 'data-live-stat="hp"' in rail
    assert 'data-live-stat="ac"' in rail
    assert 'data-live-stat="pb"' in rail
    assert "LIVE ABILITIES" in rail
    stage = Path("app/templates/character_stage_response.html").read_text()
    assert "character_ability_rail.html" not in stage
    assert "data-character-live-state" in stage


def test_identity_and_background_client_behaviors_are_present():
    js = Path("app/static/js/app.js").read_text()
    assert "initIdentityBuilder" in js
    assert "levelForXp" in js
    assert "text.length > 220" in js
    assert "background-granted" in js
    css = Path("app/static/css/app.css").read_text()
    assert ".background-token-columns" in css
    assert "overflow-x:hidden" in css
