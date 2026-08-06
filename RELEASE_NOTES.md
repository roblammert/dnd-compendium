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

- Replaced the README with a GitHub-style project introduction, quick start, role matrix, architecture highlights, and operational guidance.
- Added cumulative `RELEASE_NOTES.md`; future patch installers append their patch notes to the end.
- Patch installers no longer create backup copies because Git is the source of rollback history.
- Patch installers print the exact suggested `git add` and `git commit` commands, including commit title and body.
- Authenticated users can see all lists, including other members' private lists, with owner attribution and read-only access.
- Only list owners can edit, reorder, remove items from, or delete their lists.
- Added Settings → View Management with per-endpoint visibility levels: Users, Editors, Administrators, and INVISIBLE.
- Endpoint visibility applies to home tiles, recent entities, Browse results and filters, direct entity pages, and list contents.
- Site Lexicon remains complete for administrators, and Open5e synchronization is unaffected.
- New endpoint types default to Users visibility.

## v0.22.0

- Expanded Weapon properties into structured entries with descriptions, range details, and links to the referenced weapon-property records.
- Combined Site Lexicon and View Management into Endpoint Management with per-row asynchronous saves and five-second inline confirmation.
- Prevented direct-host restart requests from terminating Uvicorn without a supervisor; local deployments now receive explicit restart instructions while Docker retains automatic restart behavior.
- Made `APP_NAME` drive the site header, browser title, FastAPI title, and footer.
- Reorganized Site Config into Application, Storage, Open5e Synchronization, and Authentication/Session groups.
- Changed local defaults to `sqlite:///./data/compendium.sqlite3` and `./data/assets`; Docker now mounts host data at `/app/data`.
- Added a shared D&D coin formatter for visible Cost fields, selecting the simplest exact coin denomination and exposing PP/GP/SP/CP conversions in a hover tooltip.
- Added explicit `Unknown` rendering for present-but-empty Cost and Weight fields.

