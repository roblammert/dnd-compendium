from pathlib import Path


def test_feat_hide_toggle_is_compact():
    template = Path("app/templates/tools_feat_evaluator.html").read_text()
    css = Path("app/static/css/app.css").read_text()
    assert 'class="inline-tool-toggle"' in template
    assert 'width:auto' in css
    assert 'input[type="checkbox"]' in css


def test_weapon_game_system_filter_is_client_side():
    template = Path("app/templates/tools_weapon_evaluator.html").read_text()
    script = Path("app/static/js/app.js").read_text()
    routes = Path("app/tools_routes.py").read_text()
    assert "data-weapon-system-filter" in template
    assert "data-game-system" in template
    assert 'addEventListener("change", filterWeapons)' in script
    assert 'choice.hidden = !show' in script
    assert "weapons=all_weapons" in routes
