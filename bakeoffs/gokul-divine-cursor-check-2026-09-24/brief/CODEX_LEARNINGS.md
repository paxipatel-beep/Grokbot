# Codex learnings to apply (method + rule interpretation)

Privacy-safe. Do **not** copy any prior placement coordinates. Re-derive geometry from this base PDF and previews. These are the rule interpretations and production habits Codex settled on after blank-bakeoff + Gokul Divine marking.

## Immutable base (hard)
1. Never rasterize or redraw walls, furniture, SB IDs, title block, schedules, or the electrical legend.
2. Build a **separate vector overlay** (reportlab) and merge onto the **original** PDF page with pypdf (or equivalent). Page size/orientation must stay identical.
3. Prefer extracting native vector geometry (PyMuPDF/fitz) or measuring from a fresh `pdftoppm -png -r 150` render — never eyeball-only from a low-res preview.
4. Record SHA-256 of the base before/after; it must be unchanged.

## Legend / family B (viwaves simplified on overlay)
- Magenta on-wall SW / SO
- Cyan wall-bracket SW / SO (toilets usually bracket)
- Orange 4" / peach or orange 10" screens
- Purple CM
- True yellow square **surface** GW + separate black circular IR (not CG+IR combine)
- Black oval/badge DB at VDP / bell
- Cameras: **0** unless scoped — electrical-legend camera symbols describe the base only
- Add a compact overlay legend + red issue stamp in blank margin: **PROPOSED / FOR REVIEW / NOT FOR EXECUTION**
- Do not overwrite or normalize the sheet’s existing electrical legend

## Placement rules (standing)
1. **Bedside:** first side reached from room entry → **4" + SW/SO**; other bedside → SW/SO only.
2. **Living:** SW/SO above sofa side tables; **10"** when living has sightline to entry/VDP.
3. **Toilet:** cyan SW/SO pair parallel on **dry basin wall** (opposite wet/shower).
4. **Entry:** SW on **latch jamb** opposite door swing; DB at VDP/bell if present.
5. **CM:** one candidate motor per **evidenced** curtain track / curtain-light schedule entry, leader to a **drive-end** endpoint. Do **not** auto-place both ends. Flag stacking side / opening direction / exact track count as review items.
6. **GW+IR:** one pair near each clear AV/TV serve wall that has schedule/furniture evidence. Candidate serve locations, not an approved network design. No invented bedrooms without AV cue.
7. SB boards locate control stations but do **not** prove smart-module quantity. Preserve SB numbers; never silently renumber duplicates — always qualify by room.
8. Empty rooms (Kitchen appliance package, Passage with no control cue) → do not invent standalone points unless a schedule explicitly supports a light/two-way that maps to one SW.

## Gokul Divine room reading (from sheet text + SB schedule — verify yourself)
- Entrance Foyer (top-right): VDP, bell, SB1, main door swing
- Living Dining (center): L-sofa + side tables, TV, dining, balcony/window curtain evidence
- Kitchen (top-left); Passage
- Master Bedroom + Att. Bathroom
- Plan label “Home Office” = **Guest Bedroom** in SB schedule (sofa cum bed + desk) + Guest Bathroom
- Parent’s Bedroom + Parent’s Bathroom
- Powder Bathroom

## Production / QA habits Codex used successfully
- placements.json: one record per plan symbol (qty=1), with room, product, mounting, evidence, assumption, badge box, leader target. Exclude legend samples from totals.
- qa-notes.md: evidence class, every assumption flagged, room-by-room reconciliation, product totals, metadata quirks on the sheet.
- Visual QA: full sheet + crops of entry, bed sides, basins, AV, curtain ends; move crowded callouts into clear space; leaders may cross electrical lines thinly but must not cover furniture symbols or SB text.
- Print plan totals on the sheet margin and reconcile to JSON.
- Do not invent commercial packages, pricing, or cameras.

## Blank-bakeoff delta (fix into this run)
On the synthetic blank, Cursor previously placed **CM on both ends** of each track while Codex placed **one CM per track** at the drive end. Preferred standing for this check: **Codex rule — one CM per evidenced track at a candidate drive end**, with dual-motor called out only if the drawing clearly shows two motors / two stacks. Flag uncertainty instead of doubling.

## What NOT to do
- Do not open or copy Codex baseline placements.json / coordinates for this job (baseline exists only for the human compare after you finish).
- Do not post to Slack/Zoho or touch other repos/apps.
- Do not claim FINAL / FOR EXECUTION.
