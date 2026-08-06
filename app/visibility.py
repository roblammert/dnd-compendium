from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth import ROLE_RANK
from app.models import Entity, EntityTypeVisibility, User

VIEW_LEVELS = {"user": 0, "editor": 20, "administrator": 30, "invisible": 999}
VIEW_LABELS = {"user": "Users", "editor": "Editors", "administrator": "Administrators", "invisible": "INVISIBLE"}

def visibility_map(db: Session) -> dict[str, str]:
    return {row.entity_type: row.minimum_role for row in db.scalars(select(EntityTypeVisibility)).all()}

def ensure_visibility_rows(db: Session) -> None:
    existing = visibility_map(db)
    types = db.scalars(select(Entity.entity_type).distinct()).all()
    changed = False
    for entity_type in types:
        if entity_type not in existing:
            db.add(EntityTypeVisibility(entity_type=entity_type, minimum_role="user")); changed = True
    if changed: db.commit()

def can_view_type(user: User | None, entity_type: str, mapping: dict[str,str]) -> bool:
    level = mapping.get(entity_type, "user")
    if level == "invisible": return False
    if level == "user": return True
    return bool(user and user.is_active and ROLE_RANK.get(user.role, 0) >= VIEW_LEVELS[level])

def visible_types(db: Session, user: User | None) -> set[str]:
    mapping = visibility_map(db)
    types = set(db.scalars(select(Entity.entity_type).distinct()).all())
    return {t for t in types if can_view_type(user, t, mapping)}
