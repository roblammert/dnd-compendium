from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Entity
from app.character_services import equipment_print_columns

PRINT = Path("app/templates/character_print.html").read_text()


def _entity(entity_type, name, slug, data, *, source="srd-2024", system="5e-2024"):
    return Entity(
        public_id=f"ent-{entity_type}-{slug}", entity_type=entity_type, name=name,
        slug=slug, canonical_key=slug.replace("-2", ""), source_kind="open5e",
        source_document=source, source_display_name="5e 2024 Rules",
        game_system_key=system, game_system_name="5th Edition 2024",
        data_json=data, is_active=True,
    )


def test_currency_is_after_at_a_glance_in_right_reference_column():
    attacks = PRINT.index("Attacks & Spellcasting")
    glance = PRINT.index('>At-a-Glance Features</h2>')
    currency = PRINT.index('<span>Currency</span>')
    assert attacks < glance < currency
    assert PRINT.count('<span>Currency</span>') == 1


def test_proficiency_panels_are_directly_before_at_a_glance_and_features_use_two_columns():
    prof = PRINT.index('>Proficiencies</h2>')
    skills = PRINT.index('>Skill Proficiencies</h2>')
    saves = PRINT.index('>Saving Throw Proficiencies</h2>')
    glance = PRINT.index('>At-a-Glance Features</h2>')
    assert prof < skills < saves < glance
    assert 'class="clean-list feature-list-two"' in PRINT
    assert '.feature-list-two { columns:2;' in PRINT


def test_equipment_print_has_three_item_type_value_weight_groups():
    assert PRINT.count('<th>Item</th>') >= 3
    assert PRINT.count('<th>Type</th>') >= 3
    assert PRINT.count('<th>Value</th>') == 3
    assert PRINT.count('<th>Weight</th>') == 3
    assert 'col class="value"' in PRINT
    assert 'class="value">{{ item.value }}' in PRINT


def test_equipment_blank_rows_keep_value_and_same_row_height_and_weapon_cost_fallback():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    weapon = _entity("weapon", "Battleaxe", "battleaxe-2", {"name": "Battleaxe"}, source="srd-2014", system="5e-2014")
    item = _entity("item", "Battleaxe", "battleaxe-2", {"name": "Battleaxe", "cost": "10.00", "weight": "4.000"}, source="srd-2014", system="5e-2014")
    with Session(engine) as db:
        db.add_all([weapon, item]); db.commit()
        rows = equipment_print_columns(db, [weapon], groups=3, minimum_rows=8)
        assert rows[0][0]["value"] not in {"", "—"}
        assert rows[0][0]["weight"] == "4.0 lb."
        assert rows[-1][2] == {"name": "", "type": "", "value": "", "weight": ""}
    assert 'tbody tr { height:18px; }' in PRINT
