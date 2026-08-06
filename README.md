# D&D Compendium v0.18.0

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

## Background synchronization

The Admin page starts Open5e synchronization as a background task and returns immediately. The worker processes exactly one endpoint at a time and one API page at a time; it does not prefetch or run endpoint requests concurrently. Each page is committed before the next page is requested, which keeps SQLite write transactions bounded and makes progress visible. Requests are deliberately delayed, a longer pause is applied between entity types, and HTTP 429/500/502/503/504 plus network failures use bounded exponential backoff with `Retry-After` support. While a run is active, the page polls `/admin/sync/status` every two seconds and displays per-endpoint status plus seen, created, and updated counts. A second sync cannot be started while one is queued or running. Jobs interrupted by an application or container restart are marked failed during startup and can then be restarted.

### Sync safety settings

```env
OPEN5E_PAGE_SIZE=50
OPEN5E_COMMIT_EVERY=50
OPEN5E_REQUEST_DELAY=0.75
OPEN5E_ENDPOINT_DELAY=2.0
OPEN5E_RETRY_ATTEMPTS=5
OPEN5E_RETRY_BASE_DELAY=2.0
OPEN5E_RETRY_MAX_DELAY=60.0
```

For an especially conservative first import, use `OPEN5E_PAGE_SIZE=25`, `OPEN5E_REQUEST_DELAY=1.5`, and `OPEN5E_ENDPOINT_DELAY=5.0`.

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

## Version 0.6.0 additions

- Reliable two-second synchronization dashboard polling using a local JavaScript fallback plus HTMX attributes.
- Explicit terminal endpoint state transitions so completed endpoints cannot fall back to `pending`.
- Open5e document metadata persisted as `source_display_name`, `game_system_key`, and `game_system_name`.
- Source and game-system pills on browse cards and detail cards.
- Browse and JSON API filters for source display name and game-system name.
- Automatic additive SQLite migration for existing databases; no database deletion is required.


## v0.8.0 changes

- SQL-level canonical grouping prevents SQLite expression-tree overflow on large libraries.
- Browse tables paginate at 10, 25, 50, or 100 rows. The selected size is persisted in a one-year HTTP-only cookie.
- Monster ability-score extraction supports flat, nested, mapping, list, and Open5e v2-style data shapes.
- Every entity detail page includes a collapsed complete-JSON viewer.

## v0.10.0 monster-card normalization

Monster cards now normalize Open5e reference objects and structured fields:

- Size, creature type, subtype, and alignment appear as stable colored classification pills.
- Speed mappings such as `{ "walk": 30, "unit": "feet" }` display as `Walk 30 feet`.
- Ability Scores and Saving Throw Modifiers use aligned six-column grids.
- Senses are omitted from the visual monster card.
- Structured languages display as `Name: description` entries.
- The redundant source footer was removed; source and system remain in the metadata pills near the title.
- The complete selected-source JSON remains available in the collapsed JSON inspector.

## v0.11.0 monster summary and defenses

- Replaces the old linear AC/HP block with a responsive three-column stat summary.
- Emphasizes HP, AC, and XP as primary metrics.
- Adds initiative, creature type, size, alignment, proficiency bonus, and passive perception when available.
- Removes hit-dice display from the card.
- Places language entries below the Languages label.
- Adds a structured Resistances and Immunities table below Skill Bonuses.


## v0.17.0 hotfix

Fixed a Jinja dictionary-key collision in the monster Resistances and Immunities table. The template now accesses `row["items"]` and `row["category"]`, preventing `dict.items` from being treated as table data.


## Settings area (v0.17.0)

The former Admin page is now **Settings**, with Open5e Sync, Site Lexicon, User Management, and Site Config pages. Site Config writes the project `.env`; restart is required to apply runtime changes.


## v0.17.0 display refinements

- Site Lexicon overrides are used for user-facing entity/endpoint labels without changing stored API keys.
- Browse shows a single count pill when an entity has multiple sources or systems.
- The Type column reserves enough width for labels such as “Game System”.
- The footer displays the application version and Open5e compatibility.


## v0.17.0 card templates

Dedicated professional cards are included for Magic Items and Species, with source variants, shared artwork, structured metadata, feature sections, and raw JSON inspection.

## v0.17.0 card updates

- Magic Item and Item descriptions render CommonMark, including pipe tables, using site-native table styling.
- Visible weights are normalized to one decimal place.
- Magic Item armor metadata exposes `armor.ac_display` when present.
- Species summary cards retain Size and omit Speed.
- Mundane `item` records use a dedicated Item card with category, subtype, cost, weight, armor class, damage, quantity, properties, details, source variants, shared artwork, and raw JSON.


## v0.17.0

- Home-page entity links always use raw database route keys, while lexicon values remain display-only.
- Recently updated cards derive summaries from common Open5e description fields.
- Source and game-system badges now appear in the card footer without `Source:` or `System:` labels.
- The raw source-document footer was removed.
- Generic and structured descriptions render Markdown bold and italic emphasis.


## v0.18.0 Weapon card

Weapons now use a dedicated stat-card layout with damage, cost, weight, category, range, reach, versatile damage, mastery, ammunition, properties, special rules, source variants, shared artwork, and raw JSON inspection.
