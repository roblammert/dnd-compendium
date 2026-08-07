# D&D Compendium

A self-hosted, searchable Dungeons & Dragons compendium built with **FastAPI**, **SQLite/FTS5**, **Jinja**, **HTMX-style progressive enhancement**, Python, and Docker. It mirrors Open5e content into a local database, protects homebrew records during synchronization, and presents rules content through professional type-specific cards.

## Highlights

- Public browse, search, filtering, pagination, and read-only JSON API
- Background, sequential, throttled Open5e v2 synchronization with live progress
- Canonical grouping of entities that have multiple sources or game-system variants
- Professional cards for Monsters, Magic Items, Items, Species, and Weapons, including detailed linked weapon properties
- Local artwork uploads and shared images across source variants
- Protected homebrew content that Open5e sync never overwrites
- Authentication with Administrator, Editor, and User roles
- Public and private personal entity lists with persistent drag-and-drop ordering
- Endpoint Management combining display-name overrides and role-based visibility
- Docker-first deployment with persistent `./data` storage

## Quick start with Docker

```bash
cp .env.example .env
mkdir -p data
# Set SECRET_KEY and DEFAULT_ADMIN_PASSWORD before first startup.
docker compose up --build
```

Open <http://localhost:8000>. The first startup creates the default administrator if the users table is empty.

## Important environment settings

```env
SECRET_KEY=replace-with-a-long-random-secret
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=replace-with-a-strong-password
DATABASE_URL=sqlite:///./data/compendium.sqlite3
ASSET_ROOT=./data/assets
OPEN5E_API_ROOT=https://api.open5e.com/v2/
```

See `.env.example` for synchronization throttling, retry, session, and storage settings. Docker mounts the host `./data` directory at `/app/data`, so the same relative paths work locally and in the container.

## Endpoint management

Administrators can use **Settings → Endpoint Management** to rename imported endpoint labels and set the minimum role allowed to see each type. Each row saves independently without a page refresh. These settings affect only the user interface; synchronization and stored data remain unchanged.

## Open5e synchronization

Administrators can start synchronization from **Settings → Open5e Sync**. The worker processes one endpoint and one API page at a time, commits each page, pauses between requests, honors `Retry-After`, and retries transient API/network failures with bounded exponential backoff. Sync remains unaffected by interface visibility rules.

## Roles and permissions

| Capability | Public | User | Editor | Administrator |
|---|:---:|:---:|:---:|:---:|
| Browse visible compendium content | ✓ | ✓ | ✓ | ✓ |
| Create/manage personal lists |  | ✓ | ✓ | ✓ |
| View all member public/private lists read-only |  | ✓ | ✓ | ✓ |
| Add/edit homebrew |  |  | ✓ | ✓ |
| Upload entity artwork |  |  | ✓ | ✓ |
| View complete entity JSON |  |  | ✓ | ✓ |
| Access Settings and manage users |  |  |  | ✓ |

## View Management

Administrators can set each endpoint type to **Users**, **Editors**, **Administrators**, or **INVISIBLE**. These rules filter home-page tiles, recent cards, Browse results, filters, entity pages, and list contents. The Site Lexicon continues to show every endpoint to administrators, and Open5e synchronization continues importing all configured data.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Run tests with:

```bash
pytest -q
```

## Data ownership

Every entity has a `source_kind`. Open5e synchronization may update only `open5e` records. Locally created `homebrew` records, user lists, uploaded images, lexicon overrides, users, and view permissions remain locally owned.

## Documentation

- `RELEASE_NOTES.md` — cumulative release history
- `/docs` — interactive OpenAPI documentation
- `.env.example` — configuration reference

## Content and licensing

This repository contains application code only. Open5e records and downloaded artwork retain their original licenses and attribution requirements.

## Complete Open5e card coverage

The compendium includes dedicated presentations for all Open5e v2 content types currently imported by the synchronizer. In addition to Monsters, Magic Items, Species, Items, Weapons, Spells, and rules-reference cards, v0.25.0 adds tailored cards for abilities, alignments, armor, backgrounds, classes, conditions, creature sets and types, damage types, source documents, environments, feats, game systems, images, item categories and rarities, item sets, licenses, publishers, rules, and rule sets.

Card builders normalize nested Open5e references into readable metadata and preserve the original source JSON for authorized users.

## Tools

The public Tools area includes a coin converter, encounter builder, and loot generator. Authenticated users can also select a preferred Open5e source in their profile.

### Encounter intelligence console

The public Dungeon Master tools include a mode-aware Encounter Builder with CR-band randomization, exact mixed-level XP budgets, variable party-size scaling previews, Lazy DM limiting analysis, preserved settings, and keepable monster rows. The Loot Generator uses separate per-entry and total-list GP limits and supports keepable compendium entities.

### Character Builder

Authenticated users have a persistent **Tools → Player → Character Builder** workspace. It uses the local Open5e cache and the user's preferred source to guide a character through identity/source, species/race, class, ability scores, background/proficiencies, equipment, spells/feats, narrative details, and final review.

Character records are stored separately from reference entities. Derived values such as proficiency bonus, ability modifiers, hit points, Armor Class, initiative, saving throws, skills, passive Perception, attacks, and spellcasting numbers are recalculated from the saved choices.

Completed characters can be printed through a purpose-built three-page sheet or downloaded directly as PDF. See `CHARACTER_BUILDER.md` for architecture and extension points.


### Character Builder reliability

Character Builder navigation is progressively enhanced: HTMX provides in-place step transitions, while every step also has a normal POST fallback. Direct fragment URLs redirect to the full application shell, and static assets are cache-busted by application version.

### Character Builder v0.31.4
The Player Character Builder now provides guided descriptions, parent-aware subclass selection, auto-generated ability scores, broader 2024-compatible background handling, selectable languages/proficiencies, and a live ability-score rail that shows character-impacting choices in real time.


### Character Builder v0.31.6

The Character Builder now includes a compact right-side Live Stats/Live Abilities rail, Level↔XP synchronization, source-specific background variants, locked background-granted skills and tools, and a reformatted Background & Proficiencies workflow with responsive non-overflowing choice grids.
