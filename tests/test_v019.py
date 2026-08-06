from pathlib import Path

def test_auth_and_list_implementation_files_exist():
    assert Path("app/auth.py").exists()
    assert Path("app/user_routes.py").exists()
    text=Path("app/models.py").read_text()
    assert "class User(Base)" in text
    assert "class UserEntityList(Base)" in text
    assert "class UserEntityListItem(Base)" in text


def test_public_and_role_gated_navigation():
    base=Path("app/templates/base.html").read_text()
    assert "request.state.user.role == 'administrator'" in base
    assert 'href="/lists"' in base
    assert 'href="/login"' in base


def test_entity_detail_permissions_and_list_dialog():
    detail=Path("app/templates/entity_detail.html").read_text()
    assert "can_view_json" in detail
    assert "can_upload_artwork" in detail
    assert "add-to-list-dialog" in detail
    assert "/lists/add" in detail


def test_default_admin_environment_settings():
    config=Path("app/config.py").read_text()
    assert "default_admin_password" in config
    assert "session_cookie_name" in config
