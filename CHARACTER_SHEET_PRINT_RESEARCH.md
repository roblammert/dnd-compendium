# Printable Character Sheet Research - v0.32.0

This release rebuilt the printable Character Builder output after reviewing more than twenty official and community D&D 5e / 2024 sheet approaches. The objective was not to reproduce any one copyrighted layout, but to identify recurring usability patterns and implement an original print system for Rob's D&D Compendium.

## Reviewed sheet approaches

| # | Sheet / approach | Design lesson used |
|---|---|---|
| 1 | Official D&D 2024 Character Sheet | Combat-critical numbers are promoted to the top and skills are more tightly associated with abilities. |
| 2 | Official D&D 2014 3-page Character Sheet | Clear separation between core play, narrative details, and spells remains useful. |
| 3 | Official D&D 5e Fillable PDF | Strong field hierarchy and familiar terminology improve scan speed. |
| 4 | Official Starter Set sheets | New-player sheets benefit from obvious grouping and reduced visual ambiguity. |
| 5 | Adventurers League sheets | Campaign/reference fields should not displace core combat information. |
| 6 | MorePurpleMoreBetter sheet family | Automated/derived values and dense information can coexist when hierarchy remains consistent. |
| 7 | Alternate default 5e layouts catalogued by D&D Compendium | Reordering the official information model can improve table usability without removing data. |
| 8 | Complete editable 5e PDF variants catalogued by D&D Compendium | Computer-generated sheets should remain print-first rather than looking like browser forms. |
| 9 | Erbentunk class-specific sheets | Class-specific information deserves stronger visual prominence than generic empty boxes. |
| 10 | Additional class-specific DMs Guild sheets | Class resources are easier to use when feature names are available at a glance. |
| 11 | Alternate class-specific layouts catalogued by D&D Compendium | Long class text belongs on reference pages, not in the core combat dashboard. |
| 12 | Wasted Wizard Games 2024 sheet | A print-first layout can remain dense while preserving generous whitespace between logical groups. |
| 13 | Wasted Wizard Games 2014 sheet | Dedicated spell tracking remains valuable for spell-heavy characters. |
| 14 | byfrancita illustrated dyslexia-friendly 5e sheet | Strong grouping, icons/markers, and distinct ability areas improve quick recognition. |
| 15 | Dungeon Bros class-specific sheet bundle | Ability/skill grouping and class-tailored reference blocks reduce lookup time. |
| 16 | Dungeon Master Assistance 7-page auto-fill sheet | Overflow content should receive additional pages rather than being compressed into unreadable text. |
| 17 | Eren Angiolini 3-page character sheet | Combat references, concentration/components, and restrained ornament can improve usability. |
| 18 | DMing Dad optimized printable sheets | Notes, equipment, and auxiliary information benefit from dedicated printable space. |
| 19 | 2legit2crit minimalist sheet | Minimal decoration and consistent alignment make dense numeric data easier to scan. |
| 20 | Esoterisk clean minimalist Character/Combat layout | Separating roleplay-oriented and combat-oriented information reduces visual competition. |
| 21 | Community 2024 replica/fillable sheets | The 2024 layout's combined ability/skill treatment is a strong improvement over a separate alphabetical skill column. |
| 22 | Community 2024 portrait variant | Optional presentation fields should not consume required mechanical space. |
| 23 | Compact one-page community sheets | One-page density is useful for quick reference, but long features and spells should not be forced into it. |
| 24 | Brett Bullion class-specific sheets | Trackable class resources and short-reference information are more valuable on the front page than long prose. |
| 25 | Roll20 2024 printable character output | A digital character record should be the source of truth, with the PDF treated as a rendering of that state. |

## Sources reviewed

- D&D Beyond official character-sheet resources: https://www.dndbeyond.com/resources/1779-d-d-character-sheets
- Wizards Play Network 2024 Character Sheets: https://wpn.wizards.com/en/products/2024-character-sheets
- D&D Compendium character-sheet directory: https://www.dnd-compendium.com/player-guides/character-sheets
- Polygon review/discussion of the 2024 sheet: https://www.polygon.com/dnd-dungeons-dragons/491005/2024-character-sheet-where-to-find
- Wasted Wizard Games 2024 printable sheet: https://wastedwizardgames.com/dnd/character-sheets/2024/
- Wasted Wizard Games 2014 printable sheet: https://wastedwizardgames.com/dnd/character-sheets/5e/
- byfrancita dyslexia-friendly sheet: https://byfrancita.itch.io/illustrated-dyslexia-5e-sheet
- Dungeon Master Assistance 7-page sheet: https://olddungeonmaster.com/2017/09/21/dd5e-character-sheet-rev7/
- Eren Angiolini character sheet: https://erenangiolini.com/shop/p/dd-character-sheet-printabledigital-file
- DMing Dad printable sheets: https://dmingdad.com/product/printable-dd-5e-character-sheets/
- Community discussions and examples from r/DnD, r/dndnext, r/DnDIY, and r/FoundryVTT reviewed during design research.

## Resulting design principles

1. **Page 1 is the at-the-table dashboard.** Identity, AC, HP, initiative, speed, proficiency bonus, passive perception, abilities, saving throws, skills, attacks, languages, currency, and short feature names are immediately available.
2. **Skills live with their governing ability.** This follows the more readable 2024-style grouping and eliminates the need to visually jump between distant sections.
3. **Rules prose is separated from play-state numbers.** Traits, features, and feats retain their descriptions and rendered Markdown on reference pages where they can flow naturally.
4. **Inventory is a real table.** Table headers repeat on continuation pages and the list may expand rather than clipping or shrinking.
5. **Narrative content is content-driven.** Empty story boxes provide a small writing area; populated boxes grow and paginate naturally.
6. **Spellcasting is conditional.** Non-casters do not receive an empty spell page. Caster spell sections are emitted only when relevant and may use remaining page space before continuing naturally.
7. **No fixed-height prose containers.** Long descriptions, Markdown tables, backstories, and notes are permitted to paginate. Atomic short cards prefer not to split, while oversized content is allowed to continue on the next page.
8. **US Letter is authoritative.** PDF output uses CSS paged media at 8.5 x 11 inches and reserves bottom margin for the generated footer.
9. **The PDF is a rendering of character state.** No values are separately maintained inside the print layer; derived Character Builder data remains the source of truth.
10. **Printer-friendly visual language.** The design uses restrained dark teal, warm neutral borders, strong typography, and no large ink-heavy backgrounds.
