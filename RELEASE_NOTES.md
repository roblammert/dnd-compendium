## v0.30.1 — Loot Generator Layout Hotfix

- Corrects the Content Profile layout shown in the supplied screenshot.
- Keeps checkbox labels inside their tiles and fieldsets.
- Uses stable responsive columns for Include and Magic Item Rarity options.
- Adds wrapping and minimum sizing for multi-word labels.

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

# v0.27.1 — Weapon Item-Fallback Hotfix

- Fix Weapon detail routes so matching Item records are selected by canonical key, slug, or case-insensitive name.
- Prefer an Item from the same source document, then the same game system.
- Read Cost and Weight from top-level or nested `item`, `equipment`, and `weapon` objects.
- Treat blank and zero Weapon values as missing so linked Item metadata can replace them.
- Support structured coin-unit objects and full coin names.
- Add regression coverage for nested Battleaxe Item metadata.

# v0.27.3 — Weapon Variant Fallback Matching

- Match Weapon and Item variants by source document first, then game system.
- Derive source and game-system keys from nested Open5e `document` metadata when indexed columns are blank.
- When only one Item variant exists, reuse its Cost and Weight for every matching Weapon variant.
- Keep the Item record unchanged and apply the values only while rendering the Weapon card.
- Add regression coverage for one-item/many-weapon and multi-source matching.

## v0.27.3

- Moved Weapon Cost and Weight fallback values into the metadata table and fixed structured cost rendering.
- Added exact-source Battleaxe regression coverage.

## v0.27.4 — Weapon Cost Conversion Tooltip

- Added the D&D coin conversion tooltip to the Weapon card Cost value in the structured metadata table.
- Corrected rendering of formatted Cost metadata objects.
- Preserved the existing quick-stat Cost tooltip and omitted tooltips for unknown or zero costs.
## v0.28.0 — Preferred Sources and Tools

- Added a user-profile preferred source setting used automatically on multi-source entity cards.
- Added a public Tools section with General, Player, and Dungeon Master navigation groups.
- Added a working coin converter with themed PP, GP, SP, and CP indicators.
- Added an encounter builder supporting CR randomization, XP-threshold budgets, manual search, variable scaling previews, and the Lazy DM benchmark.
- Added a loot generator with configurable categories, rarity filters, value limits, and keepable entity rows.
- Added regression coverage for preferred-source selection and public tool routes.


## v0.28.1 — Loot Generator State and Metadata Fixes

- Disable Magic Item Rarities whenever Magic Items are not included.
- Preserve every Loot Generator option after generation, including unchecked values.
- Reuse the Weapon card's source-aware Item fallback for Weapon Cost and Weight.
- Apply Endpoint Management display labels to the Type column.
- Add D&D coin-conversion tooltips to populated Cost cells.
- Add regression coverage for Battleaxe Item fallback and form-state preservation.


## v0.28.2 — Encounter Console and Loot Value Controls

- Rebuilds Encounter Builder with CR Range and Character XP Threshold modes.
- Adds mixed-level party entry, Medium/Hard/Deadly budgets, preserved settings, and Keep rows.
- Moves Lazy DM limiting into the scaling selector and adds high-tech metrics and analysis.
- Removes coin categories from Loot Generator.
- Adds 40 GP per-entry and 600 GP total-list value sliders.

## v0.29.0 — Encounter Design Workbench

- Rebuilds the Encounter Builder as a guided five-stage professional workflow.
- Adds XP Threshold, 2014 Adjusted XP, Story-First Lazy Benchmark, Composition Template, and CR Band methods.
- Adds mixed-level party setup, objective, terrain, pace, creature-theme, scaling, safety, and diagnostics controls.
- Preserves settings and kept monsters across regeneration.
- Adds a responsive high-tech tactical workbench interface.

## v0.29.1

- Polished the Scenario Parameters cards so labels, selectors, and descriptions align without overflowing.
- Applied Target Monster Count to XP Threshold, 2014 Adjusted XP, Story-First Benchmark, and CR Band generation.
- Counted kept monsters against the requested target and generated only the remaining slots.
- Rebuilt Loot Generator with the tactical workbench header, workflow navigation, structured panels, metrics dashboard, sticky generation dock, and matching roster table.
# D&D Compendium v0.30.0 Patch

This release adds generated-result list assignment, modernizes My Lists, and introduces the first complete Player tool suite.

## Included

- Bulk list assignment endpoint and reusable Add to List modal
- Encounter and Loot Generator Add to List actions
- Modal-only list creation and public list discovery sections
- Loadout Generator
- Feat Evaluator
- Weapon & Martial Arts Evaluator
- Tactical workbench CSS for Player tools
- Regression tests

## v0.30.2

- Rendered structured Feat Evaluator descriptions as Markdown with emphasis and tables.
- Fixed Loadout Generator content-card label layout.
- Standardized accessible cost-conversion tooltips across all Tools cost tables.

## v0.30.3 — Evaluator Filtering

- Added an instant client-side Hide Blocked toggle to Feat Evaluator without evaluation or page refresh.
- Renamed Weapon & Martial Arts Evaluator to Weapons Evaluator throughout the Tools interface.
- Added a Game System dropdown beside weapon search and preserved selected comparison records while filtering the picker.

## v0.30.4 — Evaluator interaction fixes

- Made the Feat Evaluator Hide Blocked control compact and correctly sized.
- Added immediate client-side Game System filtering to the Weapons Evaluator.
- Added immediate weapon-name filtering while preserving selected comparison records.

## v0.31.0 - Character Builder

- Added persistent user-owned characters and a nine-stage HTMX Character Builder.
- Added source-aware Species/Race, Class, Background, Equipment, Spell, and Feat choices from local Open5e data.
- Added character derivation for proficiency, abilities, HP, AC, initiative, saves, skills, attacks, passive Perception, and spellcasting.
- Added three-page print output and direct PDF generation with WeasyPrint.
- Added Docker PDF-rendering dependencies and Character Builder architecture documentation.
- Added v0.31 regression tests.

## v0.31.1 - Locked 2024 Character Rules

- Removed the Character Builder Game Rules / Source selector.
- Character Builder is now permanently pinned to `srd-2024` / `5e-2024` regardless of the user's general Preferred Source setting.
- New characters begin with the 2024 rules source already assigned, eliminating the Step 1 "source required" blocker.
- Existing Character Builder records from another edition are normalized to the 2024 rules and incompatible source-specific choices are cleared once.
- Character reference lookups never fall through to 2014 data; exact `srd-2024` entities are preferred, with `5e-2024` records as the only fallback.
- Added bundled SRD 5.2.1 mechanical fallback metadata for core class hit dice, saving throws, skill choices, spellcasting abilities, and Free Rules background mechanics when cached Open5e records omit structured fields.

## v0.31.2 - Character Builder Navigation & Asset Reliability

- Makes every Character Builder step form progressively enhanced with both normal POST and HTMX submission paths.
- Fixes Save & Continue returning to Identity when HTMX is unavailable or fails to initialize.
- Redirects direct `/step/{step}` browser requests to the full Character Builder page instead of rendering a fragment without site CSS/navigation.
- Adds application-version cache busting to CSS, HTMX, and JavaScript asset URLs.
- Adds regression coverage for all Character Builder step forms and fragment routing.

## v0.31.3 — Character Builder Guided Choice UX

- Removes repeated ruleset/source callouts from builder cards.
- Adds descriptive Species/Race, Class, Subclass, and Background cards with More Info modals loading the cached Compendium card.
- Groups subclasses under their primary class and filters them live.
- Repairs Ability Score method controls and adds Standard Array, exact 27-point Point Buy, and 4d6-drop-lowest auto generation with instant modifier updates.
- Supports legacy cached backgrounds under the 2024 conversion rules while preferring 2024 variants when duplicates exist.
- Repairs Alignment availability by using the best cached variant when a dedicated 2024 record is absent.
- Replaces free-text language/proficiency entry with selectable controls.
- Adds a persistent Live Abilities rail after the Ability Scores step with green/red five-second change feedback.

## v0.31.4 — Character Builder class normalization and reference-modal hotfix

- Keeps Character Builder More Info modals read-only by removing raw JSON, list actions, and artwork upload/link controls from embedded Compendium cards.
- Normalizes the class catalog into the twelve 2024 primary classes and nests recognized 2024 subclasses beneath their correct parent class even when Open5e exposes them through a class-shaped endpoint.
- Expands subclass-parent aliases for the 48 subclasses in the 2024 Player's Handbook naming scheme, including College of Lore and Circle of the Land.
- Fixes a Jinja context collision that caused a 500 error immediately after saving Ability Scores and advancing to Background & Proficiencies.

## v0.31.5 — Character Builder live stats and background workflow refinement

- Reworked the right rail into compact Live Stats (HP, AC, PB) and three-letter Live Abilities rows.
- Removed HP/AC/PB from Build Status and eliminated duplicate/bottom ability rails by using a live-state HTMX payload instead of out-of-band rail rendering.
- Added Level/XP synchronization using the bundled 2024 XP thresholds, with backend normalization.
- Rebuilt Background & Proficiencies layout to prevent truncated controls and horizontal overflow.
- Background descriptions are capped at 220 characters in the workflow while More Info retains the complete cached reference card.
- Background-granted skills and tool proficiencies are shown checked, locked, and read-only and are included in derived character output.
- Background selections preserve the exact source variant by public ID while legacy canonical selections continue to resolve.
- Removed class saving-throw abbreviations from the Other Proficiencies picker.


## v0.31.6 — Character Builder live rules and equipment workflow

- Compacts the right-side Live Stats / Live Abilities rail so HP, AC, PB, ability score, and modifier information uses much less horizontal space.
- Synchronizes Level and XP immediately in both directions while editing Identity.
- Normalizes the class key used by the subclass filter so only subclasses belonging to the selected primary class are shown.
- Shows and persists Background Ability Adjustment only for exact `srd-2024` / 5e 2024 Rules backgrounds; legacy backgrounds no longer receive that ASI widget.
- Locks Common as the universal language and limits the normal origin language picker to two additional languages.
- Makes skills, languages, and other proficiency rows open read-only reference information inside the Character Builder modal when cached endpoint data exists.
- Rebuilds Equipment & Attacks with automatic class/background/species starting-equipment grants, locked granted rows, duplicate generic Item suppression when a dedicated Weapon/Armor exists, Endpoint Management display labels as pills, source-aware Weapon→Item cost fallback, live purchased-equipment cost, armor training checks, and one-suit/one-shield enforcement.
- Adds compact 2024 Basic Rules fallback metadata for class armor/weapon training and Package A starting equipment when Open5e does not expose structured values.

## v0.31.7 — Character Builder controlled navigation, live search, and spell/feat rules

- Non-clickable step rail with guarded Up/Down controls.
- Fully visible Background skill/language/proficiency grids.
- Debounced SQLite wildcard search and live type filters for Equipment.
- Correct live armor deselection/reselection behavior.
- Debounced class-specific Spell search with level/selected filters.
- All-source spell/feat reference choices with source pills and More Info modals.
- 2024 spell selection/preparation limits and feat prerequisite enforcement.
- Locked background grants remain persisted server-side.

## v0.31.8 — Character Builder guarded navigation and reliable filtering

- Added dirty-state tracking to Character Builder steps. Previous and Up/Down movement now warns when the current step has unsaved changes and offers Save & Move, Discard & Move, or Cancel.
- Updated HTMX step responses to keep the Up/Down controls synchronized with the currently rendered step and its completion state.
- Rebuilt Languages and Other Proficiencies as full-width readable rows with no internal scroll areas.
- Fixed Equipment filtering by normalizing every displayed row to a semantic Armor, Item, or Weapon filter type and applying dropdown changes immediately in the browser.
- Preserved SQLite wildcard Equipment search across entity name, summary, and cached JSON/description content.
- Prevented Enter in Equipment search from submitting the step form or navigating backward.
- Fixed Spell level filtering by normalizing cached spell levels in Python before rendering filter metadata.
- Prevented Enter in Spell search from submitting the step form or navigating backward.
- Added v0.31.8 regression coverage; full suite: 166 passed.

## v0.31.9

### Character Builder filter rendering hotfix
- Fixed Equipment and Spell result cards remaining visible after their search/filter state marked them hidden.
- Added explicit `display: none !important` rules for dynamically hidden Equipment and Spell rows so card layout CSS cannot override the HTML `hidden` state.
- Removed the older name-only Character Builder search listeners so Equipment and Spell filtering now has a single authoritative implementation.
- Equipment search now sends the selected type filter to the backend in addition to applying the semantic type filter client-side.
- Enter in Equipment and Spell search remains intercepted and cannot submit the surrounding Character Builder step form.

## v0.31.10 - Character Builder feat rows

- Replaced the Character Builder feat grid with compact full-width rows.
- Removed inline feat benefit/description previews from the Spells & Feats step.
- Kept feat name, source, prerequisite/status text, selection control, and More Info action visible.
- Detailed feat content remains available through the read-only Character Builder reference modal.

## v0.31.11 - Character Builder review state and completion lifecycle

- Reopening a saved character from the Character Library now always starts at Step 1: Identity.
- Simplified Review & Character Sheet by removing the Combat and Features & Feats boxes.
- Rebuilt the Review layout into a responsive derived-stat dashboard plus Identity and Ability Score summaries.
- Moved the completion control into a dedicated Character Status panel so it remains inside the Review form and layout.
- Any actual persisted change saved on Steps 1–8 now automatically clears `is_complete`, returning the character to Draft until explicitly completed again on Step 9.
- Navigation-only changes do not invalidate completion because `current_step` is excluded from the completion-state fingerprint.

## v0.31.12 - Character Review layout alignment hotfix

- Re-aligned Review ability score rows so ability abbreviation, score, and modifier remain cleanly on one line.
- Increased Review ability score prominence while preserving the smaller modifier typography.
- Replaced the oversized completion checkbox presentation with an explicitly sized native checkbox and compact inline label.
- Constrained the completion control so its label remains inside the Character Status panel.

## v0.31.13 - Character Review ability-tile fit hotfix

- Tightened the Step 9 Ability Scores row grid so the ability abbreviation, score, and modifier all remain inside each tile.
- Preserved the existing score and modifier font sizes while reducing only spacing and reserved column width.
- Added overflow safeguards for narrow Review layouts.

## v0.31.14 - Printable Character Sheet Layout

This release restructures the printable/PDF character sheet for US Letter output.

- Printable `Armor Class` is shortened to `AC`.
- Hit Dice and Proficiency Bonus now sit above the HP row.
- Current HP and Temp HP share a single row and use compact `HP` labels.
- Personality Traits, Ideals, Bonds, Flaws, and page-two narrative boxes size to their content with a two-line minimum instead of large fixed empty regions.
- Equipment moved into the third column beneath Flaws, aligned with the top of Attacks & Spellcasting.
- The old combined Features & Traits region is split into full-width Traits and Features boxes.
- Traits and Features render Markdown emphasis, lists, blockquotes, and tables.
- Printable panels are allowed to grow naturally; WeasyPrint retains US Letter page sizing and can paginate longer content instead of clipping it.

## v0.32.0 - Printable Character Sheet Rework

The Character Builder print/PDF subsystem has been redesigned from the ground up after reviewing more than twenty official and community D&D 5e/2024 character-sheet approaches. The new layout prioritizes at-the-table scan speed, complete information, printer efficiency, and safe content pagination.

The first page is a combat-first dashboard with identity, core statistics, grouped ability/skill cards, attacks, defenses, languages, proficiencies, currency, and feature names. Inventory and detailed rules content move to reference sections where Markdown can render without compression. Narrative information uses content-driven sizing, and spellcasting is included only when relevant. Long content continues onto additional US Letter pages instead of overflowing or being clipped.

Every printed page includes `Generated with Rob's D&D Compendium - {version} - {YYYYMMDD}`.
