# Character Builder - v0.31.0

## Purpose

The Character Builder is a persistent, source-aware Player tool for creating and maintaining D&D 5e characters from the application's local Open5e cache. It deliberately stores player choices separately from derived numbers so that changes to level, equipment, ability scores, proficiencies, or spells can recalculate the sheet without destroying the user's original selections.

## Routes

- `GET /tools/character-builder` - saved character library
- `POST /tools/character-builder/new` - create a character draft
- `GET /tools/character-builder/{public_id}` - interactive builder shell
- `GET /tools/character-builder/{public_id}/step/{step}` - HTMX step fragment
- `POST /tools/character-builder/{public_id}/step/{step}` - persist a step and return the next fragment
- `GET /tools/character-builder/{public_id}/print` - browser print sheet
- `GET /tools/character-builder/{public_id}/pdf` - generated three-page PDF
- `POST /tools/character-builder/{public_id}/delete` - delete owned character

All character routes require an authenticated user and enforce ownership.

## Workflow

1. Identity & Rules Source
2. Species / Race
3. Class & Subclass
4. Ability Scores
5. Background & Proficiencies
6. Equipment & Attacks
7. Spells & Feats
8. Character Details
9. Review & Sheet

The HTMX shell keeps the workflow in one application surface. Each save updates SQLite and replaces only the current stage.

## Source behavior

New characters default to the user's preferred source when one is configured. Reference data is selected in this order:

1. Exact source document match.
2. Same game system.
3. Available cached records when the requested category does not exist for that source.

Changing a character's source clears source-dependent choices so that selections from incompatible rules documents are not silently carried across editions.

## Character persistence

The `characters` table stores:

- ownership and identity
- source document / game system
- level and XP
- species/race, heritage, class, subclass, background, alignment
- base ability scores and ability method
- selected equipment
- known and prepared spells
- feats
- skills, saves, languages, other proficiencies
- currency
- roleplaying, appearance, story, organization and combat-state details
- completion state and current workflow step

Flexible JSON columns are intentional. Open5e sources vary in field shape and character options need to survive additions to upstream schemas without requiring a database migration for every new choice type.

## Derivation engine

`app/character_services.py` keeps calculated values out of the stored character state where practical.

Current calculations include:

- proficiency bonus by level
- ability modifiers
- source-provided ability score adjustments when detectable
- level-based HP from class Hit Die and Constitution
- saving throw modifiers and proficiency
- all 18 standard skills and proficiency
- passive Perception
- Armor Class from unarmored base and selected armor
- shield bonus detection
- stealth disadvantage / Strength requirement detection
- initiative and species speed
- weapon attack ability, attack bonus and damage
- spellcasting ability, Spell Save DC and Spell Attack Bonus
- known/prepared spell separation
- currency state
- Point Buy budget diagnostics

## Ability generation

Supported methods:

- Standard Array
- 27-point Point Buy
- Rolled
- Manual

Point Buy feedback is client-side and does not require a page refresh. The backend still stores the actual base values rather than relying on client-only calculations.

## Equipment

Equipment is selected from cached `equipment`, `item`, `weapon`, and `armor` entities in the active source/system. Equipped armor contributes to AC. Weapons become attack rows on the sheet. Equipment can be searched locally without a refresh.

## Spells and feats

Spell choices are source-aware and filtered against the selected class when the cached Open5e spell record exposes class/spell-list metadata. The filter also restricts inaccessible spell levels using the character's current level as a conservative upper bound.

Known spells and prepared spells are stored separately.

Feat selection is sourced from cached feat records. The existing Feat Evaluator remains available as a dedicated prerequisite-analysis tool.

## Printing and PDF

The printable character record is a custom three-page layout inspired by the information architecture of a traditional 5e character sheet without redistributing the supplied Wizards of the Coast form artwork.

Page 1:

- identity
- abilities
- saves
- skills
- AC / initiative / speed
- HP / Hit Dice
- attacks
- inventory / currency
- personality fields
- proficiencies and languages
- features and traits

Page 2:

- physical description
- appearance
- allies / organizations
- symbol / affiliation
- backstory
- additional features
- treasure

Page 3:

- spellcasting class and ability
- Spell Save DC
- Spell Attack Bonus
- Cantrips and spell levels 1-9
- prepared-state markers
- spell-slot writing space

The browser print route supports the browser's Print / Save as PDF workflow. The direct PDF route uses WeasyPrint and returns a downloadable PDF.

## Docker PDF support

The Docker image installs the small set of Pango/Harfbuzz/image libraries required by WeasyPrint and installs `weasyprint>=68,<69` with the application.

## Compatibility notes

Open5e v2 data is intentionally source-driven. Different sources can encode class traits, skill choices, spell lists, species bonuses, revised background bonuses, and equipment metadata differently. The derivation helpers therefore use tolerant field extraction rather than assuming one source-specific JSON schema.

When a rule cannot be safely derived from cached structured data, the builder preserves the user's explicit choice rather than inventing a rule.

## Planned expansion points

The v0.31 model is designed to support later increments without replacing character records:

- class-specific choice schemas and exact skill-choice counts
- 2014 vs 2024 source-specific creation policies
- multiclassing and multiclass prerequisites
- subclass level gates
- exact class spell-slot / prepared-spell tables
- cantrip and spell-known counts per class
- expertise and half-proficiency
- fighting styles and weapon mastery selection
- attunement and magic-item effects
- encumbrance modes
- rests, death saves and expendable resources
- level-up wizard and feature-choice diffs
- character portraits and organization symbols
- import/export character JSON
- campaign assignment and DM-view permissions

## v0.31.3 Interactive Builder UX

The builder now treats descriptions and immediate feedback as first-class workflow requirements:

- Species/race choices include concise descriptions with a **More Info** modal that loads the actual cached Compendium card.
- Class cards include concise descriptions and class-specific subclass choices. Subclasses stay hidden until their parent class is selected.
- Ability generation methods use readable radio cards. **Auto Generate / Fill** supports Standard Array, exact 27-point Point Buy, and 4d6-drop-lowest rolling. Ability modifiers update in the browser as scores change.
- Backgrounds are intentionally broader than the fixed 2024 rules source. Current 2024 variants are preferred for duplicates, while legacy backgrounds remain available under the 2024 conversion rule. Alignment similarly uses the best cached variant instead of requiring a dedicated 2024 endpoint record.
- Languages and common secondary proficiencies are checkbox selections rather than comma-delimited text fields.
- From Background onward, a sticky **Live Abilities** rail remains visible. Changes to background ability adjustments update the rail immediately; increases flash green and decreases flash red for five seconds.

The application rules engine itself remains fixed to D&D 2024. Broader background availability is compatibility behavior inside those rules, not an edition selector.
