from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class EntityCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    source_document: str | None = "homebrew"
    data: dict[str, Any] = Field(default_factory=dict)

class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = None
    data: dict[str, Any] | None = None
    is_active: bool | None = None

class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: str
    entity_type: str
    name: str
    slug: str
    source_kind: str
    source_document: str | None
    source_display_name: str | None = None
    game_system_key: str | None = None
    game_system_name: str | None = None
    is_homebrew: bool
    is_active: bool
    summary: str | None
    data_json: dict[str, Any]
