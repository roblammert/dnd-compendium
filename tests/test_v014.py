from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def test_home_uses_lexicon_display_rows():
    template = (Path(__file__).parents[1] / "app" / "templates" / "home.html").read_text()
    assert "count_rows" in template
    assert "row.label" in template


def test_browse_collapses_multiple_sources_and_systems():
    template = (Path(__file__).parents[1] / "app" / "templates" / "fragments" / "results.html").read_text()
    assert "group.source_count > 1" in template
    assert "group.system_count > 1" in template
    assert "{{ group.source_count }} sources" in template
    assert "{{ group.system_count }} systems" in template


def test_footer_has_version_and_open5e_compatibility():
    template_dir = Path(__file__).parents[1] / "app" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("base.html")
    rendered = template.render(app_version="0.14.0", app_name="D&D Compendium")
    assert "D&D Compendium v0.14.0" in rendered
    assert "Open5e Compatible" in rendered


def test_type_column_has_minimum_width():
    css = (Path(__file__).parents[1] / "app" / "static" / "css" / "app.css").read_text()
    assert ".compendium-table th:nth-child(2)" in css
    assert "min-width:9.5rem" in css
