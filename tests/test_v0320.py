from pathlib import Path


def test_v0320_print_sheet_is_full_rework():
    template = Path("app/templates/character_print.html").read_text()
    assert 'class="combat-ribbon"' in template
    assert 'class="ability-board"' in template
    assert 'skill.ability == save.ability' in template
    assert 'Inventory & Character Traits' in template
    assert 'Character & Story' in template
    assert '{% if derived.spellcasting_ability or derived.spells %}' in template
    assert 'Generated with Rob\'s D&amp;D Compendium - {{ app_version }} - {{ generated_date }}' in template


def test_v0320_print_sheet_has_overflow_safe_paged_css():
    template = Path("app/templates/character_print.html").read_text()
    assert 'break-inside:avoid-page' in template
    assert 'page-break-inside:avoid' in template
    assert 'display:table-header-group' in template
    assert '@bottom-left' in template and '@bottom-right' in template
    assert '.story-content { white-space:pre-wrap; overflow-wrap:anywhere;' in template
    assert '.flow-block { break-inside:auto; page-break-inside:auto; }' in template


def test_v0320_routes_supply_version_and_generation_date():
    routes = Path("app/character_routes.py").read_text()
    assert 'date.today().strftime("%Y%m%d")' in routes
    assert 'app_version=request.app.version' in routes
