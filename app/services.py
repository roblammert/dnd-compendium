from __future__ import annotations
import hashlib, json, re, uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.models import Entity

def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or uuid.uuid4().hex[:12]

def public_id(prefix: str = "ent") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"

def canonical_checksum(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

def flatten_text(value: Any) -> str:
    if value is None: return ""
    if isinstance(value, dict): return " ".join(flatten_text(v) for v in value.values())
    if isinstance(value, list): return " ".join(flatten_text(v) for v in value)
    return str(value)

def ensure_unique_slug(db: Session, entity_type: str, desired: str, exclude_id: int | None = None) -> str:
    base = slugify(desired); candidate = base; n = 2
    while True:
        q = select(Entity.id).where(Entity.entity_type == entity_type, Entity.slug == candidate)
        if exclude_id: q = q.where(Entity.id != exclude_id)
        if db.scalar(q) is None: return candidate
        candidate = f"{base}-{n}"; n += 1

def rebuild_search_row(db: Session, entity: Entity) -> None:
    db.execute(text("DELETE FROM entity_search WHERE entity_id=:id"), {"id": entity.id})
    body = flatten_text(entity.data_json)
    db.execute(text("""
      INSERT INTO entity_search(entity_id,name,entity_type,source_document,summary,body)
      VALUES(:id,:name,:type,:source,:summary,:body)
    """), {"id": entity.id, "name": entity.name, "type": entity.entity_type,
           "source": entity.source_document or "", "summary": entity.summary or "", "body": body})

def init_search(db: Session) -> None:
    db.execute(text("""CREATE VIRTUAL TABLE IF NOT EXISTS entity_search USING fts5(
      entity_id UNINDEXED, name, entity_type, source_document, summary, body,
      tokenize='unicode61 remove_diacritics 2'
    )"""))
    db.commit()

def create_homebrew(db: Session, payload) -> Entity:
    entity = Entity(public_id=public_id(), entity_type=payload.entity_type,
        name=payload.name, slug=ensure_unique_slug(db, payload.entity_type, payload.name),
        source_kind="homebrew", source_document=payload.source_document or "homebrew",
        is_homebrew=True, summary=payload.summary, data_json=payload.data)
    db.add(entity); db.flush(); rebuild_search_row(db, entity); db.commit(); db.refresh(entity)
    return entity
