from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db import Base
from app.models import Entity, EntityTypeVisibility, User
from app.visibility import can_view_type, ensure_visibility_rows, visible_types

def test_visibility_defaults_and_role_rules():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Entity(public_id="e1",entity_type="monster",name="Goblin",slug="goblin",canonical_key="goblin",source_kind="open5e",data_json={}))
        db.commit(); ensure_visibility_rows(db)
        row=db.scalar(select(EntityTypeVisibility).where(EntityTypeVisibility.entity_type=="monster"))
        assert row.minimum_role=="user"
        assert "monster" in visible_types(db,None)
        row.minimum_role="editor"; db.commit()
        assert "monster" not in visible_types(db,None)
        editor=User(public_id="u1",username="ed",display_name="Ed",password_hash="x",role="editor",is_active=True)
        assert can_view_type(editor,"monster",{"monster":"editor"})
        row.minimum_role="invisible"; db.commit()
        assert "monster" not in visible_types(db,editor)

def test_patch_policy_and_docs_exist():
    assert Path("RELEASE_NOTES.md").exists()
    readme=Path("README.md").read_text()
    assert "## Quick start with Docker" in readme
    assert "View Management" in readme
