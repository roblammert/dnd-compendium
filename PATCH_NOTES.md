# v0.27.2 — Weapon Variant Fallback Matching

- Match Weapon and Item variants by source document first, then game system.
- Derive source and game-system keys from nested Open5e `document` metadata when indexed columns are blank.
- When only one Item variant exists, reuse its Cost and Weight for every matching Weapon variant.
- Keep the Item record unchanged and apply the values only while rendering the Weapon card.
- Add regression coverage for one-item/many-weapon and multi-source matching.
