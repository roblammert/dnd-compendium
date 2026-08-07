from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_feat_evaluator_has_client_side_hide_blocked_toggle():
    template = (ROOT / "app/templates/tools_feat_evaluator.html").read_text()
    script = (ROOT / "app/static/js/app.js").read_text()
    css = (ROOT / "app/static/css/app.css").read_text()
    assert "data-hide-blocked" in template
    assert "data-feat-grid" in template
    assert 'classList.toggle("hide-blocked"' in script
    assert ".feat-grid.hide-blocked .feat-evaluation-card.ineligible" in css


def test_weapon_evaluator_is_renamed_and_has_game_system_filter():
    template = (ROOT / "app/templates/tools_weapon_evaluator.html").read_text()
    layout = (ROOT / "app/templates/tools_layout.html").read_text()
    routes = (ROOT / "app/tools_routes.py").read_text()
    assert "<h1>Weapons Evaluator</h1>" in template
    assert ">Weapons Evaluator</a>" in layout
    assert 'select name="game_system"' in template
    assert 'game_system: str = ""' in routes
    assert "game_systems=game_systems" in routes
    assert "chosen=[w for w in all_weapons" in routes
