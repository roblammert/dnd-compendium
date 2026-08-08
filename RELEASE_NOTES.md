
## v0.30.1 — Loot Generator Layout Hotfix

- Corrected the Content Profile grid so Include and Magic Item Rarity controls remain inside their fieldsets.
- Added stable checkbox-tile columns, label wrapping, equal tile sizing, and responsive breakpoints.
- Prevented long labels such as Magic Items, Very Rare, and Legendary from overflowing or colliding.

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
## v0.28.1 — Preferred Sources and Tools

- Added a user-profile preferred source setting used automatically on multi-source entity cards.
- Added a public Tools section with General, Player, and Dungeon Master navigation groups.
- Added a working coin converter with themed PP, GP, SP, and CP indicators.
- Added an encounter builder supporting CR randomization, XP-threshold budgets, manual search, variable scaling previews, and the Lazy DM benchmark.
- Added a loot generator with configurable categories, rarity filters, value limits, and keepable entity rows.
- Added regression coverage for preferred-source selection and public tool routes.


## v0.28.1 — Loot Generator State and Metadata Fixes

- Disabled Magic Item Rarities when Magic Items are excluded.
- Preserved all generator form settings across repeated generation requests.
- Reused source-aware Item metadata for Weapon Cost and Weight in generated loot.
- Applied Endpoint Management labels to generated entity types.
- Added cost conversion tooltips to populated Loot Generator rows.

## v0.28.2 — Encounter Console and Loot Value Controls

- Rebuilt the Encounter Builder as a professional, mode-aware encounter intelligence console.
- Removed Manual Search and all mode-irrelevant controls from the active interface.
- Added exact mixed-level party XP budgeting with Medium, Hard, and Deadly difficulty choices.
- Added add/remove party-member level controls and per-member XP threshold breakdowns.
- Moved Lazy DM limiting into the Scaling Strategy selector and applies it only when selected.
- Added preserved encounter settings and Keep checkboxes that retain selected monsters between generations.
- Added party-size and average-level inputs when CR mode requires variable or Lazy DM analysis.
- Added encounter metrics for party composition, XP budget, selected XP, total CR, scaling ratio, and Lazy DM limit.
- Removed PP, GP, SP, and CP generation controls from the Loot Generator.
- Added separate Maximum Value per Entry and Maximum Total List Value sliders, defaulting to 40 GP and 600 GP.
- Kept loot settings and kept rows persistent across repeated generation requests.
- Added regression coverage for mixed-level budgets, supported encounter modes, keep controls, and loot value controls.

### Mixed-level example clarification

Using the supplied standard Medium thresholds, levels 2, 4, 6, 7, 8, and 10 total 3,800 XP (100 + 250 + 600 + 750 + 900 + 1,200), not 2,900 XP.

## v0.29.0 — Encounter Design Workbench

- Rebuilt Encounter Builder as a five-stage professional workflow.
- Added Classic 2014 Adjusted XP, Story-First Lazy Benchmark, and composition-template build modes.
- Added party profile, encounter objective, terrain, pace, and creature-theme controls.
- Added raw/adjusted XP diagnostics, monster-count multipliers, and persistent keep behavior.
- Added responsive high-tech workbench styling and method reference documentation.

## v0.29.1

- Polished Scenario Parameters alignment and constrained all controls to their cards.
- Made Target Monster Count apply to XP Budget, Adjusted XP, Story-First, and CR Randomizer generation; kept monsters count toward the target.
- Rebuilt Loot Generator with the Encounter Builder tactical workbench styling, workflow navigation, metrics, and roster presentation.

## v0.30.0 — Generated Lists and Player Tools

- Added bulk Add to List modals to Encounter Builder, Loot Generator, and Loadout Generator results.
- Added support for adding generated results to an existing list or creating a new public/private list.
- Redesigned My Lists with a modal-based creation flow and separate My Lists and Other's Lists sections.
- Added Loadout Generator with cost/weight constraints, keepable rows, total weight/cost, armor class, stealth disadvantage, and Strength requirement analysis.
- Added Feat Evaluator with level, ability score, and proficiency-aware prerequisite filtering.
- Added Weapon & Martial Arts Evaluator with side-by-side damage, properties/mastery, range, source, and source-aware cost comparison.
- Extended the tactical workbench visual system across all new Player tools.

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

- Added a persistent, user-owned Character Builder under Player Tools.
- Added a nine-stage HTMX character creation and maintenance workflow.
- Added source-aware Species/Race, Class, Background, Equipment, Spell, and Feat selection from the local Open5e cache.
- Added Standard Array, Point Buy, Rolled, and Manual ability-score workflows.
- Added a backend character derivation engine for proficiency bonus, modifiers, HP, AC, initiative, speed, saves, skills, passive Perception, attacks, and spellcasting numbers.
- Added inventory, currency, known/prepared spells, proficiencies, appearance, backstory, personality, allies, treasure, and notes persistence.
- Added a three-page printable character sheet and direct PDF download via WeasyPrint.
- Added Docker dependencies required for PDF generation.
- Added `CHARACTER_BUILDER.md` architecture and extension documentation.
- Added v0.31 regression tests; full suite: 129 passed.

## v0.31.1 - Locked 2024 Character Rules

- Removed the Character Builder Game Rules / Source selector.
- Character Builder is now permanently pinned to `srd-2024` / `5e-2024` regardless of the user's general Preferred Source setting.
- New characters begin with the 2024 rules source already assigned, eliminating the Step 1 "source required" blocker.
- Existing Character Builder records from another edition are normalized to the 2024 rules and incompatible source-specific choices are cleared once.
- Character reference lookups never fall through to 2014 data; exact `srd-2024` entities are preferred, with `5e-2024` records as the only fallback.
- Added bundled SRD 5.2.1 mechanical fallback metadata for core class hit dice, saving throws, skill choices, spellcasting abilities, and Free Rules background mechanics when cached Open5e records omit structured fields.

## v0.31.2 - Character Builder Navigation & Asset Reliability

- Fixed Character Builder step forms so they work with or without HTMX by providing normal POST `method` and `action` attributes in addition to `hx-post`.
- Fixed Save & Continue on Identity and every subsequent Character Builder step so a valid save advances to the requested next stage even when HTMX fails to initialize.
- Direct visits to `/step/{step}` fragment URLs now redirect to the full Character Builder shell instead of rendering an unstyled partial document.
- Added version query strings to application CSS, HTMX, and JavaScript assets to prevent stale browser caches after upgrades.
- Added regression tests covering progressive-enhancement form wiring, fragment redirects, and asset cache busting.

## v0.31.4 — Character Builder Guided Choice UX

- Removed repeated ruleset/source callouts from the Character Builder stages.
- Added concise Species/Race, Class, Subclass, and Background descriptions with cached Compendium **More Info** modals.
- Grouped subclasses beneath their parent class and enabled them only after the matching primary class is selected.
- Rebuilt Ability Score method controls, added Standard Array / Point Buy / 4d6-drop-lowest auto generation, and added instant modifier updates.
- Expanded Background selection to support legacy cached backgrounds under 2024 conversion rules while preferring 2024 variants where available.
- Fixed Alignment options when no dedicated 2024 alignment records exist.
- Replaced free-text language/proficiency entry with selectable controls.
- Added the sticky Live Abilities rail from Background through Review with five-second green/red change feedback.
- Added v0.31.4 regression coverage.


## v0.31.5 — Character Builder live stats and background workflow refinement

- Reworked the Character Builder right rail into compact Live Stats (HP, AC, PB) and three-letter Live Abilities rows.
- Removed HP/AC/PB from the Build Status header and eliminated duplicate/bottom ability rails by replacing HTMX out-of-band rail rendering with a live-state payload.
- Added bidirectional Level/XP synchronization using the 2024 XP thresholds, with server-side normalization.
- Rebuilt Background & Proficiencies layout to prevent truncated controls and horizontal overflow.
- Background descriptions are capped at 220 characters in the workflow while More Info retains the complete cached reference card.
- Background-granted skills and tool proficiencies are shown checked, locked, and read-only; derived character output includes them automatically.
- Background selections now preserve the exact source variant by public ID, while legacy canonical selections continue to resolve.
- Removed class saving-throw abbreviations from the Other Proficiencies picker.


## v0.31.6 — Character Builder rules-aware UI and equipment workflow

- Compacts the Live Stats/Abilities rail and keeps score/modifier values on one line.
- Makes Level and XP synchronize immediately in the Identity step.
- Restricts subclass choices to the selected primary class.
- Shows Background Ability Adjustment only for exact 5e 2024 Rules backgrounds.
- Locks Common and 2024 background-granted proficiencies while adding in-builder reference modals.
- Rebuilds Equipment & Attacks with automatic starting grants, duplicate item suppression, armor-training/one-suit limits, endpoint display pills, source-aware weapon costs, live Equipment Cost, and More Info modals.

## v0.31.7 — Character Builder controlled navigation, live search, and spell/feat rules

- Made the nine Character Builder step indicators non-clickable and added explicit Up/Down movement controls beneath the step list; forward movement is disabled until the active step is complete.
- Rebuilt Background skill, language, and other-proficiency pickers as fully visible non-scrolling grids.
- Added server-backed debounced Equipment search using SQLite `LIKE`/`ILIKE` matching against both names and cached JSON/description content, plus All/Armor/Item/Weapon/All Selected filtering.
- Kept selected armor enabled so it can always be removed; conflicting armor choices unlock immediately without a refresh.
- Added server-backed debounced Spell search with available-level and All Selected filtering.
- Expanded Spell selection across cached sources while requiring an explicit class/Available-To designation for the selected primary class.
- Added source pills and read-only More Info modals to spell choices.
- Added 2024 class/level spell-selection limits for cantrips, chosen levelled spells, and prepared spells, enforced in both browser behavior and server persistence.
- Expanded Feats across all cached sources, disabled feats with detectable unmet prerequisites, and added source pills and More Info modals.
- Preserved background-granted locked skills and tool proficiencies on POST even though locked controls are disabled in HTML.

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

- Renamed printable Armor Class to AC.
- Moved Hit Dice and Proficiency Bonus above the HP row.
- Split the former HP blocks into Current HP and Temp HP boxes on one line.
- Made narrative boxes content-driven with a two-line minimum instead of fixed empty height.
- Moved Equipment into the third-column position aligned with Attacks & Spellcasting.
- Split Traits and Features into separate full-width printable sections.
- Added print-specific Markdown rendering for emphasis, lists, blockquotes, and tables.
- Removed fixed-height narrative regions on page 2 so content grows naturally while Letter-size pagination is preserved.

## v0.32.1 - Printable Sheet Data & Pagination Repair

- Printable Traits now extract species trait blocks and class core-trait metadata from cached Open5e JSON instead of relying only on a top-level description.
- Class feature normalization discards Open5e progression-table placeholder rows such as `[Column data]`, ordinal table cells, proficiency columns, and class spell-list appendices.
- Features begin on a fresh US Letter page and use full-width flowing cards.
- Equipment switches to a four-data-column layout (`Item | Type | gutter | Item | Type`) when more than 10 entries are present.
- WeasyPrint page-margin footers now reserve their own page area so rules content cannot be printed through the footer.
- Footer left: `Generated with Rob's D&D Compendium - {version} - {YYYYMMDD}`.
- Footer right: `{Character Name} - {Player Name} - {Page}/{Total Pages}`.

## v0.32.3 - Printable play tracking and spell guidance

- Added printable Hit Dice usage pips beside the character's Hit Dice value.
- Added the 15 D&D 2024 core conditions as a three-column Condition Tracker on the core play page.
- Added the coin-equivalency reminder to the Currency title bar.
- Reworked spell-level headers for handwriting-friendly slot tracking and populated class/level slot totals when non-zero.
- Prepared-spell markers now print empty so players can track them manually at the table.
- Added a personalized Spell Usage reference covering cantrips, leveled spells, slots, preparation, spellcasting math, Concentration, and components.
- Strengthened the print footer into a single full-width rule while preserving Central-time generation stamps and character/player page numbering.


# D&D Compendium v0.32.4 Patch

## v0.32.4 — Cantrip-Locked Character Generation and Writable Spell Sheet

- Character creation now selects only cantrips; level 1+ spells and prepared-spell choices are no longer persisted by the builder.
- Cantrips become permanently locked when a character is marked complete.
- Printable Spellcasting page now always provides eight cantrip lines and nine writable spell-level boxes with calculated slot totals.
- Spell Usage is anchored at the bottom and explains fixed cantrips, prepared-spell changes after Long Rest/level-up, slot use, casting math, concentration, and components.

# D&D Compendium v0.32.5 Patch

## v0.32.5 — Spell Sheet Workspace Refinement

- Expanded every level 1–9 spell-writing box from four writable lines to nine.
- Reworked the Spellcasting header so Ability, Save DC, Attack, and Cantrips cards stack vertically at their existing compact width.
- Positioned the eight-line Cantrips panel beside the stacked summary cards to use the top of the US Letter page more efficiently.
- Preserved the bottom-anchored Spell Usage reference and class-aware slot totals.


# D&D Compendium v0.32.6 Patch

## v0.32.6 — Printable Inventory and Spell Workspace Refinement

- Moved Skill Proficiencies and Saving Throw Proficiencies beneath At-a-Glance Features on the core play page.
- Expanded printable Equipment into three balanced Item / Type / Weight groups across the page with gutters and blank write-in rows.
- Added source-aware Weapon weight fallback using matching Item records, consistent with the Weapon card behavior.
- Removed the explanatory footer text from the Equipment panel.
- Expanded each spell-level writing area to ten lines and matched the writable line height to the Cantrips panel while preserving the single-page US Letter spell workspace.

# D&D Compendium v0.32.7

## v0.32.7 — Printable Core Reference and Inventory Refinement

- Equipment now prints three full Item / Type / Value / Weight groups across the page.
- Printable Equipment Value uses the same source-aware cost fallback used by Weapon cards.
- Empty equipment rows retain the same height as populated rows for handwriting during play.
- Currency moved beneath the How Do I Roll reference on the left side of the core page.
- Skill Proficiencies and Saving Throw Proficiencies now sit directly beneath Proficiencies.
- At-a-Glance Features now uses two columns to reduce vertical space while keeping all entries readable.

# D&D Compendium v0.32.8

## v0.32.8 — Version Centralization and Print Layout Repair

- Added `app/version.py` as the single runtime source for the application version and updated all Jinja environments to import it instead of carrying stale hard-coded values.
- Replaced the Character Builder step mover glyphs with centered SVG arrow icons.
- Corrected the printable spell-level workspace so all ten writing lines fit inside every Level 1–9 box without overflow.
- Removed the internal vertical separators around Ability Score modifiers on the printable core page.
- Moved Currency beneath At-a-Glance Features on the core play page while retaining the coin conversion reminder.

# D&D Compendium v0.33.0

## Player Architect — Stage 1

- Added a completely separate Player Architect subsystem under Tools > Player, clearly marked **IN DEVELOPMENT**.
- Added persistent `architect_characters` and `architect_blueprint_entries` tables without reusing Player Builder character state.
- Added a compact character-library landing page with Create, Modify, PDF placeholder, and confirmed Delete actions.
- Added a responsive application shell with a fixed progress sidebar, scrollable workspace, collapsible Character Blueprint drawer, and fixed live-stat footer.
- Implemented Identity, Race/Species, Class/Subclass, Ability Scores, and Background/Alignment stages using the complete active compendium catalogs rather than the Player Builder's 2024-source restriction.
- Added automatic locked Blueprint entries for detectable ability, language, class Hit Die, and proficiency changes.
- Added verified user-created Blueprint entries that can be edited or deleted while automated entries remain immutable.
- Base ability scores are stored independently from Blueprint modifiers; live ability totals, AC, PB, and HP are derived without overwriting base values.
- Added minimum-ability requirement checks where cached race/class/subclass prerequisite data can be detected.
- Added Proficiencies, Languages, Feats, Cantrips & Spells, Character Details, and Review & Sheet stub stages for subsequent development.


## v0.33.1 - Player Architect Stage 1 UI repairs

- Rebuilt Race / Species and Class selectors as full-width rows for reliable desktop, tablet, and mobile layout.
- Fixed primary Class classification so generic class metadata no longer causes every class to be mistaken for a subclass.
- Added explicit subclass parent metadata for live filtering beneath the selected primary class.
- Reworked Ability Scores into a compact responsive 3x2 editor with Base / Blueprint / Live values.
- Rebuilt Background & Alignment into four explicit rows with live description updates and More Info actions.
- Converted Character Blueprint into a 70%-width overlay drawer with scrim, collapse control, and persistent vertical reopen tab.
- Player Architect workspace now uses the full content width while the Blueprint is closed.

## v0.33.2 — Player Architect shell and live-modifier repair

- Docked Player Architect navigation and workflow controls inside a fixed-height application shell.
- Moved Previous Step, Next Step, and View Blueprint actions to the pinned left sidebar.
- Removed duplicate in-content workflow buttons and expanded the workspace to the available viewport.
- Kept the PA content area between the website header and live status footer, with only the workspace scrolling.
- Reclassified the PA class catalog strictly from the Open5e `class` endpoint: a populated `subclass_of` identifies a subclass; an empty/missing `subclass_of` identifies a primary class.
- Expanded automatic Race/Species modifier extraction for Open5e mapping, attribute-list, nested, and prose JSON shapes.
- Added immediate Race/Class footer updates and pending Blueprint previews before save.
- Repaired Background and Alignment live description binding.
- Restyled More Info, modal Close, and Blueprint collapse controls for visibility and touch use.
- Added live Next Step enable/disable behavior based on the current form's minimum requirements.

## v0.33.3 — Player Architect class endpoint correction

- Correct Player Architect class discovery to use the cached Open5e `classe` entity type.
- Define subclasses exactly as SQLite does: `data_json.subclass_of` exists and is not JSON null.
- Define primary classes as the exact inverse: `subclass_of` is missing or JSON null.
- Keep all other class metadata out of primary/subclass classification.
## v0.33.4 — Player Architect class proficiency Blueprint

- Parse class and subclass proficiency/core-trait data across 2014 prose and 2024 Markdown-table shapes.
- Add fixed weapon, armor, tool, saving-throw, skill, language, cantrip, spell, and feat rules to the locked Character Blueprint when they can be applied deterministically.
- Add a **Needs Your Choice** ledger section for class/subclass instructions such as `Choose one tool`, `Choose 2 skills`, starting-equipment choices, and other unresolved player decisions.
- Preserve primary-class Blueprint entries when an optional subclass is selected so subclass rules layer on top of inherited class rules.
- Expand manual Blueprint stat categories to include Weapons, Armor, Tools, Saving Throws, Skills, Cantrips, Spells, and Feats.


## v0.33.5 — Player Architect structured class parser

- Treat class Hit Dice as a dedicated `Hit Dice` Blueprint stat instead of an HP modifier, preferring `hit_points.hit_dice_name` / `hit_points.hit_dice` and normalizing values such as `1d10 /Fighter Level`.
- Use only the class JSON `saving_throws` array for automatic Saving Throw Blueprint entries; do not duplicate save data parsed from prose/core-trait tables.
- Rename deterministic class facts to `Weapon Proficiencies`, `Armor Proficiencies`, `Tool Proficiencies`, and `Skill Proficiencies` so the ledger reflects the actual rule category.
- Ignore `None`, zero, `+0`, N/A, dash, and equivalent no-op modifiers instead of inserting them into the Blueprint.
- Suppress duplicate ledger rows that share the same How, Mod, and Stat, including pending live previews.
- Add a Source column to persistent Blueprint entries and automatically attribute imported rows to their compendium source.
- Move `+ Manual Blueprint Entry` above the ledger table.
- Keep unresolved `Choose...` class rules in Needs Your Choice rather than converting them into locked modifiers.
