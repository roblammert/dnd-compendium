from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Entity
from app.character_services import equipment_print_columns

PRINT = Path("app/templates/character_print.html").read_text()


def _entity(entity_type, name, slug, data, *, source="srd-2024", system="5e-2024"):
    return Entity(
        public_id=f"ent-{entity_type}-{slug}",
        entity_type=entity_type,
        name=name,
        slug=slug,
        canonical_key=slug.replace("-2", ""),
        source_kind="open5e",
        source_document=source,
        source_display_name="5e 2024 Rules" if source == "srd-2024" else source,
        game_system_key=system,
        game_system_name="5th Edition 2024" if system == "5e-2024" else system,
        data_json=data,
        is_active=True,
    )


def test_print_moves_proficiencies_below_at_a_glance_and_removes_inventory_note():
    assert PRINT.index("Proficiencies") < PRINT.index("Skill Proficiencies") < PRINT.index("Saving Throw Proficiencies") < PRINT.index("At-a-Glance Features")
    detail = PRINT[PRINT.index("Inventory & Character Traits"):]
    assert "Currency is summarized on the core page" not in detail


def test_equipment_print_is_three_item_type_weight_groups_with_gutters():
    assert 'class="inventory-table triple-equipment"' in PRINT
    assert PRINT.count('<th>Weight</th>') == 3
    assert PRINT.count('<th>Item</th>') >= 3
    assert PRINT.count('<th>Type</th>') >= 3
    assert PRINT.count('class="gutter"') >= 2


def test_three_group_equipment_rows_include_blank_play_rows_and_weapon_item_weight_fallback():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    weapon = _entity("weapon", "Battleaxe", "battleaxe-2", {"name": "Battleaxe"}, source="srd-2014", system="5e-2014")
    item = _entity("item", "Battleaxe", "battleaxe-2", {"name": "Battleaxe", "weight": "4.000"}, source="srd-2014", system="5e-2014")
    with Session(engine) as db:
        db.add_all([weapon, item]); db.commit()
        rows = equipment_print_columns(db, [weapon], groups=3, minimum_rows=8)
        assert len(rows) == 8
        assert len(rows[0]) == 3
        assert rows[0][0]["weight"] == "4.0 lb."
        assert rows[-1][2] == {"name": "", "type": "", "value": "", "weight": ""}


def test_spell_level_boxes_have_ten_cantrip_height_lines():
    assert 'for _ in range(10)' in PRINT
    assert '.write-line { border-bottom:1px dotted #b9a77f; min-height:0; flex:1 1 0;' in PRINT
