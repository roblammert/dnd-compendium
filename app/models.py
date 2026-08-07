from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.db import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("source_kind", "entity_type", "upstream_id", name="uq_upstream_entity"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), index=True)
    canonical_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_kind: Mapped[str] = mapped_column(String(40), index=True)
    source_document: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    game_system_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    game_system_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    upstream_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upstream_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    upstream_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_homebrew: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deleted_upstream: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assets: Mapped[list[EntityAsset]] = relationship(back_populates="entity", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    storage_name: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class EntityAsset(Base):
    __tablename__ = "entity_assets"
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(40), primary_key=True, default="portrait")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    entity: Mapped[Entity] = relationship(back_populates="assets")
    asset: Mapped[Asset] = relationship()

class LexiconTerm(Base):
    __tablename__ = "lexicon_terms"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_term: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_term: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EntityTypeVisibility(Base):
    __tablename__ = "entity_type_visibility"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    minimum_role: Mapped[str] = mapped_column(String(30), default="user", index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class SyncRun(Base):
    __tablename__ = "sync_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), default="open5e")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="running")
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0)
    records_archived: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    endpoints: Mapped[list["SyncEndpoint"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="SyncEndpoint.id"
    )

class SyncEndpoint(Base):
    __tablename__ = "sync_endpoints"
    __table_args__ = (
        UniqueConstraint("sync_run_id", "endpoint", name="uq_sync_run_endpoint"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    sync_run_id: Mapped[int] = mapped_column(ForeignKey("sync_runs.id", ondelete="CASCADE"), index=True)
    endpoint: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    records_seen: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run: Mapped[SyncRun] = relationship(back_populates="endpoints")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    token_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    preferred_source_document: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    token_asset: Mapped[Asset | None] = relationship(foreign_keys=[token_asset_id])
    lists: Mapped[list["UserEntityList"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class UserEntityList(Base):
    __tablename__ = "user_entity_lists"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sort_mode: Mapped[str] = mapped_column(String(30), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    owner: Mapped[User] = relationship(back_populates="lists")
    items: Mapped[list["UserEntityListItem"]] = relationship(back_populates="entity_list", cascade="all, delete-orphan", order_by="UserEntityListItem.position")

class UserEntityListItem(Base):
    __tablename__ = "user_entity_list_items"
    __table_args__ = (UniqueConstraint("list_id", "entity_type", "canonical_key", name="uq_list_canonical_entity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("user_entity_lists.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    canonical_key: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    entity_list: Mapped[UserEntityList] = relationship(back_populates="items")
    entity: Mapped[Entity] = relationship()
