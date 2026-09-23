# QA Notes — Blank Marking Bake-off (Cursor cloud / Grok arm)

Base: `inputs/BLANK_SYNTHETIC_1BHK.pdf` (A3 landscape, 1190.55 × 841.89 pt). Evidence class per
`SKILL.md`: **base-only** — no matched quote/working sheet, no prior marked revision. Status stamp
applied: **PROPOSED / FOR REVIEW / NOT FOR EXECUTION**.

All coordinates below were read directly from the base PDF's own vector paths and text spans
(`fitz.get_drawings()` / `get_text('dict')`) — nothing was eyeballed from the preview PNG. Every
badge in `placements.json` carries a `center_topdown_pt` and (where applicable) the real feature
it leaders to, so every symbol is traceable back to a drawn wall/basin/table/curtain-track/door.

## Room-by-room rule application

| Room | Rule(s) applied | Marks |
|---|---|---|
| Master Bedroom | 1 (bedside), 5 (CM) | CM×2 (curtain-track ends), 4"+SW+SO (first/east bedside), SW+SO (other/west bedside) |
| Living / Dining | 2 (living), 5 (CM), 6 (GW+IR) | SW+SO×2 (both sofa side tables), 10" (open-plan sightline to Passage/Foyer), CM×2 (curtain-track ends), GW+IR (beside the only TV on the sheet) |
| Kitchen | — | none (no furniture/fixture on this base matches any rule — see "Explicitly skipped" below) |
| Master Bath | 3 (toilet) | SW+SO (bracket, parallel on basin/west wall) |
| Powder | 3 (toilet) | SW+SO (bracket, parallel on basin/west wall) |
| Passage | — | none (empty room, no rule match) |
| Guest Bedroom | 1 (bedside) | 4"+SW+SO (first/west bedside), SW+SO (other/east bedside). No CM — no curtain track drawn in this room (brief states only master + living have curtain tracks). No GW/IR — no TV drawn here. |
| Guest Bath | 3 (toilet) | SW+SO (bracket, parallel on basin/west wall) |
| Foyer / Entry | 4 (entry) | SW (latch wall, opposite door swing), DB (at entry) |

## Placement logic and assumptions that need confirmation

1. **Bedside "first side" (Master + Guest bedrooms).** No door swing is drawn for either
   bedroom door on this blank base (only the Foyer/main door has a swing arrow). To apply rule 1
   at all, I used the corridor-adjacency heuristic: Master Bedroom's east wall (shared with
   Living/Dining) and Guest Bedroom's west wall (shared with Passage) were treated as the
   presumed access sides, so the side table nearer that wall got the 4"+SW/SO treatment and the
   far table got SW/SO only. **Flag: confirm actual bedroom door locations/swing on the real
   drawing** — this assumption directly decides which nightstand gets the 4" panel.
2. **No bedroom "entry SW."** Rule 4 ("Entry SW on latch wall opposite door swing") was applied
   only to the Foyer/main door, which is the only door swing actually drawn on this sheet. I did
   not add a separate entry SW inside Master/Guest bedrooms since no door swing evidence exists
   for those doors — adding one would be inventing geometry not on the base. This is a
   deliberate, more conservative choice than some prior bake-off runs on similarly-named files.
3. **Wall-projection for tables not directly against a wall.** In both bedrooms and the living
   room, the furniture is drawn offset toward one side (bed/sofa left-of-room-center with one
   nightstand tight against a wall and the other floating in open floor area). For the
   floating-side table, the SW/SO badge was projected onto the nearest available wall on that
   side (e.g., Master Bedroom's east table → east wall badges, ~110pt lateral offset) rather than
   invented mid-floor. Leader lines connect each badge back to its real table so the offset is
   visible and auditable, not hidden.
4. **Living → Passage/Foyer opening treated as open-plan, not a door.** The gap between
   Living/Dining's south wall and Passage is the same 20pt wall-thickness gap used everywhere
   else on the sheet, with no door leaf or swing drawn there — consistent with the brief's "open
   plan" framing. No separate SW was added at that opening; only the 10" screen (rule 2, "10\" if
   living sees entry") was placed on the south wall, since that is the only symbol the brief
   actually specifies for this condition.
5. **Toilet SW/SO orientation ("parallel on dry basin wall").** All three basins (Master Bath,
   Powder, Guest Bath) sit against a west wall. The SW/SO bracket pair was stacked vertically
   (parallel to that wall) and offset above/below the basin footprint so the basin symbol stays
   fully visible, per the "do not cover furniture" rule in `SKILL.md`.
6. **Foyer door swing reading.** The base draws a single vertical leaf line at the door hinge
   (x≈480, at the south/exterior wall) with a rightward arrow, read as: hinge at the wall, leaf
   swinging open toward increasing x (east) into the room. The latch/unswept wall is therefore to
   the **west** of the hinge, which is where the entry SW was placed. **Flag: confirm this swing
   reading against the real door schedule** — swing-arrow conventions vary by drafter.
7. **No SO or DB duplicated at main entry.** Rule 4 names only "SW ... DB at entry" — no SO was
   added at the Foyer, matching the brief literally rather than the broader bedside pattern.
8. **Kitchen and Passage left unmarked.** Neither room has any furniture, TV, basin, curtain
   track, or door swing drawn on this synthetic base, so no placement rule (1–6) is triggered.
   Per `SKILL.md` ("never assume... map SW to confirmed points"), no automation was invented for
   these rooms. **Flag: once a scoped quote/working sheet is available, revisit Kitchen/Passage.**
9. **No cameras anywhere** — explicit exclusion per rule 6, confirmed: zero camera symbols in
   `placements.json`.
10. **Family/colors used** (rule 7): pink = on-wall SW/SO, cyan = bracket SW/SO (used for all
    three toilets), orange = 4", peach = 10", purple = CM, yellow = surface GW, black = IR + DB.
    No undefined/legacy abbreviations (`CG+IP`, `SE`, `WSW`, etc.) appear anywhere in this
    marking, so nothing needed flagging against the legend families in `SKILL.md`.

## Validation performed

- Rendered the merged PDF at 2× via PyMuPDF and visually inspected every room at zoom (see
  `qa-preview.png`) — no badge covers a wall, door swing, dimension, room label, or furniture
  outline (two initial overlaps against nightstand rects were caught this way and corrected by
  offsetting badges above/below the furniture footprint instead of beside it).
- Every symbol kind used in the drawing (`SW`, `SO`, `4"`, `10"`, `CM`, `GW`, `IR`, `DB`) appears
  in the on-sheet legend strip drawn under the stamp banner — no undefined symbol was introduced.
- `placements.json` totals were cross-checked against `RESULT.md` by summing `Counter(kind)` in
  code (not typed by hand), so the schedule and the drawing cannot silently drift apart.
- Original base PDF content (walls, furniture, room labels, title block, dimensions) was merged
  via `pypdf.PageObject.merge_page`, i.e. the source page object is untouched and the overlay is a
  second vector layer on top — no rasterization of the base occurred, so it stays crisp and
  editable at any zoom.

## Outstanding items before this can move past PROPOSED

- Confirm real door swings for Master Bedroom and Guest Bedroom (item 1/2 above).
- Confirm Foyer door hinge/swing reading against the actual door schedule (item 6).
- Obtain a scoped quote/working sheet to decide whether Kitchen and/or Passage need automation
  (item 8) and to confirm SO quantities generally (SW locates a control point; SO quantity needs
  independent scope confirmation per `SKILL.md`).
