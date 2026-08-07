from pathlib import Path


def test_character_step_forms_have_progressive_post_fallbacks():
    root = Path(__file__).parents[1]
    steps = ("identity", "species", "class", "abilities", "background", "gear", "spells", "details", "review")
    for step in steps:
        text = (root / f"app/templates/character_steps/{step}.html").read_text()
        assert 'method="post"' in text
        assert f'action="/tools/character-builder/{{{{ character.public_id }}}}/step/{step}"' in text
        assert f'hx-post="/tools/character-builder/{{{{ character.public_id }}}}/step/{step}"' in text


def test_character_fragment_route_redirects_non_htmx_requests_to_shell():
    root = Path(__file__).parents[1]
    routes = (root / "app/character_routes.py").read_text()
    assert 'if request.headers.get("HX-Request") != "true":' in routes
    assert 'RedirectResponse(f"/tools/character-builder/{row.public_id}?step={step}", 303)' in routes


def test_static_assets_are_version_cache_busted():
    root = Path(__file__).parents[1]
    base = (root / "app/templates/base.html").read_text()
    assert '/static/css/app.css?v={{ app_version }}' in base
    assert '/static/vendor/htmx.min.js?v={{ app_version }}' in base
    assert '/static/js/app.js?v={{ app_version }}' in base


def test_identity_save_continue_targets_species():
    root = Path(__file__).parents[1]
    identity = (root / "app/templates/character_steps/identity.html").read_text()
    assert 'name="next_step" value="species"' in identity
