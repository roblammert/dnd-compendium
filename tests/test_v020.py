from pathlib import Path


def test_homebrew_requires_editor_and_navigation_matches():
    main = Path("app/main.py").read_text()
    base = Path("app/templates/base.html").read_text()
    assert "Depends(require_editor)" in main
    assert "request.state.user.role in ['editor','administrator']" in base


def test_profile_and_drag_drop_list_ui():
    profile = Path("app/templates/profile.html").read_text()
    list_detail = Path("app/templates/list_detail.html").read_text()
    script = Path("app/static/js/app.js").read_text()
    assert "profile-identity-card" in profile
    assert "data-sortable-list" in list_detail
    assert "data-item-order" in list_detail
    assert "dragstart" in script and "dragover" in script


def test_add_to_list_new_fields_toggle_and_duplicate_notice():
    detail = Path("app/templates/entity_detail.html").read_text()
    routes = Path("app/user_routes.py").read_text()
    script = Path("app/static/js/app.js").read_text()
    assert "data-list-destination" in detail
    assert "data-new-list-fields" in detail
    assert "already_added" in routes
    assert "updateNewListVisibility" in script


def test_user_router_has_footer_version():
    routes = Path("app/user_routes.py").read_text()
    assert 'templates.env.globals["app_version"] = ' in routes
