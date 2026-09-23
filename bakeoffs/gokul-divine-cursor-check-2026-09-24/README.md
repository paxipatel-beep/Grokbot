# Gokul Divine — Cursor cloud marking check (2026-09-24)

PROPOSED viwaves automation overlay on the real Gokul Divine electrical
layout, produced independently per `brief/CODEX_LEARNINGS.md`,
`brief/SKILL.md`, `brief/LEARNINGS.md`, and `brief/BRIEF.md`.

Evidence class: **base-only** (discussion electrical layout). Issue status:
**PROPOSED / FOR REVIEW / NOT FOR EXECUTION**.

## Folder layout

- `brief/` — the uploaded task brief and rule/learnings files (copied in for a self-contained PR).
- `layout/` — the immutable base PDF (`100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf`), unmodified.
- `marking/` — a curated set of full-sheet/region renders used to re-derive geometry, plus the raw PDF text-word coordinate dump (`words_dump.txt`) used as evidence for every placement.
- `make_marking.py` — reproducible generator: reads `layout/`, writes the five deliverables into `output/`.
- `output/` — the five required deliverables:
  1. `MARKING_PROPOSED.pdf`
  2. `placements.json`
  3. `qa-notes.md`
  4. `RESULT.md`
  5. `qa-preview.png`

## Reproduce

```bash
pip install reportlab pypdf PyMuPDF pillow
python3 make_marking.py
```

Regenerates all five files under `output/` from the base PDF and the
hard-coded, evidence-cited placement list in `make_marking.py`. The base PDF
is never opened for writing; SHA-256 of the base file is verified unchanged
before/after each run (printed to stdout and recorded in `placements.json`).

## Scope note

This work was produced under `bakeoffs/gokul-divine-cursor-check-2026-09-24/`
only; no other files in this repository were touched.
