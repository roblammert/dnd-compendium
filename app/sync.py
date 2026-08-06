from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from urllib.parse import urljoin
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Entity, SyncRun
from app.services import canonical_checksum, ensure_unique_slug, public_id, rebuild_search_row

settings = get_settings()

def normalize(endpoint: str, raw: dict) -> dict:
    name = raw.get("name") or raw.get("title") or raw.get("slug") or "Unnamed"
    upstream_id = str(raw.get("slug") or raw.get("key") or raw.get("id") or name)
    return {
      "entity_type": endpoint.rstrip("s"), "name": name,
      "upstream_id": upstream_id, "source_document": raw.get("document__slug") or raw.get("document") or raw.get("source"),
      "summary": raw.get("desc") or raw.get("description") or raw.get("short_desc"), "data": raw,
      "upstream_url": raw.get("url") or raw.get("document__url")
    }

async def fetch_endpoint(client: httpx.AsyncClient, endpoint: str):
    url = f"{settings.open5e_base_url.rstrip('/')}/v1/{endpoint}/"
    while url:
        response = await client.get(url, params={"limit": settings.open5e_page_size} if "?" not in url else None)
        response.raise_for_status(); payload = response.json()
        results = payload.get("results", payload if isinstance(payload, list) else [])
        for item in results: yield item
        next_url = payload.get("next") if isinstance(payload, dict) else None
        url = urljoin(url, next_url) if next_url else None

async def sync_open5e(db: Session, endpoints: list[str] | None = None) -> SyncRun:
    run = SyncRun(); db.add(run); db.commit(); db.refresh(run)
    seen: set[tuple[str,str]] = set()
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            for endpoint in endpoints or settings.endpoint_names:
                async for raw in fetch_endpoint(client, endpoint):
                    n = normalize(endpoint, raw); run.records_seen += 1
                    key=(n["entity_type"], n["upstream_id"]); seen.add(key)
                    checksum=canonical_checksum(n["data"])
                    entity=db.scalar(select(Entity).where(Entity.source_kind=="open5e", Entity.entity_type==n["entity_type"], Entity.upstream_id==n["upstream_id"]))
                    if entity is None:
                        entity=Entity(public_id=public_id(), entity_type=n["entity_type"], name=n["name"],
                          slug=ensure_unique_slug(db,n["entity_type"],n["name"]), source_kind="open5e",
                          source_document=n["source_document"], upstream_id=n["upstream_id"], upstream_url=n["upstream_url"],
                          upstream_checksum=checksum, summary=n["summary"], data_json=n["data"], synced_at=datetime.now(timezone.utc))
                        db.add(entity); db.flush(); run.records_created += 1; rebuild_search_row(db,entity)
                    elif entity.upstream_checksum != checksum:
                        entity.name=n["name"]; entity.source_document=n["source_document"]; entity.upstream_url=n["upstream_url"]
                        entity.upstream_checksum=checksum; entity.summary=n["summary"]; entity.data_json=n["data"]
                        entity.synced_at=datetime.now(timezone.utc); entity.is_active=True; entity.is_deleted_upstream=False
                        run.records_updated += 1; db.flush(); rebuild_search_row(db,entity)
                    if run.records_seen % 100 == 0: db.commit()
        run.status="completed"; run.completed_at=datetime.now(timezone.utc); db.commit(); db.refresh(run); return run
    except Exception as exc:
        db.rollback(); run=db.get(SyncRun,run.id); run.status="failed"; run.error_message=str(exc); run.completed_at=datetime.now(timezone.utc); db.commit(); raise
