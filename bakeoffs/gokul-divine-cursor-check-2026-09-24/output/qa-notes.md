# QA Notes — Gokul Divine PROPOSED automation overlay

**Evidence class:** base-only (single-page discussion electrical layout,
`100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf`, rev blank, dated 03/07/2026,
"DISCUSSION DRAWING", DWG No. 01, PROJ. NO. AS/26/I-RES/05, client Mr. Yogesh
Dedhia, C/503 Gokul Divine, Irla S.V. Road, Vile Parle West, Mumbai 400056).
No matched room-wise working sheet, approved quote, marked revision, or
curtain/RCP drawing was supplied for this check — every product placement
below is therefore a **candidate**, not an approved scope.

**Issue status:** PROPOSED / FOR REVIEW / NOT FOR EXECUTION (stamped on sheet,
top-left blank margin).

## Method

1. Opened the base PDF with PyMuPDF (`fitz`) — 1 page, 1191×842 pt (A3
   landscape), rotation 0.
2. Extracted every text run with `page.get_text("words")` to get exact
   PDF-point coordinates for room labels, furniture callouts, SB switchboard
   tags, dimension strings, and SB-schedule line items (dumped to
   `marking/words_dump.txt`, not shipped as a deliverable but kept for
   traceability alongside the crop renders in `marking/`).
3. Rendered targeted crops at 300–600 dpi with `page.get_pixmap(..., clip=...)`
   to visually confirm furniture shapes, door swings, balcony thresholds and
   wall returns before placing any badge — never relied on the low-res
   thumbnail alone.
4. Built one Python dict per plan symbol with an `anchor` (the evidence point
   on the base) and a `badge` (the drawn symbol's center, nudged only far
   enough to clear base ink), each carrying an explicit `evidence` and
   `assumption` string.
5. Drew the overlay as a separate ReportLab canvas the same page size as the
   base, then merged it onto the **original** base page object with `pypdf`
   (`page.merge_page`) — the base PDF file on disk was never opened for
   writing. SHA-256 of the base file was hashed before and after the merge
   run; both hashes are identical (see `placements.json` →
   `base_pdf_sha256_before_merge` / `_after_merge` / `base_unchanged: true`).
6. Rendered the merged result at 150 dpi for `qa-preview.png`.

## Room reading applied

- Plan label **"HOME OFFICE"** (9'10"×13'6", sofa-cum-bed + work desk) is read
  as **Guest Bedroom** per the SB schedule column headed "Guest Bedroom", per
  `CODEX_LEARNINGS.md`. All placements.json records for this room are labeled
  `Guest Bedroom (plan label 'Home Office')`.
- The schedule box titled **"Master Bathroom"** corresponds to the in-plan
  room labeled **"ATT. BATHROOM"** (10'3"×4'4") — same physical room, two
  names on the same sheet (schedule heading vs. plan room tag). Labeled
  `Att. Bathroom (Master)` in placements.json to keep both names traceable.
- **Kitchen** and **Passage** were left with no automation symbols: both are
  appliance/circulation-only spaces with no SW/SO/AV/curtain schedule cue,
  per the "empty rooms" rule.
- **Cameras: 0.** The sheet's own electrical legend includes a generic
  "CAMERA" light-fixture symbol (unrelated CCTV convention used on many of
  these AS Architects sheets) but no camera scope was given for this check,
  so none were added, per rule.

## Evidence used per product class

| Class | Evidence source |
|---|---|
| SW / SO | Room-entry / bedside / toilet / living-room control rules (`CODEX_LEARNINGS.md` placement rules 1–4), tied wherever possible to an actual in-plan `SB…` tag coordinate rather than an invented point. |
| 4" / 10" | Bedside vs. living placement rule (rule 1–2); 10" chosen for Living & Dining because it has entry/VDP sightline. |
| CM | SB-schedule "curtain light point" line items (4 confirmed: Master Bedroom, Guest Bedroom, Living & Dining, Parent's Bedroom) + the room's own balcony/slider opening. **One CM per evidenced opening, at a candidate drive end — never both ends by default**, per the Codex blank-bakeoff delta. |
| GW / IR | SB-schedule "…for tv and HDMI cable" line items (4 rooms: Master Bedroom, Guest Bedroom, Living & Dining, Parent's Bedroom), paired as separate Surface-Gateway + IR-blaster badges (family-B convention, not combined CG+IR). |
| DB | VDP camera + bell-point + VDP-screen text cluster at the Entrance Foyer, matching SB1 "Main Door Bell point & VDP camera" schedule row. |

## Assumptions and review flags (do not execute without confirming these on site / against other drawings)

1. **CM drive ends are candidates, not confirmed.** This is an electrical-only
   sheet — no RCP or curtain-track drawing was supplied. None of the four
   curtain openings (Master Bedroom north wall, Guest Bedroom's own balcony,
   Living & Dining's balcony, Parent's Bedroom's balcony) shows a drawn
   track, stacking side, opening direction, or single-vs-dual-track split.
   Each CM badge was placed at the wall return judged most likely to be a
   fixed/stacking side (away from a rounded corner where one existed), and
   each `placements.json` record for a CM says so explicitly in its
   `assumption` field. **Flag: verify track count and stacking side before
   ordering hardware — large/dual-track openings may need two motors.**
2. **Master Bedroom entry side is inferred, not drawn.** No door-swing arc is
   printed for the Master Bedroom's own door on this sheet (only the exterior
   Att.-Bathroom-side doors show swing arcs). The "first bedside from entry"
   assignment (west side, near the SB4-series wall cluster) is a reasonable
   read of the passage connection, not a confirmed hinge/latch reading.
   **Flag: confirm against the furniture/architectural plan.**
3. **Parent's Bedroom entry side is inferred** the same way, from the
   top-corridor side table's proximity, not a drawn door swing.
4. **Guest Bathroom's room outline is not clearly delineated** on this
   electrical-only sheet. The SB schedule lists a distinct "Guest Bathroom"
   (geyser/exhaust/pressure-pump/mirror-light/switch), but in the plan the
   only matching evidence is a small basin-shaped symbol plus an
   SB6/SB6A/SB7 tag cluster on the wall shared by Guest Bedroom and Living &
   Dining. **Flag: confirm the Guest Bathroom's actual footprint against the
   furniture/architectural drawing before finalizing switch positions.**
5. **Duplicate SB6/SB6A tag.** The tag pair "SB6/SB6A" appears twice on the
   sheet at two different physical locations — once on Guest Bedroom's own
   west wall (~421,393–413) and again on the Guest-Bedroom/Living-Dining
   boundary wall (~566–578,396–410). Per rule, this was **not silently
   renumbered**; both locations are visible in the crops under `marking/`.
   **Flag: confirm with the electrical consultant whether this is one gang
   spanning two faces of the same partition or a genuine duplicate/typo.**
6. **Entrance Foyer door swing** is not drawn (only the ENTRY/EXIT arrow and
   SB1 dot are shown); the SW badge's "latch jamb opposite door swing"
   placement is a candidate side, not a confirmed reading.
7. **Guest Bedroom and Parent's Bedroom GW/IR walls are inferred** from the
   nearest SB tag associated with a "…tv and HDMI…" schedule line, because
   (unlike Master Bedroom, which has an explicit in-plan "tv unit" symbol)
   no TV-console furniture symbol is drawn for these two rooms.
8. **SB board evidence proves control-station location, not smart-module
   quantity** (per rule 7): every SW/SO placement above is a proposal keyed
   to an existing SB tag or furniture cue, not a confirmed automation-module
   count.

## Room-by-room reconciliation (rooms with $\ge$1 product)

| Room | SW | SO | 4" | 10" | CM | GW | IR | DB |
|---|---|---|---|---|---|---|---|---|
| Entrance Foyer | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| Living & Dining Room | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 0 |
| Master Bedroom | 2 | 2 | 1 | 0 | 1 | 1 | 1 | 0 |
| Att. Bathroom (Master) | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Guest Bedroom ('Home Office') | 2 | 2 | 1 | 0 | 1 | 1 | 1 | 0 |
| Guest Bathroom | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Parent's Bedroom | 2 | 2 | 1 | 0 | 1 | 1 | 1 | 0 |
| Parent's Bathroom | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Powder Bathroom | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **12** | **11** | **3** | **1** | **4** | **4** | **4** | **1** |

Kitchen and Passage: 0 (no control cue, per rule 8).

Sums above match `placements.json` → `product_totals` exactly; cameras = 0.

## Base-preservation checks

- Base PDF SHA-256 unchanged before/after merge (see `placements.json`).
- Page size/orientation unchanged (1191×842 pt, landscape) in
  `MARKING_PROPOSED.pdf`.
- No wall, furniture, SB tag, dimension, schedule, title block, or the
  sheet's own electrical/light legend was edited, redrawn, or covered by an
  opaque overlay element — every overlay badge is a small outlined/filled
  symbol (≤7 pt radius) with a thin dashed leader; leaders were routed to
  cross only dashed wiring-loop lines, never furniture outlines or SB text
  (checked per-room in `marking/qa2_*.png` and `marking/qa_*.png`).
- All eight requested product classes are represented (SW, SO, 4", 10", CM,
  GW, IR, DB); cameras = 0 as required.

## Metadata observations (unchanged from source, flagged for completeness)

- Title block shows "DISCUSSION DRAWING" / blank Rev. No. / date 03/07/2026 —
  consistent with a first-issue base, not yet a marked/approved revision.
- The Revisions table on the sheet is empty (normal for a first issue).
- File name says "v2" while the title block's own DWG No. is "01" with no
  revision letter — a naming-vs-title-block mismatch worth flagging to the
  architect/consultant per QA convention, though it does not affect this
  proposal's geometry.
