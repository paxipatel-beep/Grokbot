# RESULT — Gokul Divine PROPOSED automation overlay (Cursor cloud marking check)

**Date:** 2026-09-24 (Asia/Calcutta) · **Status:** PROPOSED / FOR REVIEW / NOT FOR EXECUTION
**Base:** `layout/100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf` (A3 landscape, 1 page, unchanged)
**Evidence class:** base-only (discussion electrical layout; no matched working sheet, quote, or curtain/RCP drawing supplied)

## Method (one-liner)

Re-derived all geometry independently from the base PDF with PyMuPDF (text-word
coordinates + 300–600 dpi clip renders), drew a separate ReportLab vector
overlay keyed to that evidence, and merged it onto the original base page with
pypdf (base bytes/page size unchanged, SHA-256 verified) — never copying
coordinates from any other job.

## Product totals

| Product | Qty | Notes |
|---|---:|---|
| SW (switch) | 12 | 8× magenta on-wall, 4× cyan wall-bracket (toilets) |
| SO (socket) | 11 | 7× magenta on-wall, 4× cyan wall-bracket (toilets) |
| 4" (bedside screen) | 3 | Master Bedroom, Guest Bedroom, Parent's Bedroom |
| 10" (living screen) | 1 | Living & Dining Room |
| CM (curtain motor) | 4 | One per evidenced curtain-light schedule entry × candidate drive end (not both ends) |
| GW (surface gateway) | 4 | One per AV/TV-evidenced room |
| IR (IR blaster) | 4 | Paired with each GW, separate badge (family-B convention) |
| DB (doorbell/VDP) | 1 | Entrance Foyer |
| **Cameras** | **0** | Not scoped for this check |

Totals reconcile exactly to `output/placements.json` → `product_totals` and to
the room-by-room table in `output/qa-notes.md`.

## Room reading

- Plan label **"Home Office"** → read as **Guest Bedroom** per the SB
  schedule (sofa-cum-bed + work desk), per `CODEX_LEARNINGS.md`.
- Schedule box **"Master Bathroom"** → physically the in-plan **"Att.
  Bathroom"** room next to Master Bedroom.
- **Kitchen** and **Passage** carry no automation symbols (appliance-only /
  no control cue).

## Curtain motor rule applied

Four rooms have an explicit "curtain light point" SB-schedule entry (Master
Bedroom, Guest Bedroom, Living & Dining Room, Parent's Bedroom). Each gets
**exactly one** CM badge at a candidate drive-end wall return — never both
ends by default, per the Codex blank-bakeoff delta. Exact track count and
stacking side are **not** shown on this electrical-only base and are flagged
as review items in `qa-notes.md`.

## Deliverables in this folder (`output/`)

1. `MARKING_PROPOSED.pdf` — original vector base + overlay, stamped PROPOSED / FOR REVIEW / NOT FOR EXECUTION
2. `placements.json` — one record per plan symbol, with evidence + assumption per record
3. `qa-notes.md` — evidence class, method, room-by-room reconciliation, flagged assumptions
4. `RESULT.md` — this file
5. `qa-preview.png` — full-sheet 150 dpi render of the merged PDF

Reproducible generator: `../make_marking.py` (run from the bakeoff folder root;
writes all five files into `output/`).

## Known review items (see `qa-notes.md` for full list)

- CM drive-end / stacking-side / track-count assumptions (all 4 CMs).
- Master Bedroom and Parent's Bedroom "first bedside from entry" inferred
  without a drawn door-swing arc.
- Guest Bathroom's physical room outline is not clearly delineated on this
  electrical-only sheet (evidence: schedule row + small basin symbol + SB
  cluster on a shared wall).
- Duplicate "SB6/SB6A" tag appears at two physical locations — flagged, not
  silently renumbered.
