from pathlib import Path

from app.tools_routes import _structured_markdown, templates

ROOT = Path(__file__).resolve().parents[1]


def test_structured_feat_descriptions_become_markdown():
    value = [
        {"desc": "Gain **advantage** on checks."},
        {"name": "Table", "desc": "| Roll | Result |\n|---|---|\n| 1 | Success |"},
    ]
    rendered = _structured_markdown(value)
    assert "**advantage**" in rendered
    assert "| Roll | Result |" in rendered
    assert "**Table.**" in rendered


def test_tools_environment_renders_markdown_tables_and_emphasis():
    html = str(templates.env.filters["render_markdown"]("**Bold**\n\n| A | B |\n|---|---|\n| 1 | 2 |"))
    assert "<strong>Bold</strong>" in html
    assert "<table>" in html


def test_loadout_toggle_labels_are_wrapped_for_layout():
    template = (ROOT / "app/templates/tools_loadout_generator.html").read_text()
    assert "<span>Weapons</span>" in template
    assert "<span>Equipment and items</span>" in template


def test_every_tools_cost_cell_uses_accessible_conversion_tooltip():
    for name in (
        "tools_loadout_generator.html",
        "tools_loot_generator.html",
        "tools_weapon_evaluator.html",
    ):
        template = (ROOT / "app/templates" / name).read_text()
        assert 'class="cost-tooltip" tabindex="0"' in template
        assert 'title="{{ row.cost_tooltip }}"' in template
