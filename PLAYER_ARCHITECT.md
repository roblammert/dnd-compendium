# Player Architect

Player Architect is an experimental, intentionally isolated character-generation subsystem introduced in v0.33.0. It does **not** use the Player Builder `Character` model, routes, services, templates, or 2024-only source-selection rules.

## Stage 1 scope

Implemented stages:
1. Identity
2. Race / Species
3. Class & Subclass
4. Ability Scores
5. Background & Alignment

Stubbed for later development:
6. Proficiencies
7. Languages
8. Feats
9. Cantrips & Spells
10. Character Details
11. Review & Sheet

The user specification repeated Step 5 when listing the future stages. The implementation normalizes the sequence so Background & Alignment remains Step 5 and the remaining stages continue sequentially through Step 11.

## Architectural isolation

- Routes: `app/player_architect_routes.py`
- State: `ArchitectCharacter`
- Modifier ledger: `ArchitectBlueprintEntry`
- Templates: `tools_player_architect*.html` and `player_architect_steps/`
- JavaScript: `app/static/js/player_architect.js`
- CSS: `.pa-*` namespace in `app/static/css/app.css`

Player Architect may read shared `Entity` records from the compendium but never writes Player Builder state.

## Character Blueprint

Every modifier is represented as a ledger row with:
- icon/lock state
- How
- Mod
- Stat
- Note

Automated entries are regenerated when their owning Race, Class, Subclass, or Background changes. Manual entries require explicit verification and remain user-editable/removable.

Base ability scores are never rewritten by Blueprint modifiers. Live values are derived as `base + blueprint`, preserving an auditable history of how a character reached its current numbers.


## v0.33.1 Stage 1 UI corrections

The main workspace is full width. Character Blueprint is now an overlay drawer rather than a permanent third column. Race/Species and Class/Subclass use row selectors; Ability Scores uses a responsive 3x2 card layout; Background and Alignment use dedicated selector/description rows. Primary class detection ignores generic self-referential `class` fields and only treats explicit parent relationships as subclass metadata.


## v0.33.2 shell corrections
The PA shell now owns viewport-height scrolling, pinned workflow controls, overlay Blueprint behavior, strict `subclass_of` class classification, and broader automatic modifier extraction.

## v0.33.3 class catalog rule

Player Architect reads primary classes and subclasses from the cached `classe` entity type. Subclass detection mirrors SQLite JSON semantics: a record is a subclass only when `$.subclass_of` exists and its JSON value is not null. A primary class is the inverse: `subclass_of` is absent or JSON null.

## v0.33.4 class proficiency and choice ledger

Step 03 now parses source-wide class/subclass proficiency structures instead of assuming a single Open5e schema. Older `**Weapons:** ...` / `**Tools:** ...` proficiency prose and newer `CORE_TRAITS_TABLE` Markdown rows are normalized into Blueprint facts. Deterministic rules become locked automated Blueprint entries. Any rule containing a player decision such as `Choose`, `Select`, `Pick`, `one of`, or an either/or equipment choice is surfaced under **Needs Your Choice** rather than being guessed. Selecting a subclass never removes the primary class Blueprint entries; subclass entries are a separate locked origin layered on top.
