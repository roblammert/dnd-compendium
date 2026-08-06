from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, AsyncIterator
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Entity, SyncEndpoint, SyncRun
from app.services import canonical_checksum, canonical_entity_key, ensure_unique_slug, public_id, rebuild_search_row

settings = get_settings()

ENTITY_TYPE_MAP = {
    "creatures": "monster",
    "magicitems": "magicitem",
    "magic-items": "magicitem",
    "species": "species",
}

FALLBACK_ENDPOINTS = (
    "backgrounds", "classes", "conditions", "creatures", "documents",
    "equipment", "feats", "magicitems", "rules", "sections", "species",
    "spells", "weapons", "armor",
)

ACTIVE_SYNC_STATUSES = ("queued", "running")
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def entity_type_for_endpoint(endpoint: str) -> str:
    return ENTITY_TYPE_MAP.get(endpoint, endpoint[:-1] if endpoint.endswith("s") else endpoint)


def add_limit(url: str, limit: int) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["limit"] = str(limit)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def endpoint_name_from_url(url: str) -> str:
    return urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]


def first_text(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, (str, int, float)):
            return str(value)
    return None


def document_values(raw: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Return document key, name, display name, game-system key and game-system name."""
    document = raw.get("document")
    if isinstance(document, dict):
        gamesystem = document.get("gamesystem") if isinstance(document.get("gamesystem"), dict) else {}
        return (
            first_text(document, "key", "slug", "id"),
            first_text(document, "name", "title"),
            first_text(document, "display_name", "name", "title"),
            first_text(gamesystem, "key", "slug", "id"),
            first_text(gamesystem, "name", "display_name", "title"),
        )
    if isinstance(document, (str, int, float)):
        value = str(document)
        return value, value, value, None, None
    return (
        first_text(raw, "document__key", "document__slug"),
        first_text(raw, "document__name", "source"),
        first_text(raw, "document__display_name", "document__name", "source"),
        first_text(raw, "document__gamesystem__key"),
        first_text(raw, "document__gamesystem__name"),
    )


def record_identity(raw: dict[str, Any]) -> str:
    document_key, _, _, _, _ = document_values(raw)
    key = first_text(raw, "key", "slug", "id", "pk", "index")
    if key and document_key:
        return f"{document_key}:{key}"
    return key or canonical_checksum(raw)


def normalize(endpoint: str, raw: dict[str, Any]) -> dict[str, Any]:
    name = first_text(raw, "name", "title", "slug", "key") or "Unnamed"
    document_key, document_name, source_display_name, game_system_key, game_system_name = document_values(raw)
    return {
        "entity_type": entity_type_for_endpoint(endpoint),
        "name": name,
        "canonical_key": canonical_entity_key(entity_type_for_endpoint(endpoint), name),
        "upstream_id": record_identity(raw),
        "source_document": document_key or document_name,
        "source_display_name": source_display_name or document_name or document_key,
        "game_system_key": game_system_key,
        "game_system_name": game_system_name,
        "summary": first_text(raw, "desc", "description", "short_desc"),
        "data": raw,
        "upstream_url": first_text(raw, "url", "document__url"),
    }


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0.0, (parsed - utc_now()).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def _backoff_seconds(attempt: int, response: httpx.Response | None = None) -> float:
    retry_after = _retry_after_seconds(response) if response is not None else None
    if retry_after is not None:
        return min(retry_after, settings.open5e_retry_max_delay)
    exponential = settings.open5e_retry_base_delay * (2 ** attempt)
    return min(exponential, settings.open5e_retry_max_delay)


async def request_json(client: httpx.AsyncClient, url: str) -> Any:
    """Request one Open5e page with bounded retries and respectful throttling."""
    last_error: Exception | None = None
    for attempt in range(settings.open5e_retry_attempts + 1):
        response: httpx.Response | None = None
        try:
            response = await client.get(url)
            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt >= settings.open5e_retry_attempts:
                    response.raise_for_status()
                await asyncio.sleep(_backoff_seconds(attempt, response))
                continue
            response.raise_for_status()
            payload = response.json()
            if settings.open5e_request_delay > 0:
                await asyncio.sleep(settings.open5e_request_delay)
            return payload
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt >= settings.open5e_retry_attempts:
                raise
            await asyncio.sleep(_backoff_seconds(attempt, response))
        except ValueError:
            # Invalid JSON should not be retried endlessly; surface it immediately.
            raise
    if last_error:
        raise last_error
    raise RuntimeError(f"Open5e request failed without an error: {url}")


async def discover_endpoints(client: httpx.AsyncClient) -> dict[str, str]:
    api_root = settings.open5e_api_root.rstrip("/") + "/"
    try:
        root = await request_json(client, api_root)
    except (httpx.HTTPError, ValueError):
        return {name: urljoin(api_root, f"{name}/") for name in FALLBACK_ENDPOINTS}

    discovered: dict[str, str] = {}
    if isinstance(root, dict):
        for key, value in root.items():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                name = endpoint_name_from_url(value) or str(key)
                if name != "search":
                    discovered[name] = value
    return dict(sorted(discovered.items())) if discovered else {
        name: urljoin(api_root, f"{name}/") for name in FALLBACK_ENDPOINTS
    }


async def fetch_endpoint_pages(
    client: httpx.AsyncClient, url: str
) -> AsyncIterator[tuple[int, list[dict[str, Any]]]]:
    """Yield exactly one API page at a time, never prefetching concurrent pages."""
    next_url: str | None = add_limit(url, settings.open5e_page_size)
    page_number = 0
    while next_url:
        page_number += 1
        payload = await request_json(client, next_url)
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            raw_results = payload["results"]
            next_value = payload.get("next")
            following_url = urljoin(next_url, next_value) if next_value else None
        elif isinstance(payload, list):
            raw_results = payload
            following_url = None
        else:
            raise ValueError(f"Unexpected Open5e response shape from {next_url}")
        results = [item for item in raw_results if isinstance(item, dict)]
        yield page_number, results
        next_url = following_url


async def fetch_endpoint(client: httpx.AsyncClient, url: str) -> AsyncIterator[dict[str, Any]]:
    """Compatibility iterator used by callers/tests that want individual records."""
    async for _, page in fetch_endpoint_pages(client, url):
        for item in page:
            yield item


def create_sync_run(db: Session) -> tuple[SyncRun, bool]:
    active = db.scalar(
        select(SyncRun).where(SyncRun.provider == "open5e", SyncRun.status.in_(ACTIVE_SYNC_STATUSES))
        .order_by(SyncRun.id.desc())
    )
    if active:
        return active, False
    run = SyncRun(provider="open5e", status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run, True


def recover_interrupted_syncs(db: Session) -> int:
    """Mark jobs left active by an application restart as failed."""
    runs = db.scalars(select(SyncRun).where(SyncRun.status.in_(ACTIVE_SYNC_STATUSES))).all()
    now = utc_now()
    for run in runs:
        run.status = "failed"
        run.error_message = "Application restarted while this synchronization was active."
        run.completed_at = now
        for item in run.endpoints:
            if item.status in ("pending", "running"):
                item.status = "failed"
                item.error_message = "Interrupted by application restart."
                item.completed_at = now
    if runs:
        db.commit()
    return len(runs)



def _mark_endpoint_running(db: Session, run_id: int, endpoint_id: int) -> None:
    """Atomically enforce that only one endpoint row is marked running."""
    db.execute(
        update(SyncEndpoint)
        .where(
            SyncEndpoint.sync_run_id == run_id,
            SyncEndpoint.status == "running",
            SyncEndpoint.id != endpoint_id,
        )
        .values(status="pending", started_at=None)
    )
    progress = db.get(SyncEndpoint, endpoint_id)
    if progress is None:
        raise RuntimeError(f"Sync endpoint {endpoint_id} no longer exists")
    progress.status = "running"
    progress.started_at = utc_now()
    progress.completed_at = None
    progress.error_message = None
    db.commit()

def _mark_endpoint_finished(
    db: Session, endpoint_id: int, status: str, error_message: str | None = None
) -> None:
    """Persist a terminal endpoint state without relying on stale ORM objects."""
    db.execute(
        update(SyncEndpoint)
        .where(SyncEndpoint.id == endpoint_id)
        .values(
            status=status,
            completed_at=utc_now(),
            error_message=error_message,
        )
    )
    db.commit()


def _refresh_run_totals(db: Session, run: SyncRun) -> None:
    """Aggregate counters without refreshing away unflushed run status changes."""
    totals = db.execute(
        select(
            func.coalesce(func.sum(SyncEndpoint.records_seen), 0),
            func.coalesce(func.sum(SyncEndpoint.records_created), 0),
            func.coalesce(func.sum(SyncEndpoint.records_updated), 0),
            func.coalesce(func.sum(SyncEndpoint.records_unchanged), 0),
        ).where(SyncEndpoint.sync_run_id == run.id)
    ).one()
    run.records_seen = int(totals[0] or 0)
    run.records_created = int(totals[1] or 0)
    run.records_updated = int(totals[2] or 0)
    run.records_unchanged = int(totals[3] or 0)


def _upsert_record(db: Session, progress: SyncEndpoint, endpoint_name: str, raw: dict[str, Any]) -> None:
    normalized = normalize(endpoint_name, raw)
    progress.records_seen += 1
    checksum = canonical_checksum(normalized["data"])
    entity = db.scalar(select(Entity).where(
        Entity.source_kind == "open5e",
        Entity.entity_type == normalized["entity_type"],
        Entity.upstream_id == normalized["upstream_id"],
    ))
    if entity is None:
        entity = Entity(
            public_id=public_id(), entity_type=normalized["entity_type"],
            name=normalized["name"],
            slug=ensure_unique_slug(db, normalized["entity_type"], normalized["name"]),
            canonical_key=normalized["canonical_key"],
            source_kind="open5e", source_document=normalized["source_document"],
            source_display_name=normalized["source_display_name"],
            game_system_key=normalized["game_system_key"],
            game_system_name=normalized["game_system_name"],
            upstream_id=normalized["upstream_id"], upstream_url=normalized["upstream_url"],
            upstream_checksum=checksum, summary=normalized["summary"],
            data_json=normalized["data"], synced_at=utc_now(),
        )
        db.add(entity)
        db.flush()
        progress.records_created += 1
        rebuild_search_row(db, entity)
    elif (
        entity.upstream_checksum != checksum
        or entity.source_display_name != normalized["source_display_name"]
        or entity.game_system_name != normalized["game_system_name"]
        or entity.canonical_key != normalized["canonical_key"]
    ):
        entity.name = normalized["name"]
        entity.canonical_key = normalized["canonical_key"]
        entity.source_document = normalized["source_document"]
        entity.source_display_name = normalized["source_display_name"]
        entity.game_system_key = normalized["game_system_key"]
        entity.game_system_name = normalized["game_system_name"]
        entity.upstream_url = normalized["upstream_url"]
        entity.upstream_checksum = checksum
        entity.summary = normalized["summary"]
        entity.data_json = normalized["data"]
        entity.synced_at = utc_now()
        entity.is_active = True
        entity.is_deleted_upstream = False
        progress.records_updated += 1
        db.flush()
        rebuild_search_row(db, entity)
    else:
        progress.records_unchanged += 1


async def run_open5e_sync(run_id: int, endpoints: list[str] | None = None) -> None:
    """Run one endpoint at a time and one API page at a time.

    There is no endpoint or page concurrency. Each page is processed and committed
    before the next page is requested. Delays and retry backoff are configurable.
    """
    with SessionLocal() as db:
        run = db.get(SyncRun, run_id)
        if run is None or run.status not in ACTIVE_SYNC_STATUSES:
            return
        run.status = "running"
        run.started_at = utc_now()
        db.commit()

        failures: list[str] = []
        timeout = httpx.Timeout(settings.open5e_timeout, connect=min(settings.open5e_timeout, 15.0))
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
        headers = {"Accept": "application/json", "User-Agent": settings.open5e_user_agent}
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                headers=headers,
            ) as client:
                available = await discover_endpoints(client)
                selected = endpoints or settings.endpoint_names
                endpoint_urls = {
                    name: available.get(name, urljoin(settings.open5e_api_root.rstrip("/") + "/", f"{name}/"))
                    for name in selected
                } if selected else available

                progress_rows: list[SyncEndpoint] = []
                for endpoint_name, url in sorted(endpoint_urls.items()):
                    progress = SyncEndpoint(
                        sync_run_id=run.id,
                        endpoint=endpoint_name,
                        entity_type=entity_type_for_endpoint(endpoint_name),
                        source_url=url,
                        status="pending",
                    )
                    db.add(progress)
                    progress_rows.append(progress)
                db.commit()

                for index, progress in enumerate(progress_rows):
                    endpoint_name, url = progress.endpoint, progress.source_url or ""
                    _mark_endpoint_running(db, run.id, progress.id)
                    db.expire_all()
                    progress = db.get(SyncEndpoint, progress.id)
                    if progress is None:
                        raise RuntimeError(f"Sync endpoint disappeared: {endpoint_name}")
                    try:
                        async for page_number, records in fetch_endpoint_pages(client, url):
                            for raw in records:
                                _upsert_record(db, progress, endpoint_name, raw)
                            # A page is the transaction boundary. This limits SQLite
                            # write duration and guarantees visible incremental progress.
                            _refresh_run_totals(db, run)
                            db.commit()

                        _mark_endpoint_finished(db, progress.id, "completed")
                    except httpx.HTTPStatusError as exc:
                        message = f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}"
                        _mark_endpoint_finished(db, progress.id, "failed", message)
                        failures.append(f"{endpoint_name}: {message}")
                    except (httpx.HTTPError, ValueError) as exc:
                        message = f"{type(exc).__name__}: {exc}"
                        _mark_endpoint_finished(db, progress.id, "failed", message)
                        failures.append(f"{endpoint_name}: {message}")

                    db.expire_all()
                    run = db.get(SyncRun, run_id)
                    if run is None:
                        return
                    _refresh_run_totals(db, run)
                    db.commit()

                    # Deliberate pause between entity types. Do not delay after the last.
                    if index < len(progress_rows) - 1 and settings.open5e_endpoint_delay > 0:
                        await asyncio.sleep(settings.open5e_endpoint_delay)

            # Resolve any impossible leftovers before the run itself becomes terminal.
            leftovers = db.scalars(
                select(SyncEndpoint).where(
                    SyncEndpoint.sync_run_id == run_id,
                    SyncEndpoint.status.in_(("pending", "running")),
                )
            ).all()
            for item in leftovers:
                item.status = "failed"
                item.error_message = "Endpoint did not reach a terminal state."
                item.completed_at = utc_now()
                failures.append(f"{item.endpoint}: endpoint did not reach a terminal state")
            if leftovers:
                db.commit()

            run = db.get(SyncRun, run_id)
            if run is None:
                return
            _refresh_run_totals(db, run)
            run.status = "completed_with_errors" if failures else "completed"
            run.error_message = "; ".join(failures) if failures else None
            run.completed_at = utc_now()
            db.commit()
        except Exception as exc:
            db.rollback()
            run = db.get(SyncRun, run_id)
            if run:
                run.status = "failed"
                run.error_message = f"{type(exc).__name__}: {exc}"
                run.completed_at = utc_now()
                db.commit()


async def sync_open5e(db: Session, endpoints: list[str] | None = None) -> SyncRun:
    """Compatibility helper used by the CLI and tests; waits for completion."""
    run, created = create_sync_run(db)
    if created:
        await run_open5e_sync(run.id, endpoints=endpoints)
    db.expire_all()
    return db.get(SyncRun, run.id)
