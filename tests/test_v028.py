from types import SimpleNamespace
from app.main import templates
from app.tools_routes import XP_THRESHOLDS, _number


def test_coin_converter_template_has_all_coin_types():
    html = templates.get_template('tools_coin_converter.html').render(tools_section='coin-converter')
    for label in ('Platinum (PP)', 'Gold (GP)', 'Silver (SP)', 'Copper (CP)'):
        assert label in html


def test_encounter_threshold_example_matches_specification():
    assert XP_THRESHOLDS[5][2] * 5 == 3750
    assert XP_THRESHOLDS[5][1] * 5 == 2500


def test_fractional_challenge_rating_parser():
    assert _number('1/4') == 0.25
    assert _number({'value': '1/2'}) == 0.5


def test_profile_template_contains_preferred_source_selector():
    user = SimpleNamespace(
        username='rob', display_name='Rob', email='', role='user',
        preferred_source_document='srd-2024', token_asset=None,
    )
    request = SimpleNamespace(query_params={}, state=SimpleNamespace(user=user))
    html = templates.get_template('profile.html').render(
        request=request, profile_user=user,
        preferred_sources=[{'key':'srd-2014','name':'5e 2014 Rules'},{'key':'srd-2024','name':'5e 2024 Rules'}],
    )
    assert 'name="preferred_source_document"' in html
    assert 'value="srd-2024" selected' in html
