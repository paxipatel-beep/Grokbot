#!/usr/bin/env python3
"""
make_blank_marking.py — Grok/Cursor-cloud arm of the blank-marking bake-off (2026-09-23)

Overlays a PROPOSED viwaves automation marking onto the untouched vector base
BLANK_SYNTHETIC_1BHK.pdf. The original PDF page (walls, furniture outlines,
room labels, title block) is preserved exactly; automation symbols are drawn
on a separate vector overlay page and merged on top with pypdf.

Placement rules applied (see inputs/BRIEF.md):
  1. Bedside: first-side wall when entering -> 4" + SW/SO; other bedside -> SW/SO only
  2. Living: SW/SO above sofa side tables; 10" because living sees entry (open plan)
  3. Toilet: SW/SO parallel on the dry basin wall
  4. Entry: SW on latch wall opposite door swing; DB at entry
  5. CM only at curtain-track ends
  6. GW+IR near TV; no cameras anywhere
  7. viwaves simplified family: pink on-wall SW/SO, cyan bracket SW/SO,
     orange 4", peach 10", purple CM, yellow surface GW, black IR, black DB

All source geometry (walls, furniture, curtain tracks, basins, door swing)
was read directly from the base PDF's vector paths/text with PyMuPDF so every
badge coordinate below is anchored to a real drawn element -- see qa-notes.md
for the room-by-room evidence trail and every assumption that still needs
site/drawing confirmation.
"""
import json
import os
from collections import Counter, defaultdict

import fitz  # PyMuPDF - only used to read source geometry + render a QA preview
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas as rl_canvas

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PDF = os.path.join(HERE, "inputs", "BLANK_SYNTHETIC_1BHK.pdf")
OUT_DIR = os.path.join(HERE, "output")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- viwaves family
C_ORANGE = HexColor("#e6642a")   # 4"
C_PEACH = HexColor("#f0a06e")    # 10"
C_PURPLE = HexColor("#8c3ca0")   # CM
C_CYAN = HexColor("#6eb4dc")     # bracket SW/SO
C_PINK = HexColor("#dc508c")     # on-wall SW/SO
C_YELLOW = HexColor("#f0d232")   # surface GW
C_BLACK = HexColor("#141414")    # IR + DB
C_WHITE = white
C_RED = HexColor("#c82828")      # PROPOSED stamp

FONT = "Helvetica-Bold"

MARKS = []          # flat log for placements.json
LEADERS = []        # thin dashed leader lines (badge -> real feature) for QA traceability


def add(kind, family, room, x, y, w, h, note="", target=None):
    """Log one placed symbol. x,y,w,h are top-down (PyMuPDF-style) page points."""
    MARKS.append(
        {
            "kind": kind,
            "family": family,
            "room": room,
            "note": note,
            "bbox_topdown_pt": [round(x, 1), round(y, 1), round(x + w, 1), round(y + h, 1)],
            "center_topdown_pt": [round(x + w / 2, 1), round(y + h / 2, 1)],
        }
    )
    if target:
        LEADERS.append(((x + w / 2, y + h / 2), target))


# ---------------------------------------------------------------- drawing helpers
# All helpers take TOP-DOWN coordinates (matching the PyMuPDF geometry pulled
# from the base PDF) and flip to reportlab's bottom-up canvas space internally.
def topdown_to_rl(x, y_top, h, page_h):
    return x, page_h - y_top - h


def rounded_badge(c, page_h, x, y_top, w, h, text, fill, text_color=C_WHITE, font_size=8):
    rx, ry = topdown_to_rl(x, y_top, h, page_h)
    c.setFillColor(fill)
    c.setStrokeColor(HexColor("#000000"))
    c.setLineWidth(0.6)
    c.roundRect(rx, ry, w, h, radius=3, fill=1, stroke=1)
    c.setFillColor(text_color)
    c.setFont(FONT, font_size)
    c.drawCentredString(rx + w / 2, ry + h / 2 - font_size * 0.35, text)


def badge_sw(c, page_h, x, y_top, family="wall", w=22, h=16):
    fill = C_PINK if family == "wall" else C_CYAN
    tc = C_WHITE if family == "wall" else HexColor("#0a0a0a")
    rounded_badge(c, page_h, x, y_top, w, h, "SW", fill, tc, font_size=7.5)


def badge_so(c, page_h, x, y_top, family="wall", w=22, h=16):
    fill = C_PINK if family == "wall" else C_CYAN
    tc = C_WHITE if family == "wall" else HexColor("#0a0a0a")
    rounded_badge(c, page_h, x, y_top, w, h, "SO", fill, tc, font_size=7.5)


def badge_4(c, page_h, x, y_top, w=28, h=18):
    rounded_badge(c, page_h, x, y_top, w, h, '4"', C_ORANGE, C_WHITE, font_size=8)


def badge_10(c, page_h, x, y_top, w=34, h=20):
    rounded_badge(c, page_h, x, y_top, w, h, '10"', C_PEACH, HexColor("#3a2410"), font_size=9)


def badge_cm(c, page_h, x, y_top, w=28, h=16):
    rounded_badge(c, page_h, x, y_top, w, h, "CM", C_PURPLE, C_WHITE, font_size=7.5)


def badge_gw(c, page_h, x, y_top, w=34, h=22):
    rounded_badge(c, page_h, x, y_top, w, h, "GW", C_YELLOW, HexColor("#0a0a0a"), font_size=8)


def badge_ir(c, page_h, x_center, y_top_center, r=10):
    rx, ry = topdown_to_rl(x_center, y_top_center, 0, page_h)
    c.setFillColor(C_BLACK)
    c.setStrokeColor(HexColor("#000000"))
    c.circle(rx, ry, r, fill=1, stroke=1)
    c.setFillColor(C_WHITE)
    c.setFont(FONT, 6)
    c.drawCentredString(rx, ry - 2, "IR")


def badge_db(c, page_h, x, y_top, w=14, h=24):
    rx, ry = topdown_to_rl(x, y_top, h, page_h)
    c.setFillColor(C_BLACK)
    c.roundRect(rx, ry, w, h, radius=4, fill=1, stroke=1)
    c.setFillColor(C_WHITE)
    c.circle(rx + w / 2, ry + h * 0.62, w * 0.28, fill=1, stroke=0)
    c.setFillColor(C_WHITE)
    c.rect(rx + w * 0.28, ry + h * 0.18, w * 0.44, h * 0.2, fill=1, stroke=0)


def draw_leader(c, page_h, p_from_topdown, p_to_topdown):
    (x1, y1), (x2, y2) = p_from_topdown, p_to_topdown
    rx1, ry1 = x1, page_h - y1
    rx2, ry2 = x2, page_h - y2
    c.saveState()
    c.setDash(2, 2)
    c.setLineWidth(0.5)
    c.setStrokeColor(HexColor("#666666"))
    c.line(rx1, ry1, rx2, ry2)
    c.restoreState()


# ---------------------------------------------------------------- read base geometry (sanity)
src = fitz.open(BASE_PDF)
page = src[0]
PAGE_W, PAGE_H = page.rect.width, page.rect.height
src.close()

# ================================================================ BUILD OVERLAY
overlay_path = os.path.join(OUT_DIR, "_overlay.pdf")
c = rl_canvas.Canvas(overlay_path, pagesize=(PAGE_W, PAGE_H))

# ---------- MASTER BEDROOM (100,141.9)-(380,391.9) ----------
ROOM = "Master Bedroom"
# curtain track (110,146.9)-(370,146.9) -> CM at both drawn ends
badge_cm(c, PAGE_H, 106, 158, w=28, h=16)
add("CM", "purple", ROOM, 106, 158, 28, 16, "curtain track - left end", target=(110, 146.9))
draw_leader(c, PAGE_H, (120, 166), (110, 146.9))
badge_cm(c, PAGE_H, 346, 158, w=28, h=16)
add("CM", "purple", ROOM, 346, 158, 28, 16, "curtain track - right end", target=(370, 146.9))
draw_leader(c, PAGE_H, (360, 166), (370, 146.9))

# first-side bedside = right table (271,266.9), nearest to shared wall with
# Living/Dining (assumed access side - see qa-notes) -> 4" + SW/SO on east wall
badge_4(c, PAGE_H, 340, 232, w=28, h=18)
add("4\"", "orange", ROOM, 340, 232, 28, 18, "first-side bedside (east/right table)", target=(271, 266.9))
badge_sw(c, PAGE_H, 336, 256, "wall")
add("SW", "wall", ROOM, 336, 256, 22, 16, "first-side bedside (east/right table)", target=(271, 266.9))
badge_so(c, PAGE_H, 336, 276, "wall")
add("SO", "wall", ROOM, 336, 276, 22, 16, "first-side bedside (east/right table)", target=(271, 266.9))
draw_leader(c, PAGE_H, (340, 264), (271, 266.9))

# other bedside = left table (129,266.9), west wall -> SW/SO only
# (table footprint is x120-138,y251.9-281.9; badges sit above/below it so the
# furniture symbol stays visible, per SKILL.md "do not cover ... furniture")
badge_sw(c, PAGE_H, 106, 220, "wall", w=20, h=16)
add("SW", "wall", ROOM, 106, 220, 20, 16, "other bedside (west/left table)", target=(129, 266.9))
badge_so(c, PAGE_H, 106, 285, "wall", w=20, h=16)
add("SO", "wall", ROOM, 106, 285, 20, 16, "other bedside (west/left table)", target=(129, 266.9))
draw_leader(c, PAGE_H, (116, 236), (129, 251.9))
draw_leader(c, PAGE_H, (116, 285), (129, 281.9))

# ---------- LIVING / DINING (400,141.9)-(720,391.9) ----------
ROOM = "Living / Dining"
# curtain track (410,146.9)-(710,146.9) -> CM at both drawn ends
badge_cm(c, PAGE_H, 406, 158, w=28, h=16)
add("CM", "purple", ROOM, 406, 158, 28, 16, "curtain track - left end", target=(410, 146.9))
draw_leader(c, PAGE_H, (420, 166), (410, 146.9))
badge_cm(c, PAGE_H, 676, 158, w=28, h=16)
add("CM", "purple", ROOM, 676, 158, 28, 16, "curtain track - right end", target=(710, 146.9))
draw_leader(c, PAGE_H, (690, 166), (710, 146.9))

# west side table (426,296.9) close to west wall -> pink SW/SO
badge_sw(c, PAGE_H, 404, 270, "wall")
add("SW", "wall", ROOM, 404, 270, 22, 16, "sofa side table - west", target=(426, 296.9))
badge_so(c, PAGE_H, 404, 290, "wall")
add("SO", "wall", ROOM, 404, 290, 22, 16, "sofa side table - west", target=(426, 296.9))
draw_leader(c, PAGE_H, (415, 298), (426, 296.9))

# east side table (614,296.9) projected onto east wall -> pink SW/SO
badge_sw(c, PAGE_H, 696, 270, "wall")
add("SW", "wall", ROOM, 696, 270, 22, 16, "sofa side table - east", target=(614, 296.9))
badge_so(c, PAGE_H, 696, 290, "wall")
add("SO", "wall", ROOM, 696, 290, 22, 16, "sofa side table - east", target=(614, 296.9))
draw_leader(c, PAGE_H, (707, 298), (614, 296.9))

# 10" on south wall - living/dining open plan sees Passage -> Foyer/Entry
badge_10(c, PAGE_H, 542, 368, w=34, h=20)
add("10\"", "peach", ROOM, 542, 368, 34, 20, "open-plan sightline to Passage/Foyer entry", target=(559, 391.9))
draw_leader(c, PAGE_H, (559, 388), (559, 391.9))

# GW + IR beside the only TV drawn on this base
badge_gw(c, PAGE_H, 566, 178, w=34, h=22)
add("GW", "yellow", ROOM, 566, 178, 34, 22, "surface gateway near TV", target=(560, 192.9))
badge_ir(c, PAGE_H, 615, 189, r=10)
add("IR", "black", ROOM, 605, 179, 20, 20, "IR blaster near TV", target=(560, 192.9))
draw_leader(c, PAGE_H, (566, 189), (560, 192.9))

# ---------- MASTER BATH (100,411.9)-(260,561.9) ----------
ROOM = "Master Bath"
# basin (120,471.9)-(140,491.9) against west wall -> SW/SO parallel on that wall, below basin
badge_sw(c, PAGE_H, 104, 505, "bracket")
add("SW", "bracket", ROOM, 104, 505, 22, 16, "parallel on dry basin (west) wall", target=(130, 481.9))
badge_so(c, PAGE_H, 104, 525, "bracket")
add("SO", "bracket", ROOM, 104, 525, 22, 16, "parallel on dry basin (west) wall", target=(130, 481.9))
draw_leader(c, PAGE_H, (115, 505), (130, 491.9))

# ---------- POWDER (280,411.9)-(380,561.9) ----------
ROOM = "Powder"
# basin (290,491.9)-(310,511.9) against shared west wall -> SW/SO above basin
badge_sw(c, PAGE_H, 284, 451, "bracket")
add("SW", "bracket", ROOM, 284, 451, 22, 16, "parallel on dry basin (west) wall", target=(300, 501.9))
badge_so(c, PAGE_H, 284, 471, "bracket")
add("SO", "bracket", ROOM, 284, 471, 22, 16, "parallel on dry basin (west) wall", target=(300, 501.9))
draw_leader(c, PAGE_H, (295, 487), (300, 491.9))

# ---------- GUEST BEDROOM (740,341.9)-(960,561.9) ----------
ROOM = "Guest Bedroom"
# first-side bedside = west table (768,447.9), nearest the Passage access side -> 4" + SW/SO
# (table footprint is x760-776,y433.9-461.9; badges sit above/below it so the
# furniture symbol stays visible, per SKILL.md "do not cover ... furniture")
badge_4(c, PAGE_H, 748, 400, w=28, h=18)
add("4\"", "orange", ROOM, 748, 400, 28, 18, "first-side bedside (west/left table)", target=(768, 447.9))
badge_sw(c, PAGE_H, 748, 466, "wall", w=28, h=16)
add("SW", "wall", ROOM, 748, 466, 28, 16, "first-side bedside (west/left table)", target=(768, 447.9))
badge_so(c, PAGE_H, 748, 486, "wall", w=28, h=16)
add("SO", "wall", ROOM, 748, 486, 28, 16, "first-side bedside (west/left table)", target=(768, 447.9))
draw_leader(c, PAGE_H, (762, 418), (768, 433.9))
draw_leader(c, PAGE_H, (762, 466), (768, 461.9))

# other bedside = east table (890,447.9) -> SW/SO only
badge_sw(c, PAGE_H, 930, 436, "wall")
add("SW", "wall", ROOM, 930, 436, 22, 16, "other bedside (east/right table)", target=(890, 447.9))
badge_so(c, PAGE_H, 930, 456, "wall")
add("SO", "wall", ROOM, 930, 456, 22, 16, "other bedside (east/right table)", target=(890, 447.9))
draw_leader(c, PAGE_H, (930, 446), (890, 447.9))

# ---------- GUEST BATH (740,581.9)-(860,741.9) ----------
ROOM = "Guest Bath"
# basin (760,651.9)-(780,671.9) against west wall -> SW/SO parallel, below basin
badge_sw(c, PAGE_H, 744, 685, "bracket")
add("SW", "bracket", ROOM, 744, 685, 22, 16, "parallel on dry basin (west) wall", target=(770, 661.9))
badge_so(c, PAGE_H, 744, 705, "bracket")
add("SO", "bracket", ROOM, 744, 705, 22, 16, "parallel on dry basin (west) wall", target=(770, 661.9))
draw_leader(c, PAGE_H, (755, 685), (770, 671.9))

# ---------- FOYER / ENTRY (400,581.9)-(600,741.9) ----------
ROOM = "Foyer / Entry"
# door leaf at x=480 (hinge at wall, 480,741.9), arrow -> shows swing sweeping
# EAST; latch wall (unswept side) is WEST of the hinge -> SW there
badge_sw(c, PAGE_H, 434, 712, "wall", w=22, h=16)
add("SW", "wall", ROOM, 434, 712, 22, 16, "latch wall, opposite door swing (swing sweeps east)", target=(480, 741.9))
draw_leader(c, PAGE_H, (445, 728), (480, 741.9))

# DB at entry, placed on the swing (east) side, set back from the swept arc
badge_db(c, PAGE_H, 552, 692, w=14, h=26)
add("DB", "black", ROOM, 552, 692, 14, 26, "doorbell at main entry", target=(480, 741.9))
draw_leader(c, PAGE_H, (559, 718), (520.7, 725.8))

# ---------------------------------------------------------------- STATUS STAMP
c.setFillColor(C_RED)
c.rect(30, PAGE_H - 34, 640, 26, fill=1, stroke=0)
c.setFillColor(white)
c.setFont(FONT, 12)
c.drawString(40, PAGE_H - 26, "PROPOSED  /  FOR REVIEW  /  NOT FOR EXECUTION")
c.setFont("Helvetica", 8)
c.drawString(40, PAGE_H - 33.5 + 1.5, "")

c.setFillColor(HexColor("#333333"))
c.setFont("Helvetica", 7.5)
c.drawString(30, PAGE_H - 44, "viwaves simplified family: pink SW/SO on-wall | cyan SW/SO bracket | orange 4\" | peach 10\" | purple CM | yellow surface GW | black IR | black DB  --  Cursor cloud (Grok arm) bake-off, blank base only, no client scope")

c.showPage()
c.save()

# ================================================================ MERGE OVERLAY ONTO ORIGINAL VECTOR PDF
reader_base = PdfReader(BASE_PDF)
reader_overlay = PdfReader(overlay_path)
writer = PdfWriter()

base_page = reader_base.pages[0]
base_page.merge_page(reader_overlay.pages[0])
writer.add_page(base_page)

final_pdf = os.path.join(OUT_DIR, "MARKING_PROPOSED.pdf")
with open(final_pdf, "wb") as fh:
    writer.write(fh)
os.remove(overlay_path)
print("wrote", final_pdf)

# ================================================================ QA PREVIEW PNG (Pillow) — legend + render
doc = fitz.open(final_pdf)
pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
preview_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
doc.close()

legend_h = 120
legend = Image.new("RGB", (preview_img.width, legend_h), (255, 255, 255))
ld = ImageDraw.Draw(legend)


def load_font(size):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


f = load_font(14)
fh = load_font(16)
ld.text((16, 8), "viwaves simplified automation family (legend)", font=fh, fill=(0, 0, 0))
legend_items = [
    ("SW / SO on-wall", (220, 80, 140)),
    ("SW / SO bracket", (110, 180, 220)),
    ('4"', (230, 100, 42)),
    ('10"', (240, 160, 110)),
    ("CM", (140, 60, 160)),
    ("GW (surface)", (240, 210, 50)),
    ("IR / DB", (20, 20, 20)),
]
x = 16
y = 40
for label, color in legend_items:
    ld.rectangle([x, y, x + 26, y + 20], fill=color, outline=(0, 0, 0))
    ld.text((x + 32, y + 2), label, font=f, fill=(0, 0, 0))
    x += 32 + 8 * len(label) + 40

with_legend = Image.new("RGB", (preview_img.width, preview_img.height + legend_h), (255, 255, 255))
with_legend.paste(preview_img, (0, 0))
with_legend.paste(legend, (0, preview_img.height))
with_legend.save(os.path.join(OUT_DIR, "qa-preview.png"))
print("wrote", os.path.join(OUT_DIR, "qa-preview.png"))

# ================================================================ placements.json
totals = Counter(m["kind"] for m in MARKS)
by_room = defaultdict(Counter)
for m in MARKS:
    by_room[m["room"]][m["kind"]] += 1

placements = {
    "meta": {
        "project": "blank-marking-2026-09-23",
        "arm": "cursor-cloud (grok models)",
        "base_pdf": "inputs/BLANK_SYNTHETIC_1BHK.pdf",
        "page_size_pt": [round(PAGE_W, 2), round(PAGE_H, 2)],
        "status": "PROPOSED / FOR REVIEW / NOT FOR EXECUTION",
        "evidence_class": "base-only (no client quote/scope)",
        "coordinate_system": "top-down page points, origin top-left, y increases downward (matches PyMuPDF page space)",
    },
    "totals": dict(sorted(totals.items())),
    "totals_by_room": {room: dict(cnt) for room, cnt in by_room.items()},
    "placements": MARKS,
}
with open(os.path.join(OUT_DIR, "placements.json"), "w") as fh:
    json.dump(placements, fh, indent=2)
print("wrote", os.path.join(OUT_DIR, "placements.json"))
print("TOTALS:", dict(sorted(totals.items())))
