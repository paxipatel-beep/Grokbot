# RESULT — Blank Marking Bake-off 2026-09-23 (Cursor cloud / Grok arm)

**Status: PROPOSED / FOR REVIEW / NOT FOR EXECUTION** — base-only evidence, no client
quote/scope. See `qa-notes.md` for the full room-by-room rule trail and every assumption that
still needs confirmation before this can move past PROPOSED.

## Deliverables
- `output/MARKING_PROPOSED.pdf` — original vector base + automation overlay (original walls,
  furniture, dimensions, room labels, title block untouched; overlay merged with `pypdf`)
- `output/placements.json` — every badge's kind/family/room/coordinates + totals (machine-checked)
- `output/qa-notes.md` — placement logic, wall/rule traceability, and open confirmation items
- `output/qa-preview.png` — 2× rendered preview with on-sheet legend, used for the visual QA pass
- `RESULT.md` — this file

## Symbol totals (whole sheet)

| Symbol | Count |
|---|---|
| SW | 10 |
| SO | 9 |
| 4" | 2 |
| 10" | 1 |
| CM | 4 |
| GW | 1 |
| IR | 1 |
| DB | 1 |
| **Total marks** | **29** |

## Totals by room

| Room | SW | SO | 4" | 10" | CM | GW | IR | DB |
|---|---|---|---|---|---|---|---|---|
| Master Bedroom | 2 | 2 | 1 | — | 2 | — | — | — |
| Living / Dining | 2 | 2 | — | 1 | 2 | 1 | 1 | — |
| Kitchen | — | — | — | — | — | — | — | — |
| Master Bath | 1 | 1 | — | — | — | — | — | — |
| Powder | 1 | 1 | — | — | — | — | — | — |
| Passage | — | — | — | — | — | — | — | — |
| Guest Bedroom | 2 | 2 | 1 | — | — | — | — | — |
| Guest Bath | 1 | 1 | — | — | — | — | — | — |
| Foyer / Entry | 1 | — | — | — | — | — | — | 1 |
| **Total** | **10** | **9** | **2** | **1** | **4** | **1** | **1** | **1** |

No cameras were placed anywhere (explicit exclusion per rule 6). Kitchen and Passage carry no
marks — no furniture/fixture/TV/curtain-track/door-swing evidence on this blank base matches any
placement rule for those two rooms (see `qa-notes.md` item 8).

## How it was built
`make_blank_marking.py` reads the base PDF's own vector geometry (walls, furniture rects, curtain
tracks, basin circles, door-swing line/arrow) via PyMuPDF, computes badge positions from that real
geometry, draws the viwaves-family badges + dashed leader lines with reportlab onto a same-size
overlay PDF page, and merges that overlay onto the **original** base page with `pypdf` (no
rasterization of the base). Pillow is used to build the QA-preview legend strip and to render a
raster preview of the merged PDF for visual inspection.
