#!/usr/bin/env python3
"""
Gokul Divine — PROPOSED viwaves automation overlay generator (Cursor cloud check).

Method
------
1. Geometry (room labels, furniture labels, SB switchboard tag positions, balcony
   dimensions, curtain-light schedule entries) was re-derived directly from the
   supplied base PDF using PyMuPDF (fitz): page.get_text("words") for text-anchor
   coordinates and page.get_pixmap(..., clip=...) renders at 300-600 dpi for visual
   confirmation of furniture / door / balcony geometry. No coordinates were copied
   from any prior job or from memory.
2. All coordinates in this script are PDF points, top-left origin, y-down
   (fitz/PyMuPDF convention), matching the coordinates recorded in placements.json.
   They are converted to ReportLab's bottom-left/y-up convention only at draw time.
3. A separate vector overlay is drawn with ReportLab onto a blank page of the same
   size or orientation as the base, then merged onto the ORIGINAL base PDF page with
   pypdf. The base page's own content stream is never edited or rasterized.
4. SHA-256 of the base PDF is recorded before and after merge to prove the base
   bytes feeding the merge were untouched (the merge reads the original file only).

Run:
    python3 make_marking.py
"""
import hashlib
import json
import math
import os

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PDF = os.path.join(HERE, "layout", "100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf")
OUT_DIR = os.path.join(HERE, "output")
OVERLAY_PDF = os.path.join(OUT_DIR, "_overlay.pdf")
FINAL_PDF = os.path.join(OUT_DIR, "MARKING_PROPOSED.pdf")
PLACEMENTS_JSON = os.path.join(OUT_DIR, "placements.json")

PAGE_W, PAGE_H = 1191.0, 842.0  # A3 landscape points, taken from the base page rect

# ---------------------------------------------------------------------------
# Family-B (viwaves simplified) badge colors — copied from the sheet's own
# electrical-legend palette conventions per SKILL.md / LEARNINGS.md, not
# normalized against any other job's colors.
# ---------------------------------------------------------------------------
MAGENTA = HexColor("#E6007E")   # on-wall SW / SO
CYAN = HexColor("#00AEEF")      # wall-bracket SW / SO (toilets)
ORANGE = HexColor("#F7941D")    # 4" / 10" screens
PURPLE = HexColor("#7B2D8E")    # curtain motor CM
YELLOW = HexColor("#FFD400")    # surface gateway GW (square)
IR_BLACK = HexColor("#111111")  # IR blaster (black circle)
DB_BLACK = HexColor("#111111")  # doorbell / VDP badge (black oval)
STAMP_RED = HexColor("#D0021B")

# ---------------------------------------------------------------------------
# placements — one record per plan symbol (qty always 1). Coordinates are in
# PDF points, fitz convention (origin top-left, y increases downward), derived
# from marking/words_dump.txt (page.get_text("words")) and the high-dpi crops
# saved under marking/. "anchor" is the evidence point on the base drawing
# (SB tag / furniture label / dimension label); "badge" is where the overlay
# symbol center is drawn (offset from anchor only far enough to avoid
# overlapping base ink); leader=True draws a thin line from badge to anchor.
# ---------------------------------------------------------------------------
PLACEMENTS = [
    # ---------------- Entrance Foyer ----------------
    dict(id="EF-DB-1", room="Entrance Foyer", product="DB", mount="wall, at VDP/bell cluster",
         anchor=(708.0, 128.0), badge=(722.0, 108.0), leader=True,
         evidence="Plan text 'vdp camera' (700.6,121.0), 'bell point' (707.7,125.0), 'vdp screen' "
                  "(705.8,140.7); SB1 'Main Door Bell point & VDP camera' schedule row.",
         assumption="Badge offset up-left of the VDP/bell text cluster so it does not sit on top of "
                    "the printed words; exact bell-push mounting height not shown on this sheet."),
    dict(id="EF-SW-1", room="Entrance Foyer", product="SW", mount="on wall, latch jamb (candidate)",
         anchor=(719.8, 136.8), badge=(760.0, 118.0), leader=True,
         evidence="In-plan SB1 tag at (719.8,136.8) inside Entrance Foyer, matching the "
                  "'Main Door / Bell point & VDP camera / main door light point / name plate light "
                  "point / VDP screen' SB1 schedule row.",
         assumption="Placement rule 4: SW on the latch jamb opposite the door swing. The main-door "
                    "swing arc itself is not drawn on this electrical-only sheet (only the ENTRY/EXIT "
                    "arrow + SB1 dot are shown), so the jamb side is a candidate, not a confirmed "
                    "hinge/latch reading — flagged for site verification."),

    # ---------------- Living & Dining Room ----------------
    dict(id="LD-SW-1", room="Living & Dining Room", product="SW", mount="on wall, beside sofa seating",
         anchor=(699.0, 351.0), badge=(722.0, 320.0), leader=True,
         evidence="Furniture labels 'sofa' (696.9,345.8) and 'center table' (646.6,340.8-371.4) mark "
                  "the L-seating group; SB6 Living&Dining schedule row lists 'ceiling light point - "
                  "5nos / 2 way fan point / diwali light point / chajja light point / AC point / "
                  "curtain light point'.",
         assumption="Rule 2: SW/SO above sofa side seating. No dedicated 'side table' word label was "
                    "found beside the Living Dining sofa on this sheet (unlike the three bedrooms), so "
                    "the badge is set at the sofa arm rather than tied to a printed side-table tag — "
                    "flagged as a furniture-only read."),
    dict(id="LD-SO-1", room="Living & Dining Room", product="SO", mount="on wall, beside sofa seating",
         anchor=(699.0, 351.0), badge=(722.0, 334.0), leader=False,
         evidence="Same evidence as LD-SW-1.",
         assumption="Paired with LD-SW-1 at one control station per rule 2."),
    dict(id="LD-10-1", room="Living & Dining Room", product="10\"", mount="wall screen, TV/mandir wall",
         anchor=(580.0, 152.0), badge=(605.0, 172.0), leader=True,
         evidence="In-plan 'tv unit' labels at (548.4,144.6) and (617.6,147.3) on the passage-facing "
                  "wall that opens onto Living & Dining; room has direct sightline to the Entrance "
                  "Foyer / VDP per rule 2b.",
         assumption="10\" chosen over 4\" because Living & Dining is the primary living zone with "
                    "entry sightline (rule 2). Exact screen height/orientation on the tv-unit wall is "
                    "not dimensioned on this electrical sheet."),
    dict(id="LD-GW-1", room="Living & Dining Room", product="GW", mount="surface, near TV/mandir wall",
         anchor=(588.0, 158.0), badge=(560.0, 172.0), leader=True,
         evidence="Same 'tv unit' plan labels as LD-10-1, plus SB2/SB3 Living&Dining schedule rows "
                  "'5/15 amp socket - 2 nos for tv and HDMI cable' / 'switch for tv on/off'.",
         assumption="AV serve wall inferred from tv-unit symbol + TV/HDMI schedule text; no dedicated "
                    "AV-rack furniture symbol is drawn."),
    dict(id="LD-IR-1", room="Living & Dining Room", product="IR", mount="separate blaster, near TV wall",
         anchor=(588.0, 158.0), badge=(560.0, 188.0), leader=False,
         evidence="Same evidence as LD-GW-1.",
         assumption="Family-B keeps GW and IR as separate badges (not combined CG+IR) per the sheet's "
                    "simplified-family convention noted in LEARNINGS.md."),
    dict(id="LD-CM-1", room="Living & Dining Room", product="CM",
         mount="candidate drive end, balcony slider (right wall return)",
         anchor=(705.0, 468.0), badge=(695.0, 443.0), leader=True,
         evidence="SB6 Living&Dining schedule row 'curtain light point' (word cluster 'curtain light "
                  "point' at 765.9-808.8,563.7); BALCONY 10'6\"x2'0\" opening at (632.6-657.7,"
                  "471.4-476.5) with full-width glazed threshold visible in marking/strip_living_dining.png.",
         assumption="ONE candidate motor placed at the right wall return (fixed partition adjoining "
                    "Parent's Bathroom) per Codex rule: one CM per evidenced track at a candidate drive "
                    "end, not both ends. This is an electrical-only base with no RCP/curtain schedule, "
                    "so exact stacking side, opening direction and true track count (single vs "
                    "dual-track) are NOT shown and must be confirmed on site or against a curtain "
                    "layout before execution."),

    # ---------------- Master Bedroom ----------------
    dict(id="MB-4-1", room="Master Bedroom", product="4\"", mount="bedside screen, first side from entry",
         anchor=(230.0, 420.0), badge=(255.0, 400.0), leader=True,
         evidence="Bed label at (287.8,445.6)-(298.1,450.8); room entry inferred from the SB4/SB4A/"
                  "SB4B/SB4C switch cluster on the west wall at (184-208,398-460), adjacent to the "
                  "wardrobe/passage side.",
         assumption="Rule 1: first bedside reached from room entry gets 4\"+SW/SO. The exact door-leaf "
                    "swing into Master Bedroom is not drawn on this electrical sheet, so 'first side' is "
                    "inferred from the SB4-series wall cluster proximity to the passage — flagged for "
                    "confirmation against the furniture/architectural plan."),
    dict(id="MB-SW-1", room="Master Bedroom", product="SW", mount="bedside, first side from entry",
         anchor=(230.0, 420.0), badge=(255.0, 416.0), leader=False,
         evidence="Same as MB-4-1.", assumption="Paired with MB-4-1 per rule 1."),
    dict(id="MB-SO-1", room="Master Bedroom", product="SO", mount="bedside, first side from entry",
         anchor=(230.0, 420.0), badge=(255.0, 432.0), leader=False,
         evidence="Same as MB-4-1.", assumption="Paired with MB-4-1 per rule 1."),
    dict(id="MB-SW-2", room="Master Bedroom", product="SW", mount="bedside, other side",
         anchor=(332.0, 382.0), badge=(318.0, 366.0), leader=True,
         evidence="'side'+'table' word pair at (323.4,385.5)-(334.6,396.7) plus in-plan SB2/SB2A tags "
                  "at (329.9-340.7,374.2-388.5) on the east wall of Master Bedroom.",
         assumption="Rule 1: other (non-entry) bedside gets SW/SO only, no screen — matches the "
                    "existing printed side-table + SB2/SB2A control station."),
    dict(id="MB-SO-2", room="Master Bedroom", product="SO", mount="bedside, other side",
         anchor=(332.0, 382.0), badge=(318.0, 380.0), leader=False,
         evidence="Same as MB-SW-2.", assumption="Paired with MB-SW-2 per rule 1."),
    dict(id="MB-CM-1", room="Master Bedroom", product="CM",
         mount="candidate drive end, north wall (left/wardrobe-corner return)",
         anchor=(215.0, 345.0), badge=(206.0, 360.0), leader=True,
         evidence="SB3 Master Bedroom schedule row 'AC point / curtain light point / chajja light "
                  "point / diwali light point / hanging light point'; word cluster 'curtain light "
                  "point' at (90.2-133.1,613.8-625.1) in the Master Bedroom SB legend table; north wall "
                  "of the room (behind the '8\\'1\\\" wardrobe' run at y≈65-95 crop-px, i.e. pdf "
                  "y≈355-360) is the room's principal window wall in the plan.",
         assumption="This electrical sheet does not draw a window/curtain-track symbol (only a "
                    "'wardrobe' furniture callout sits against this wall), so the exact glazing width "
                    "and stacking side are inferred, not confirmed. CM placed at the left (dressing-"
                    "mirror-corner) wall return as the more clearly square corner versus the rounded "
                    "corner on the opposite end — flagged as a review item."),
    dict(id="MB-GW-1", room="Master Bedroom", product="GW", mount="surface, TV wall",
         anchor=(197.0, 445.0), badge=(224.0, 430.0), leader=True,
         evidence="In-plan 'tv unit' label at (196.9,438.5)-(201.9,453.4) on the west wall; SB4 "
                  "schedule row '5/15 amp socket - 2 nos for tv and HDMI cable'.",
         assumption="AV serve wall confirmed by an explicit in-plan TV-unit symbol (stronger evidence "
                    "than the bedrooms without a drawn console)."),
    dict(id="MB-IR-1", room="Master Bedroom", product="IR", mount="separate blaster, TV wall",
         anchor=(197.0, 445.0), badge=(224.0, 454.0), leader=False,
         evidence="Same as MB-GW-1.", assumption="Separate IR badge per family-B convention."),

    # ---------------- Att. Bathroom (= 'Master Bathroom' SB schedule) ----------------
    dict(id="AB-SW-1", room="Att. Bathroom (Master)", product="SW", mount="wall bracket, dry/basin wall",
         anchor=(274.0, 220.0), badge=(268.0, 198.0), leader=True,
         evidence="In-plan SB1 tag at (271.8,215.2)-(277.7,224.8); Master Bathroom SB1 schedule row "
                  "'3 ceiling light point / 1 geyser point / 1 exhaust fan point / 1 pressure pump "
                  "point / mirror light point / 5/15 amp switch socket / 1 light will be on sensor'.",
         assumption="Rule 3: cyan pair placed on the dry basin wall (east side, at the printed SB1 "
                    "tag) opposite the 'geyser'/'exhaust' text cluster on the west wall (183-202,"
                    "192-242), read as the wet/shower side."),
    dict(id="AB-SO-1", room="Att. Bathroom (Master)", product="SO", mount="wall bracket, dry/basin wall",
         anchor=(274.0, 220.0), badge=(268.0, 214.0), leader=False,
         evidence="Same as AB-SW-1.", assumption="Paired with AB-SW-1 per rule 3."),

    # ---------------- Guest Bedroom (plan label 'Home Office') ----------------
    dict(id="GB-4-1", room="Guest Bedroom (plan label 'Home Office')", product="4\"",
         mount="bedside screen, sofa-cum-bed head end",
         anchor=(495.0, 375.0), badge=(494.0, 375.0), leader=False,
         evidence="'sofa cum bed' rotated label at (492.7,393.2)-(497.7,427.7); SB4/SB4A schedule row "
                  "'2 ceiling light points' on the north wall at (537.9-551.9,348.8-359.8).",
         assumption="Sofa-cum-bed has one clear accessible long edge (unlike a free-standing bed with "
                    "two sides), so a single bedside 4\"+SW/SO station is placed at the head end rather "
                    "than doubling per side."),
    dict(id="GB-SW-1", room="Guest Bedroom (plan label 'Home Office')", product="SW",
         mount="bedside, sofa-cum-bed head end", anchor=(495.0, 375.0), badge=(494.0, 391.0),
         leader=False, evidence="Same as GB-4-1.", assumption="Paired with GB-4-1."),
    dict(id="GB-SO-1", room="Guest Bedroom (plan label 'Home Office')", product="SO",
         mount="bedside, sofa-cum-bed head end", anchor=(495.0, 375.0), badge=(494.0, 407.0),
         leader=False, evidence="Same as GB-4-1.", assumption="Paired with GB-4-1."),
    dict(id="GB-SW-2", room="Guest Bedroom (plan label 'Home Office')", product="SW",
         mount="secondary control, work-desk wall",
         anchor=(452.0, 494.0), badge=(452.0, 514.0), leader=True,
         evidence="'work desk' label at (440.4-464.7,492.1-497.2); in-plan SB5/SB5A tags at "
                  "(535.2-549.2,460.2-471.0) and duplicate SB5/SB5A reference near the desk area.",
         assumption="Rule from SKILL.md: SW mapped to a confirmed switchboard/control point near "
                    "matched furniture (work desk) rather than invented; treated as a secondary control "
                    "station, not a second bedside."),
    dict(id="GB-SO-2", room="Guest Bedroom (plan label 'Home Office')", product="SO",
         mount="secondary control, work-desk wall", anchor=(452.0, 494.0), badge=(452.0, 530.0),
         leader=False, evidence="Same as GB-SW-2.", assumption="Paired with GB-SW-2."),
    dict(id="GB-CM-1", room="Guest Bedroom (plan label 'Home Office')", product="CM",
         mount="candidate drive end, own balcony slider (right wall return)",
         anchor=(552.0, 490.0), badge=(500.0, 458.0), leader=True,
         evidence="Word cluster 'curtain light point' at (400.0-442.9,672.7-684.1) in the Guest "
                  "Bedroom SB legend table; BALCONY 10'0\"x2'0\" opening at (479.8-505.0,519.7-531.1) "
                  "adjoining the room's south wall.",
         assumption="Same standing rule as LD-CM-1: one CM at a candidate drive end (right return, "
                    "adjacent to the Parent's-Bathroom-side partition), track count / stacking side not "
                    "shown on this electrical-only sheet — flagged for confirmation."),
    dict(id="GB-GW-1", room="Guest Bedroom (plan label 'Home Office')", product="GW",
         mount="surface, north wall (near SB4/SB4A)",
         anchor=(544.0, 356.0), badge=(568.0, 330.0), leader=True,
         evidence="SB4/SB4A tags at (537.9-551.9,348.8-359.8); Guest Bedroom SB schedule text "
                  "referencing a TV/HDMI 5/15 amp socket point for this room.",
         assumption="No TV-console furniture symbol is drawn for this room on the electrical sheet "
                    "(unlike Master Bedroom); AV wall is inferred from the SB4/SB4A cluster nearest the "
                    "schedule's TV/HDMI line — flagged as a lower-confidence read than MB-GW-1."),
    dict(id="GB-IR-1", room="Guest Bedroom (plan label 'Home Office')", product="IR",
         mount="separate blaster, north wall", anchor=(544.0, 356.0), badge=(568.0, 346.0),
         leader=False, evidence="Same as GB-GW-1.", assumption="Separate IR badge per family-B."),

    # ---------------- Guest Bathroom ----------------
    dict(id="GT-SW-1", room="Guest Bathroom", product="SW", mount="wall bracket, candidate location",
         anchor=(572.0, 410.0), badge=(590.0, 400.0), leader=True,
         evidence="Guest Bathroom SB1 schedule row '2 ceiling light point / 1 geyser point / 1 "
                  "exhaust fan point / 1 pressure pump point / mirror light point / 5/15 amp switch "
                  "socket / 1 light will be on sensor'; small basin-shaped plan symbol with adjacent "
                  "SB6/SB6A/SB7 tags at (566.2-577.7,396.1-434.4) on the wall shared by Guest Bedroom "
                  "and Living & Dining.",
         assumption="Guest Bathroom's own room outline is NOT clearly delineated on this electrical-"
                    "only sheet — this nook is the best-evidenced fixture+switchboard cluster matching "
                    "the schedule's Guest Bathroom row, but the exact room boundary should be confirmed "
                    "against the architectural/furniture drawing before execution."),
    dict(id="GT-SO-1", room="Guest Bathroom", product="SO", mount="wall bracket, candidate location",
         anchor=(572.0, 410.0), badge=(590.0, 416.0), leader=False,
         evidence="Same as GT-SW-1.", assumption="Paired with GT-SW-1; same room-boundary caveat."),

    # ---------------- Parent's Bedroom ----------------
    dict(id="PB-4-1", room="Parent's Bedroom", product="4\"", mount="bedside screen, first side from entry",
         anchor=(909.0, 268.0), badge=(940.0, 250.0), leader=True,
         evidence="'side'+'table' pair at (909.2,257.4)-(914.3,281.6); bed label at (889.4,334.1)-"
                  "(899.8,339.4); this side table sits nearer the room's top (corridor/entry) end.",
         assumption="Rule 1: first bedside reached from entry gets 4\"+SW/SO — entry side inferred "
                    "from proximity to the top corridor rather than a drawn door-swing arc (none is "
                    "printed on this electrical sheet for the bedroom's own door)."),
    dict(id="PB-SW-1", room="Parent's Bedroom", product="SW", mount="bedside, first side from entry",
         anchor=(909.0, 268.0), badge=(940.0, 266.0), leader=False,
         evidence="Same as PB-4-1.", assumption="Paired with PB-4-1."),
    dict(id="PB-SO-1", room="Parent's Bedroom", product="SO", mount="bedside, first side from entry",
         anchor=(909.0, 268.0), badge=(940.0, 282.0), leader=False,
         evidence="Same as PB-4-1.", assumption="Paired with PB-4-1."),
    dict(id="PB-SW-2", room="Parent's Bedroom", product="SW", mount="bedside, other side",
         anchor=(913.0, 415.0), badge=(940.0, 400.0), leader=True,
         evidence="'side'+'table' pair at (911.8,404.5)-(916.9,428.7), near the balcony-door 'swing' "
                  "callout at (823.1,418.7).",
         assumption="Rule 1: other bedside gets SW/SO only."),
    dict(id="PB-SO-2", room="Parent's Bedroom", product="SO", mount="bedside, other side",
         anchor=(913.0, 415.0), badge=(940.0, 416.0), leader=False,
         evidence="Same as PB-SW-2.", assumption="Paired with PB-SW-2."),
    dict(id="PB-CM-1", room="Parent's Bedroom", product="CM",
         mount="candidate drive end, balcony slider (left wall return)",
         anchor=(858.0, 468.0), badge=(846.0, 452.0), leader=True,
         evidence="Word cluster 'curtain light point' at (891.6-934.5,611.3-622.6) in the Parent's "
                  "Bedroom SB legend table; BALCONY 10'0\"x2'0\" opening at (853.4-878.5,471.7-482.9).",
         assumption="Left return chosen (straight partition shared with Parent's Bathroom) over the "
                    "right end, which the sheet marks '5\" TO 6\" CURVE' (a rounded corner, a weaker "
                    "drive-end candidate). Track count / stacking side not shown — flag for site "
                    "confirmation."),
    dict(id="PB-GW-1", room="Parent's Bedroom", product="GW", mount="surface, near SB4/SB4A wall",
         anchor=(932.0, 379.0), badge=(950.0, 362.0), leader=True,
         evidence="In-plan SB4/SB4A tags at (925.4-939.4,373.6-385.3); Parent's Bedroom SB5 schedule "
                  "row '5/15 amp socket - 2 nos for tv and HDMI cable extra'.",
         assumption="No TV-console furniture symbol drawn for this room; AV wall inferred from the "
                    "SB4/SB4A wall cluster nearest the TV/HDMI schedule line, same caveat as GB-GW-1."),
    dict(id="PB-IR-1", room="Parent's Bedroom", product="IR", mount="separate blaster, near SB4/SB4A wall",
         anchor=(932.0, 379.0), badge=(950.0, 380.0), leader=False,
         evidence="Same as PB-GW-1.", assumption="Separate IR badge per family-B."),

    # ---------------- Parent's Bathroom ----------------
    dict(id="PT-SW-1", room="Parent's Bathroom", product="SW", mount="wall bracket, dry wall",
         anchor=(809.0, 407.0), badge=(796.0, 390.0), leader=True,
         evidence="In-plan SB5A tag at (802.3,404.1)-(816.3,410.0); Parent's Bathroom SB1 schedule row "
                  "'2 way ceiling light point / 1 geyser point / 1 exhaust fan point / 1 pressure pump "
                  "point / mirror light point / 5/15 amp switch socket / 1 fan point / 1 light will be "
                  "on sensor'.",
         assumption="Only one wall-mounted SB tag (SB5A) is printed inside this small room; taken as "
                    "the dry wall by elimination since it sits at the room's entry side."),
    dict(id="PT-SO-1", room="Parent's Bathroom", product="SO", mount="wall bracket, dry wall",
         anchor=(809.0, 407.0), badge=(796.0, 406.0), leader=False,
         evidence="Same as PT-SW-1.", assumption="Paired with PT-SW-1."),

    # ---------------- Powder Bathroom ----------------
    dict(id="PW-SW-1", room="Powder Bathroom", product="SW", mount="wall bracket, entry/dry wall",
         anchor=(365.0, 319.0), badge=(365.0, 300.0), leader=True,
         evidence="Two in-plan SB1 tags at (338.3,316.2) and (391.0,316.2) on the room's top (passage-"
                  "facing) wall; Powder Bathroom schedule text is not separately itemised on this sheet "
                  "beyond the SB1 dots, consistent with a compact powder room.",
         assumption="Cyan pair centered between the two printed SB1 dots on the passage-facing wall, "
                    "read as the dry/entry wall for this small room."),
    dict(id="PW-SO-1", room="Powder Bathroom", product="SO", mount="wall bracket, entry/dry wall",
         anchor=(365.0, 319.0), badge=(365.0, 314.0), leader=False,
         evidence="Same as PW-SW-1.", assumption="Paired with PW-SW-1."),
]

LEGEND_CLASS_ORDER = ["SW", "SO", "4\"", "10\"", "CM", "GW", "IR", "DB"]
LEGEND_CLASS_LABEL = {
    "SW": "SW — switch (magenta = on wall, cyan = wall bracket)",
    "SO": "SO — socket (magenta = on wall, cyan = wall bracket)",
    "4\"": "4\" — bedside/secondary touch screen",
    "10\"": "10\" — living/central touch screen",
    "CM": "CM — curtain motor (candidate drive end)",
    "GW": "GW — surface gateway",
    "IR": "IR — IR blaster (separate from GW)",
    "DB": "DB — doorbell / VDP badge",
}


def fy(y):
    """fitz y (top-left origin, y-down) -> reportlab y (bottom-left origin, y-up)."""
    return PAGE_H - y


def draw_leader(c, x0, y0, x1, y1, color):
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.setDash(1, 2)
    c.line(x0, fy(y0), x1, fy(y1))
    c.setDash()


def draw_sw(c, x, y, color, label):
    r = 6.0
    c.setFillColor(white)
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    c.rect(x - r, fy(y) - r, 2 * r, 2 * r, fill=1, stroke=1)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(x, fy(y) - 2.0, label)


def draw_screen(c, x, y, size_label):
    r = 6.5
    c.setFillColor(white)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(1.2)
    c.roundRect(x - r, fy(y) - r, 2 * r, 2 * r, 1.5, fill=1, stroke=1)
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 5.0)
    c.drawCentredString(x, fy(y) - 2.0, size_label)


def draw_cm(c, x, y):
    r = 6.0
    c.setFillColor(white)
    c.setStrokeColor(PURPLE)
    c.setLineWidth(1.2)
    c.circle(x, fy(y), r, fill=1, stroke=1)
    c.setFillColor(PURPLE)
    c.setFont("Helvetica-Bold", 5.0)
    c.drawCentredString(x, fy(y) - 2.0, "CM")


def draw_gw(c, x, y):
    r = 5.5
    c.setFillColor(YELLOW)
    c.setStrokeColor(HexColor("#8a6d00"))
    c.setLineWidth(1.0)
    c.rect(x - r, fy(y) - r, 2 * r, 2 * r, fill=1, stroke=1)
    c.setFillColor(HexColor("#5a4600"))
    c.setFont("Helvetica-Bold", 4.6)
    c.drawCentredString(x, fy(y) - 2.0, "GW")


def draw_ir(c, x, y):
    r = 5.0
    c.setFillColor(IR_BLACK)
    c.setStrokeColor(IR_BLACK)
    c.circle(x, fy(y), r, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 4.6)
    c.drawCentredString(x, fy(y) - 1.8, "IR")


def draw_db(c, x, y):
    rw, rh = 7.0, 4.6
    c.setFillColor(DB_BLACK)
    c.setStrokeColor(DB_BLACK)
    c.ellipse(x - rw, fy(y) - rh, x + rw, fy(y) + rh, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 4.6)
    c.drawCentredString(x, fy(y) - 1.6, "DB")


def draw_placement(c, p):
    product = p["product"]
    x, y = p["badge"]
    ax, ay = p["anchor"]
    is_toilet = "Bathroom" in p["room"]
    if p.get("leader"):
        color = {
            "SW": CYAN if is_toilet else MAGENTA,
            "SO": CYAN if is_toilet else MAGENTA,
            "4\"": ORANGE, "10\"": ORANGE, "CM": PURPLE, "GW": HexColor("#8a6d00"),
            "IR": IR_BLACK, "DB": DB_BLACK,
        }[product]
        draw_leader(c, x, y, ax, ay, color)

    if product == "SW":
        draw_sw(c, x, y, CYAN if is_toilet else MAGENTA, "SW")
    elif product == "SO":
        draw_sw(c, x, y, CYAN if is_toilet else MAGENTA, "SO")
    elif product in ("4\"", "10\""):
        draw_screen(c, x, y, product)
    elif product == "CM":
        draw_cm(c, x, y)
    elif product == "GW":
        draw_gw(c, x, y)
    elif product == "IR":
        draw_ir(c, x, y)
    elif product == "DB":
        draw_db(c, x, y)
    else:
        raise ValueError(f"unknown product {product}")


def draw_stamp_and_legend(c, totals):
    # Stamp banner across the blank top margin (page content occupies
    # x:20-825,y:90-842 roughly; y:0-90 across x:20-825 is blank on the base
    # per marking/top_strip.png).
    band_x0, band_y0, band_x1, band_y1 = 24, 8, 560, 58
    c.setStrokeColor(STAMP_RED)
    c.setLineWidth(1.6)
    c.rect(band_x0, band_y0, band_x1 - band_x0, band_y1 - band_y0, fill=0, stroke=1)
    c.setFillColor(STAMP_RED)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(band_x0 + 10, band_y0 + 30, "PROPOSED  /  FOR REVIEW  /  NOT FOR EXECUTION")
    c.setFont("Helvetica", 8)
    c.drawString(band_x0 + 10, band_y0 + 14,
                 "viwaves automation overlay — base-only discussion drawing — Cursor cloud marking "
                 "check 2026-09-24")

    # Compact legend, top margin, to the right of the stamp band.
    lx0, ly0 = 576, 8
    lw, lh = 240, 78
    c.setStrokeColor(black)
    c.setLineWidth(0.7)
    c.rect(lx0, ly0, lw, lh, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(lx0 + 6, ly0 + lh - 10, "OVERLAY LEGEND (viwaves simplified family)")
    c.setFont("Helvetica", 6)
    y_cursor = ly0 + lh - 22
    for cls in LEGEND_CLASS_ORDER:
        c.drawString(lx0 + 6, y_cursor, f"{LEGEND_CLASS_LABEL[cls]}  (qty {totals.get(cls, 0)})")
        y_cursor -= 8
    c.drawString(lx0 + 6, y_cursor, "Cameras: 0 (not scoped on this base)")

    # Totals strip, remaining blank top-right area before GENERAL NOTES box.
    tx0, ty0 = 826, 0  # not usable: title/notes column starts here on the base;
    # keep totals table inside the plan-side blank band instead.
    tx0, ty0 = 24, 62
    c.setFont("Helvetica-Bold", 7)
    order = ["SW", "SO", "4\"", "10\"", "CM", "GW", "IR", "DB", "cameras"]
    line = "  ".join(f"{k}:{totals.get(k, 0)}" for k in order)
    c.drawString(tx0, ty0, "PRODUCT TOTALS (this proposal) — " + line)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    sha_before = sha256_of(BASE_PDF)

    totals = {}
    for p in PLACEMENTS:
        totals[p["product"]] = totals.get(p["product"], 0) + 1
    totals["cameras"] = 0

    # --- overlay ---
    c = canvas.Canvas(OVERLAY_PDF, pagesize=(PAGE_W, PAGE_H))
    for p in PLACEMENTS:
        draw_placement(c, p)
    draw_stamp_and_legend(c, totals)
    c.showPage()
    c.save()

    # --- merge onto ORIGINAL base page (vectors untouched) ---
    base_reader = PdfReader(BASE_PDF)
    overlay_reader = PdfReader(OVERLAY_PDF)
    writer = PdfWriter()
    base_page = base_reader.pages[0]
    base_page.merge_page(overlay_reader.pages[0])
    writer.add_page(base_page)
    with open(FINAL_PDF, "wb") as f:
        writer.write(f)

    sha_after_of_base = sha256_of(BASE_PDF)  # base file on disk must be untouched

    # --- placements.json ---
    records = []
    for p in PLACEMENTS:
        records.append({
            "id": p["id"],
            "room": p["room"],
            "product": p["product"],
            "qty": 1,
            "mounting": p["mount"],
            "coordinate_space": "pdf-points, top-left origin, y-down (fitz convention)",
            "anchor_xy": list(p["anchor"]),
            "badge_xy": list(p["badge"]),
            "leader_drawn": bool(p.get("leader")),
            "evidence": p["evidence"],
            "assumption": p["assumption"],
        })
    payload = {
        "project": "Gokul Divine, C/503, Irla S.V. Road, Vile Parle West, Mumbai 400056",
        "base_pdf": "layout/100826_GOKUL_DIVINE_ELECTRICAL_LAYOUT_v2.pdf",
        "base_pdf_sha256_before_merge": sha_before,
        "base_pdf_sha256_after_merge": sha_after_of_base,
        "base_unchanged": sha_before == sha_after_of_base,
        "evidence_class": "base-only (discussion electrical layout)",
        "issue_status": "PROPOSED / FOR REVIEW / NOT FOR EXECUTION",
        "page": {"width_pt": PAGE_W, "height_pt": PAGE_H, "orientation": "landscape (A3)"},
        "product_totals": totals,
        "placements": records,
    }
    with open(PLACEMENTS_JSON, "w") as f:
        json.dump(payload, f, indent=2)

    # --- qa-preview.png : full-sheet render of the merged PDF at ~150 dpi ---
    merged_doc = fitz.open(FINAL_PDF)
    page = merged_doc[0]
    mat = fitz.Matrix(150 / 72, 150 / 72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(os.path.join(OUT_DIR, "qa-preview.png"))
    merged_doc.close()

    os.remove(OVERLAY_PDF)

    print("Base SHA-256 before:", sha_before)
    print("Base SHA-256 after (base file, unmodified on disk):", sha_after_of_base)
    print("Totals:", totals)
    print("Wrote:", FINAL_PDF)
    print("Wrote:", PLACEMENTS_JSON)
    print("Wrote:", os.path.join(OUT_DIR, "qa-preview.png"))
    return totals, sha_before


if __name__ == "__main__":
    build()
