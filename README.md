# D&D Compendium

A self-hosted FastAPI, Jinja, HTMX-style, SQLite/FTS5 compendium designed for downloaded Open5e data and protected homebrew content.

## Included

- FastAPI website and versioned JSON API
- SQLite canonical entity store
- SQLite FTS5 cross-entity search
- Open5e pagination and synchronization service
- Source ownership rules that prevent sync from modifying homebrew
- Professional responsive entity cards and detail pages
- Homebrew creation UI and API
- Persistent Docker volume for the database and locally uploaded/downloaded artwork
- Swagger/OpenAPI interface at `/docs`
- Sync audit history

## Start with Docker

```bash
cp .env.example .env
mkdir -p data
docker compose up --build
```

Open `http://localhost:8000`.

Run the initial Open5e import from **Admin**, or from the container:

```bash
docker compose exec compendium python scripts/sync_open5e.py
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# For local execution, change DATABASE_URL and ASSET_ROOT in .env:
# DATABASE_URL=sqlite:///./data/compendium.sqlite3
# ASSET_ROOT=./data/assets
uvicorn app.main:app --reload
```

## API examples

```bash
curl 'http://localhost:8000/api/v1/entities?entity_type=monster&limit=10'
```

Create a homebrew record:

```bash
curl -X POST http://localhost:8000/api/v1/homebrew   -H 'Content-Type: application/json'   -d '{
    "entity_type":"monster",
    "name":"Ashen Ledger Drake",
    "summary":"A drake that devours written promises.",
    "data":{"armor_class":15,"hit_points":58,"challenge_rating":"4"}
  }'
```

## Data ownership invariant

Every entity has a `source_kind`:

- `open5e`: the sync service may insert or update it.
- `homebrew`: only local UI/API operations may update it.

The synchronization query always includes `source_kind = open5e`, so a same-named homebrew record is not overwritten. Slugs are made unique where needed.

## Important implementation note

The repository vendors a small local progressive-enhancement subset supporting the starter’s `hx-get`, targets, pushed URLs, live filters, and pagination without a CDN. Replace it with a pinned official HTMX distribution before using advanced HTMX extensions or behaviors.

## Next production milestones

1. Pin the official HTMX asset locally.
2. Add schema-specific cards and editors for every imported entity type.
3. Expand the included image upload/download workflow with galleries, role selection, and removal controls.
4. Add Alembic revision files before long-term schema evolution.
5. Add authentication before exposing homebrew or admin writes beyond a trusted LAN.
6. Add import fixtures matching the exact version of your downloaded Open5e dataset.

## License and content

This repository contains application code only. Open5e data and downloaded images retain their own licenses and attribution requirements.
