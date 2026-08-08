from pathlib import Path

ROUTES = Path("app/player_architect_routes.py").read_text()


def test_pa_class_catalog_uses_classe_endpoint():
    section = ROUTES.split("def _class_catalog", 1)[1].split("def _extract_named", 1)[0]
    assert '_all_entities(db, ["classe"])' in section
    assert '_all_entities(db, ["class"])' not in section


def test_pa_subclass_rule_matches_sqlite_json_type_semantics():
    section = ROUTES.split("def _class_catalog", 1)[1].split("def _extract_named", 1)[0]
    assert '"subclass_of" in data' in section
    assert 'data.get("subclass_of") is not None' in section
    assert "entity_type = 'classe'" in section


def test_pa_version_0333():
    assert Path("app/version.py").read_text().strip() == 'APP_VERSION = "0.33.7"'
