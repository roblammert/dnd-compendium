from app.sync import add_limit, normalize, record_identity


def test_add_limit_preserves_query():
    value = add_limit("https://api.open5e.com/v2/spells/?document=5e-srd", 100)
    assert "document=5e-srd" in value
    assert "limit=100" in value


def test_v2_creature_normalization_uses_document_identity():
    raw = {
        "key": "goblin",
        "name": "Goblin",
        "document": {"key": "5e-srd", "name": "5e System Reference Document"},
        "description": "A small humanoid.",
    }
    item = normalize("creatures", raw)
    assert item["entity_type"] == "monster"
    assert item["upstream_id"] == "5e-srd:goblin"
    assert item["source_document"] == "5e-srd"


def test_identity_falls_back_to_checksum():
    assert record_identity({"name": "Nameless"})

import httpx
import pytest

from app.sync import fetch_endpoint_pages, request_json


@pytest.mark.asyncio
async def test_fetch_endpoint_pages_is_sequential(monkeypatch):
    from app import sync as sync_module

    monkeypatch.setattr(sync_module.settings, "open5e_page_size", 2)
    monkeypatch.setattr(sync_module.settings, "open5e_request_delay", 0.0)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if len(calls) == 1:
            return httpx.Response(200, json={"results": [{"key": "a"}, {"key": "b"}], "next": "/v2/test/?page=2"})
        return httpx.Response(200, json={"results": [{"key": "c"}], "next": None})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.open5e.com") as client:
        pages = []
        async for page_number, records in fetch_endpoint_pages(client, "https://api.open5e.com/v2/test/"):
            pages.append((page_number, [row["key"] for row in records]))
            assert len(calls) == page_number

    assert pages == [(1, ["a", "b"]), (2, ["c"])]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_request_json_retries_429(monkeypatch):
    from app import sync as sync_module

    monkeypatch.setattr(sync_module.settings, "open5e_retry_attempts", 2)
    monkeypatch.setattr(sync_module.settings, "open5e_retry_base_delay", 0.0)
    monkeypatch.setattr(sync_module.settings, "open5e_retry_max_delay", 0.0)
    monkeypatch.setattr(sync_module.settings, "open5e_request_delay", 0.0)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"detail": "slow down"})
        return httpx.Response(200, json={"results": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload = await request_json(client, "https://api.open5e.com/v2/test/")

    assert payload == {"results": []}
    assert calls == 2

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db import Base
from app.models import SyncEndpoint, SyncRun
from app.sync import _mark_endpoint_running


def test_only_one_endpoint_can_remain_running():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        run = SyncRun(provider="open5e", status="running")
        db.add(run)
        db.flush()
        first = SyncEndpoint(sync_run_id=run.id, endpoint="abilities", status="running")
        second = SyncEndpoint(sync_run_id=run.id, endpoint="alignments", status="running")
        db.add_all([first, second])
        db.commit()

        _mark_endpoint_running(db, run.id, second.id)

        rows = db.scalars(select(SyncEndpoint).order_by(SyncEndpoint.id)).all()
        assert [row.status for row in rows] == ["pending", "running"]
from app.sync import normalize

def test_document_metadata():
    item = normalize("spells", {
        "key": "fireball", "name": "Fireball",
        "document": {
            "key": "srd-2024", "name": "System Reference Document 5.2",
            "display_name": "5e 2024 Rules",
            "gamesystem": {"key": "5e-2024", "name": "5th Edition 2024"},
        },
    })
    assert item["source_display_name"] == "5e 2024 Rules"
    assert item["game_system_key"] == "5e-2024"
    assert item["game_system_name"] == "5th Edition 2024"

from app.sync import _refresh_run_totals


def test_refresh_totals_does_not_revert_terminal_run_status():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        run = SyncRun(provider="open5e", status="running")
        db.add(run)
        db.flush()
        db.add(SyncEndpoint(sync_run_id=run.id, endpoint="creatures", status="completed", records_seen=10, records_created=8, records_unchanged=2))
        db.commit()
        run.status = "completed"
        _refresh_run_totals(db, run)
        assert run.status == "completed"
        assert run.records_seen == 10
        assert run.records_created == 8
        assert run.records_unchanged == 2
