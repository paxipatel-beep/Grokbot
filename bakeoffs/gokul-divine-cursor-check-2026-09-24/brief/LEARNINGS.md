# VLights / viwaves automation marking — general learnings

Privacy-safe only. No client identities, addresses, quote numbers, or product quantities.

Last visual study refresh: 2026-09-05 (Asia/Kolkata).

## Evidence hierarchy

1. Latest approved base drawing (furniture / architectural / RCP / electrical / looping) — immutable geometry.
2. Matched room-wise working sheet or approved quote — scope and quantity authority.
3. Latest same-project marked revision — graphic convention authority.
4. Legend printed on the current sheet — symbol meaning (overrides remembered patterns).

Classify before learning or marking: complete base-to-marked pair | revision series | marked-plus-scope | marked-only | base-only | quote-only.

Prefer finished teachers whose titles contain `viwaves Automation marking`, `AUTOMATION MARKING`, `SWITCH SOCKET MARKING`, or `LOOPING LAYOUT` (full/semi). Room-wise electrical sheets (SB / RL / HL only) are bases, not automation-convention teachers.

## Issue status discipline

- Furniture-only proposals are `PROPOSED` / `FOR REVIEW` / `NOT FOR EXECUTION`.
- Product-complete overlays still need matching approved scope before execution.
- Never invent a full package from furniture alone; never copy another job’s counts.

## Legend families (copy the sheet’s own legend)

Do not normalize colors or abbreviations across projects. Three finished families recur:

### A. Panel / wall family (common on looping + switch-socket finished sheets)

- Orange `4"` / `10"` screens (size in the badge).
- Black `CG+IR` = combined gateway + IR blaster.
- Magenta/pink `SW` / `SO` = **on wall**.
- Cyan/teal/blue `SW` / `SO` = **on panel** (joinery / decorative panel), not “wall bracket” wording.
- Purple `CM` = curtain motor.
- Optional scoped extras: door bell, camera square.

### B. Looping / viwaves simplified family (common on electrical-layout automation overlays)

- Cyan/light-blue `SW` / `SO` = **on wall bracket**.
- Magenta/pink `SW` / `SO` = **on wall**.
- Yellow **square** = Surface Gateway; yellow **circle** = Conceal Gateway (shape encodes mount).
- Separate black **IR Blaster** circle (not combined `CG+IR`).
- Purple `CM`; orange screens; door-bell oval when scoped.
- Quantity tables on these sheets may use different wording than the overlay legend (e.g. “keypad on wall” vs badge `SW`) — reconcile wording before counting.

### C. Board-tied product-complete overlays (electrical SB preserved)

- Cyan (or cyan/dark-blue pair) `SW` / `SO` placed **at existing switchboard** marks; note may say wall-bracket convention.
- Separate `GW` and `IR` circles (not always `CG+IR`).
- Purple/magenta `CM`; orange screens.
- Keep original lighting loops and SB numbering; flag duplicates/omissions — never renumber silently.

**Critical delta:** cyan/blue does **not** always mean “panel”. On family A it often means panel; on family B it means wall bracket; on family C it means board-tied / wall-bracket convention. Read the printed legend every time.

## SW / SO mount variants — how they appear

- Same letters `SW` / `SO`; **fill color** encodes mount (wall vs panel vs wall-bracket).
- Pair `SW`+`SO` side-by-side at one control station when both are scoped.
- On electrical bases, automation badges sit **adjacent to** solid red SB rectangles (or outlined “automation panel” rectangles) — do not float away from the board.
- Some finished sheets add hardware notes (button-count / model class for switches). Treat as project-specific callouts, not a global default.
- Switch-socket-scoped jobs still often show `CG+IR` / `CM` / screens when those products are in the same issue set — scope the option label, do not assume legend = full package.

## Gateway / IR style

| Family | Style |
|--------|--------|
| A (panel/wall) | Combined black `CG+IR` badge, usually one per automated zone near AV / central ceiling |
| B (simplified) | Separate Surface vs Conceal gateway (yellow square vs circle) **plus** separate black IR circle; may co-locate on a wall |
| C (board-tied) | Separate `GW` + `IR` circles per zone |

Never mix combined and separate styles on one sheet unless the printed legend shows both.

## Curtain motors (CM)

- Default graphic: purple `CM` at confirmed track end(s).
- On some electrical-automation overlays, motors are also (or instead) called out with red leaders: **“2 POINTS FOR CURTAIN MOTOR”** — treat callouts as quantity/placement authority for that opening, then place badges consistently with the legend.
- Never assume one motor per window; confirm track count, stacking side, opening direction.
- Large balcony / multi-track openings commonly show paired motors when confirmed.

## Screens

- `4"` and `10"` size badges (usually orange family).
- Place only when scoped: typically 10" at primary living/central control; 4" at bedroom entry / secondary control.
- Omit when option is without-screen / switch-socket-only unless the sheet already shows them as issued scope.

## Relationship to existing SB / electrical marks

- Preserve base electrical: solid red SB, green/magenta light points, fan symbols, dashed looping, cove/strip lines.
- Automation is a **high-contrast overlay**, not a replacement of SB geometry.
- Map `SW` to confirmed boards when an electrical base exists; an electrical loop locates boards but does **not** prove smart-module quantity.
- Room electrical sheets (living/master style) with SB / RL / HL / FN only are **bases for placement**, not finished automation teachers.

## Revision badges and on-drawing QA

- Title-block revision (`R1`, `R2`, `01`, etc.) is primary revision identity; blank revision tables on first issues are normal.
- Finished sheets may show **hand / red-ink quantity edits** in a SYMBOL–QUANTITY table (strike-through old, arrow to new). Prefer visible table over filename alone.
- Good teacher sheets include verify-on-site notes for quantities, mounting, and curtain opening.
- QA flags seen on teachers: empty formal SYM/DESCRIPTION table while overlays are present; qty-table wording ≠ overlay legend wording; duplicate/missing SB IDs left flagged.

## Quantity reconciliation (rules only — do not store job counts)

- Count room-by-room and independently by product class.
- Commercial accessories (brackets, boxes, adaptors, install, setup) may have no plan symbol.
- Full / semi / switch-socket-only / switch-only / with-screen / without-screen are mutually exclusive unless documents say otherwise.
- Revisions: list add / remove / move / reclassify; show old / new / difference.

## QA before issue

- Every overlay symbol appears in the **active** legend on that sheet.
- Schedule totals equal plan totals (after reconciling terminology drift).
- Leaders terminate at intended wall / panel / curtain / equipment; no floating symbols.
- Base drawing intact (doors, furniture, dimensions, notes, SB IDs readable).
- Report stale filename vs title-block vs quote metadata.
- Use `PROPOSED` / `FOR REVIEW` / `NOT FOR EXECUTION` until scope, counts, product type, and site conditions reconcile.

## Output

`output/pdf/<CLIENT OR PROJECT> - <MONTH YYYY>/` with revision + ISO date in filenames where applicable. No loose finals under `output/pdf/`.

## Deltas vs `skill/marking-system.md` (study refresh)

1. **Cyan meaning is family-specific** — wall-bracket (B) vs panel (A) vs board-tied (C); marking-system already warned to copy the family, but cyan≠panel must be explicit.
2. **Surface vs Conceal gateways are shape-coded** (yellow square vs yellow circle) in family B — keep that distinction.
3. **CM callout text** (“N POINTS FOR CURTAIN MOTOR”) coexists with purple `CM` badges on electrical overlays.
4. **Qty-table vs badge terminology drift** (e.g. keypad vs SW) is a real QA failure mode on finished teachers.
5. **Hardware model / button-count notes** appear on some switch-socket issues — project-local, not global legend.
6. **Semi-automation looping** sheets may still print the full panel-family legend (`CG+IR`, screens, wall/panel SW/SO); option name alone does not strip symbols — reconcile to matched scope.
7. **Room electrical sheets** remain SB/loop bases; do not treat them as automation marking convention sources.
