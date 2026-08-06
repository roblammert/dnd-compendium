# Release Notes

Cumulative release history for D&D Compendium. New patch installers append their release section to this file.

## v0.1.0

- Initial FastAPI, SQLite/FTS5, Jinja, Docker, Open5e synchronization, homebrew-safe data ownership, assets, API, and responsive card scaffold.

## v0.2.0

- Moved synchronization to the discoverable Open5e v2 API, added endpoint discovery, document-aware identities, and endpoint-level failure handling.

## v0.3.0

- Added persistent background synchronization jobs, per-endpoint SQLite progress, polling status UI, duplicate-run protection, and restart recovery.

## v0.4.0

- Made synchronization strictly sequential and throttled with one endpoint/page at a time, bounded commits, connection limits, Retry-After support, and exponential backoff.

## v0.5.0

- Corrected endpoint state invariants and introduced the compact live synchronization dashboard.

## v0.6.0

- Fixed polling fallback and terminal sync transitions; persisted source display name and game-system metadata and added Browse filters.

## v0.7.0

- Added canonical entity grouping, source variant selection, shared artwork, professional monster cards, and reliable sync finalization.

## v0.8.0

- Reworked canonical Browse grouping to avoid SQLite expression-depth limits, added pagination preference cookies, broader monster ability parsing, and raw JSON inspection.

## v0.9.0

- Normalized monster identity pills, speeds, ability/saving throw grids, and languages.

## v0.10.0

- Added site-wide stable descriptor colors, Browse return-state preservation, challenge/traits placement, and skill bonus tables.

## v0.11.0

- Redesigned monster summary statistics and added initiative, XP, passive perception, and resistance/immunity presentation.

## v0.12.0

- Expanded combined resistance/immunity parsing and refined HP/AC/XP emphasis.

## v0.12.1

- Fixed the Jinja dict.items collision in resistance tables.

## v0.13.0

- Introduced the Settings shell, Site Lexicon, Site Config, service restart control, stable source colors, horizontal primary monster stats, and full-page Browse navigation.

## v0.14.0

- Applied lexicon overrides throughout visible labels, simplified grouped source/system badges, widened Browse type cells, and versioned the footer.

## v0.15.0

- Added dedicated Magic Item and Species cards.

## v0.16.0

- Added styled Markdown tables, normalized weights/armor metadata, simplified Species summaries, and a dedicated Item card.

## v0.17.0

- Separated lexicon display labels from route keys, improved home-card summaries and footer badges, and rendered Markdown emphasis.

## v0.18.0

- Added a dedicated Weapon card with structured weapon metadata.

## v0.19.0

- Added authentication, Administrator/Editor/User roles, default admin creation, user management, profiles, artwork/JSON permissions, and public/private personal entity lists.

## v0.20.0

- Restricted homebrew to Editors/Admins, redesigned Profile and List Manager, added drag-and-drop ordering, prevented duplicate list entries, improved Add-to-List behavior, and fixed footer versions.

## v0.21.0

- Added role-based endpoint View Management, authenticated read-only access to all member lists, a GitHub-style README, cumulative release notes, and Git-native no-backup patch installers.

## v0.22.0

- Expanded Weapon properties into structured entries with descriptions, range details, and links to the referenced weapon-property records.
- Combined Site Lexicon and View Management into Endpoint Management with per-row asynchronous saves and five-second inline confirmation.
- Prevented direct-host restart requests from terminating Uvicorn without a supervisor; local deployments now receive explicit restart instructions while Docker retains automatic restart behavior.
- Made `APP_NAME` drive the site header, browser title, FastAPI title, and footer.
- Reorganized Site Config into Application, Storage, Open5e Synchronization, and Authentication/Session groups.
- Changed local defaults to `sqlite:///./data/compendium.sqlite3` and `./data/assets`; Docker now mounts host data at `/app/data`.
- Added a shared D&D coin formatter for visible Cost fields, selecting the simplest exact coin denomination and exposing PP/GP/SP/CP conversions in a hover tooltip.
- Added explicit `Unknown` rendering for present-but-empty Cost and Weight fields.



## v0.23.0

- Seed new databases with curated endpoint display labels and Users visibility defaults.
- Correct nested Open5e weapon property rendering, including details, descriptions, and local compendium links.
- Link weapon damage types and versatile damage types to Damage Type entries.
- Restrict private lists to their owners; other authenticated members see public lists only.

## v0.23.1

- Fixed Weapon summary metadata links rendering as literal dictionaries instead of clickable anchors.
- Added a Battleaxe regression test covering linked Damage Type, linked Versatile property metadata, and nested Open5e property data.
- Hide Cost and Weight primary-stat bands when those fields are absent from the source record.
# D&D Compendium v0.24.0

## Dedicated cards

Added dedicated, source-aware card renderers for:

- Spell
- Spell School
- Weapon Property
- Skill
- Service
- Language
- Size

The new cards share the established compendium presentation system: artwork, descriptor badges, source switching, Markdown descriptions, linked reference metadata, responsive summary grids, Add to List, role-gated artwork management, and raw JSON inspection.

### Spell

Displays school, level, casting time, range, components, duration, attack/save metadata, damage, ritual/concentration badges, class availability, and At Higher Levels text. Spell-school values link to their compendium entry.

### Spell School

Provides a focused rules-reference card with Markdown description and key metadata.

### Weapon Property

Displays property type, detail, range, and the full property explanation.

### Skill

Displays the governing ability as a linked compendium reference, passive usage, common uses, and description.

### Service

Displays category, normalized D&D currency cost with conversion tooltip, unit, and description.

### Language

Displays language type, script, typical speakers, and description.

### Size

Displays space, reach, typical height, typical weight, and description.

## Verification

- Added dedicated v0.24 card-normalization regression coverage.
- Full test suite: 63 passed.

# v0.25.0 — Complete Open5e Endpoint Card Coverage

This release adds tailored cards for every remaining Open5e v2 endpoint type discovered by the application.

## New cards

- Ability
- Alignment
- Armor
- Background
- Class
- Condition
- Creature Set
- Creature Type
- Damage Type
- Document / Source
- Environment
- Feat
- Game System
- Image
- Item Category
- Item Rarity
- Item Set
- License
- Publisher
- Rule
- Rule Set

Each card uses the established compendium presentation system: descriptor badges, source variants, linked references, Markdown descriptions, shared artwork, Add to List, role-gated artwork tools, and raw JSON inspection.

## Verification

- Added coverage for every remaining endpoint-card builder.
- Added link validation for Document, Game System, and Publisher references.
- Full test suite: 85 passed.

# v0.26.0 — Reference Card Metadata Refinement

This release refines Alignment, Background, Class, Condition, Creature Type, Damage Type, Feat, Game System, and Item cards around their actual Open5e metadata.

## Card updates

- Alignment now emphasizes Morality and Societal Attitude and renders each versioned description with its game system.
- Background benefits render as named detail blocks instead of flattened labels.
- Class features appear beneath the class description as full named feature blocks.
- Condition, Creature Type, and Damage Type omit internal key fields and render versioned descriptions by game system.
- Feat benefits render as complete named blocks with details and descriptions.
- Game System omits its internal key field.
- Item displays Size when supplied by Open5e.
- Document metadata inside versioned-description records remains intentionally excluded from card content.

## Verification

- Added focused regression tests for all requested card shapes.
- Full test suite: 90 passed.

# v0.27.0 — Weapon Fallback Metadata and Card Refinements

- Weapon cards now fall back to the matching Item entity for Cost and Weight when the Weapon record omits, blanks, or zeroes those fields.
- Item fallback selection prefers a matching game system when multiple Item variants exist.
- Skill cards now render versioned Descriptions grouped by Game System.
- Spell cards now recognize `saving_throw_ability` and display it in the top summary.
- Added regression coverage for all three behaviors.
