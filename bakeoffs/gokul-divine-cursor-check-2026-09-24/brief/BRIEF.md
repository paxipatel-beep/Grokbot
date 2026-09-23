# Gokul Divine — Cursor cloud marking check (with Codex learnings)

Date: 2026-09-24 Asia/Calcutta
Evidence class: **base-only** (discussion electrical layout)
Required stamp: **PROPOSED / FOR REVIEW / NOT FOR EXECUTION**

## Goal
Produce a fresh proposed viwaves automation overlay on the real Gokul Divine electrical layout, applying `CODEX_LEARNINGS.md` + `SKILL.md` + `LEARNINGS.md`. Independently re-derive all geometry. Do not copy prior placement coordinates.

## Attached / uploaded inputs
- Base PDF: `100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf` (A3 landscape, 1 page)
- Previews: `v2-1.png`, `crop-plan.png`, `crop-legend.png`, `crop-title.png`, `text.txt`
- `brief/SKILL.md`, `brief/LEARNINGS.md`, `brief/CODEX_LEARNINGS.md`, `brief/BRIEF.md`

## Deliverables (write under bakeoffs/gokul-divine-cursor-check-2026-09-24/output/ in the repo, and copy the same files to /opt/cursor/artifacts/gokul-divine-cursor-check-2026-09-24/)
1. `MARKING_PROPOSED.pdf` — original vector base + overlay, stamped
2. `placements.json`
3. `qa-notes.md`
4. `RESULT.md` — product totals table + method one-liner
5. `qa-preview.png` — readable full-sheet render (~150 dpi) with a small legend strip if helpful

## Success criteria
- Base PDF vectors/page box preserved; SHA-256 of base content path unchanged
- All eight product classes present when used: SW, SO, 4", 10", CM, GW, IR, DB; cameras = 0
- CM follows Codex learnings (one per evidenced track, not both ends by default)
- Room reading treats Home Office as Guest Bedroom per SB schedule
- Totals in RESULT.md reconcile to placements.json and printed margin schedule
- PR opened with only files under `bakeoffs/gokul-divine-cursor-check-2026-09-24/`
