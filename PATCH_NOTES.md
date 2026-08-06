# v0.27.0 — Weapon Fallback Metadata and Card Refinements

- Weapon cards now fall back to the matching Item entity for Cost and Weight when the Weapon record omits, blanks, or zeroes those fields.
- Item fallback selection prefers a matching game system when multiple Item variants exist.
- Skill cards now render versioned Descriptions grouped by Game System.
- Spell cards now recognize `saving_throw_ability` and display it in the top summary.
- Added regression coverage for all three behaviors.
