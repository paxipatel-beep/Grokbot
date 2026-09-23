---
name: Automation layout marking
description: >-
  use this when creating, revising, auditing, or issuing VLights/viwaves
  automation markings on furniture, architectural, RCP, electrical, or
  looping-layout PDFs
---
# Automation layout marking

Produce a traceable automation overlay without changing the client base drawing.

## Evidence hierarchy
1. Latest approved architectural / furniture / RCP / electrical / lighting drawing — immutable base.
2. Matched room-wise working sheet or approved quote — scope and quantity authority.
3. Latest marked revision from the same project, option, floor, room — graphic-convention authority.
4. Legend printed on the current sheet — symbol meaning (overrides remembered patterns).

Never merge sources because names look similar. Verify title block, site, floor, room set, option, quote number, revision, and date. Classify evidence before acting: complete base-to-marked pair, revision series, marked-plus-scope, marked-only, base-only, or quote-only.

## Base preservation
- Preserve walls, doors, furniture, dimensions, scale, orientation, border, title block, room names, existing electrical/looping marks.
- Add automation as a separate high-contrast overlay.
- Do not cover door swings, furniture, dimensions, notes, existing legends, or switchboard IDs.
- Copy the current drawing family’s legend; do not normalize symbols across projects.

## Legend families
Common panel family: orange `4"` / `10"`, black `CG+IR`, magenta wall `SW`/`SO`, cyan panel `SW`/`SO`, purple `CM`, black camera square when scoped.

Looping-layout / viwaves simplified family may use: cyan `SW`/`SO` = wall bracket, magenta `SW`/`SO` = on wall, separate surface/conceal gateway, separate IR blaster. Preserve the source family exactly.

Project-specific labels (`CG+IP`, `SE`, `WSW`, `ONLY GATEWAY`, `SWITCH ON INVERTER`) stay project-specific — flag undefined abbreviations.

## Placement
- Map `SW` to confirmed switchboard/control points. An electrical loop locates boards but does not prove smart-module quantity.
- Add `SO` only where matched scope or board schedule confirms it.
- Keep wall, wall-bracket, and panel points visually distinct.
- Screens only when size is scoped; place at deliberate entry/central control.
- Gateways and IR inside the served room with practical power/network access and IR line-of-sight.
- Curtain motors at confirmed curtain-track end — never assume one motor per window; verify track count, stacking side, opening direction.
- Do not add cameras or other products absent from scope.

## Quantity and revision
- Count room-by-room and independently by product; reconcile to quote/working sheet.
- Commercial accessories without plan symbols stay in a separate check.
- Treat full / semi / switch-socket-only / switch-only / with-screen / without-screen as mutually exclusive options unless docs say otherwise.
- For revisions: list additions, removals, moves, reclassifications; show old / new / difference.
- Never silently renumber duplicate/missing switchboard IDs — mark points, flag conflict, wait for confirmation.

## QA and issue status
Render every page at readable resolution. Confirm every overlay symbol is in the legend; schedule totals equal plan totals; leaders terminate at intended wall/panel; no floating symbols; report stale filename/title-block/quote metadata.

Use `PROPOSED`, `FOR REVIEW`, or `NOT FOR EXECUTION` until scope, counts, product type, and site conditions reconcile. Do not call a drawing final while a source mismatch, undefined legend item, duplicate/missing switchboard ID, or quantity discrepancy remains.

## Output
Store finals under `output/pdf/<CLIENT OR PROJECT NAME> - <MONTH YYYY>/`. Run output validator before delivery when available.

## Privacy
Never store customer identities, addresses, quotes, quantities, or raw drawings in reusable skills or global durable memory. Client-specific status belongs in the client folder or Notion client index.
