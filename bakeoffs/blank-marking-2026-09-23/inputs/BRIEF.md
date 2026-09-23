# Blank marking bake-off 2026-09-23

Compare **Grok build** (local Python overlay) vs **Codex CLI** on the same blank synthetic base.

## Evidence
- **base-only** synthetic furniture outlines on blank A3 — no client quote/scope
- Stamp: **PROPOSED / FOR REVIEW / NOT FOR EXECUTION**

## Base
- PDF: `/workspace/vlights-quote-projects/blank-marking-bakeoff-2026-09-23/layout/BLANK_SYNTHETIC_1BHK.pdf` (A3 landscape ~1191×842)
- Preview: `.../layout/preview-1.png`

## Rooms on sheet
Master Bedroom + Master Bath, Powder, Living/Dining, Kitchen, Guest Bedroom + Guest Bath, Foyer/Entry, Passage.
Furniture hints: beds + side tables, sofa + side tables, TV, basins, curtain tracks (master + living), entry door swing.

## Placement rules (MUST)
1. Bedside: first-side wall when entering → 4" + SW/SO; other bedside → SW/SO only
2. Living: SW/SO above sofa side tables; 10" if living sees entry (open plan → place 10")
3. Toilet: SW/SO parallel on dry basin wall
4. Entry: SW on latch wall opposite door swing; DB at entry
5. CM only on curtain-track ends
6. GW+IR near TV/AV; no cameras
7. viwaves simplified family: pink SW/SO on-wall; cyan SW/SO bracket; orange 4"; peach 10"; purple CM; yellow surface GW; black IR circle; black DB

## Ref
- Skill: `/home/box/agent-data/workflows/automation-layout-marking/SKILL.md`
- Badge helpers: `/workspace/new-layout/make_marking.py`
- Learnings: `/workspace/viwaves-learn/LEARNINGS.md` (if present)

## Outputs
### Grok path → `output/grok/`
### Codex path → `output/codex/`
Each must write:
1. `MARKING_PROPOSED.pdf`
2. `placements.json`
3. `qa-notes.md`
