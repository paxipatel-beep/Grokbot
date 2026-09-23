#!/usr/bin/env python3
"""Rev4 — Prakash placement rules: first-side bedside 4"+SW/SO, CM on curtains,
living SW/SO above sofa side tables, 10\" for doorbell view, toilet near basin walls,
entry SW on latch wall opposite door swing."""
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from collections import defaultdict, Counter
import os

BASE = "/workspace/new-layout/base72-1.png"
LEGEND_SRC = "/home/box/agent-data/agents/1c612e1d-5a06-4865-b940-5023a6338c17/attachments/bbc79de5f1f61c8543909bf3157ebfa842679918c076d241d23039e952797082.png"
OUT_DIR = "/workspace/new-layout/out"
os.makedirs(OUT_DIR, exist_ok=True)

C_ORANGE = (230, 100, 40, 230)
C_PEACH = (240, 160, 110, 230)
C_PURPLE = (140, 60, 160, 230)
C_BLUE = (110, 180, 220, 230)
C_PINK = (220, 80, 140, 230)
C_YELLOW = (240, 210, 50, 230)
C_BLACK = (20, 20, 20, 240)
C_WHITE = (255, 255, 255, 255)

def load_font(size):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def badge_rect(draw, xy, text, fill, text_fill=(255, 255, 255, 255), size=22):
    x, y = xy
    font = load_font(max(10, size - 8))
    pad = 3
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = max(tw + pad * 2, size), max(th + pad * 2, size - 2)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=fill, outline=(0, 0, 0, 200))
    draw.text((x + pad, y + pad - 1), text, font=font, fill=text_fill)

def badge_circle(draw, xy, text, fill, r=22, text_fill=(255, 255, 255, 255)):
    x, y = xy
    draw.ellipse([x, y, x + 2 * r, y + 2 * r], fill=fill, outline=(0, 0, 0, 200))
    font = load_font(8)
    lines = text.split()
    cy = y + r - 5 * len(lines)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + r - tw / 2, cy + i * 10), line, font=font, fill=text_fill)

def badge_sq_gateway(draw, xy, label="SURFACE\nGATEWAY"):
    x, y = xy
    w, h = 60, 42
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=C_YELLOW, outline=(0, 0, 0, 200))
    font = load_font(7)
    for i, line in enumerate(label.split("\n")):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (w - tw) / 2, y + 6 + i * 11), line, font=font, fill=(0, 0, 0, 255))
    draw.ellipse([x + w / 2 - 8, y + h - 10, x + w / 2 - 4, y + h - 6], fill=(0, 0, 0, 255))
    draw.ellipse([x + w / 2 + 4, y + h - 10, x + w / 2 + 8, y + h - 6], fill=(0, 0, 0, 255))

def badge_doorbell(draw, xy):
    x, y = xy
    draw.rounded_rectangle([x, y, x + 18, y + 36], radius=8, fill=C_BLACK, outline=(0, 0, 0, 255))
    draw.ellipse([x + 4, y + 8, x + 14, y + 18], fill=C_WHITE)
    draw.rectangle([x + 6, y + 22, x + 12, y + 28], fill=C_WHITE)

def sw_only(draw, xy):
    badge_rect(draw, xy, "SW", C_PINK, size=22)

def pair_wall(draw, xy):
    x, y = xy
    badge_rect(draw, (x, y), "SW", C_PINK, size=22)
    badge_rect(draw, (x + 26, y), "SO", C_PINK, size=22)

def pair_bracket(draw, xy):
    """Horizontal SW|SO (for walls that run left-right)."""
    x, y = xy
    badge_rect(draw, (x, y), "SW", C_BLUE, text_fill=(0, 0, 0, 255), size=22)
    badge_rect(draw, (x + 26, y), "SO", C_BLUE, text_fill=(0, 0, 0, 255), size=22)

def pair_bracket_v(draw, xy):
    """Vertical SW/SO stacked — parallel to a vertical wall."""
    x, y = xy
    badge_rect(draw, (x, y), "SW", C_BLUE, text_fill=(0, 0, 0, 255), size=22)
    badge_rect(draw, (x, y + 24), "SO", C_BLUE, text_fill=(0, 0, 0, 255), size=22)

def cm(draw, xy):
    badge_rect(draw, xy, "CM", C_PURPLE, size=24)

def cm_at(draw, cx, cy):
    """Place CM centered on curtain-track tip (cx,cy)."""
    # badge ~30x18 for size=24 "CM"
    w, h = 30, 18
    badge_rect(draw, (int(cx - w / 2), int(cy - h / 2)), "CM", C_PURPLE, size=24)

def screen4(draw, xy):
    badge_rect(draw, xy, '4"', C_ORANGE, size=24)

def screen10(draw, xy):
    badge_rect(draw, xy, '10"', C_PEACH, size=26)

def ir(draw, xy):
    badge_circle(draw, xy, "IR BLASTER", C_BLACK, r=22)

MARKS = []

def add(kind, room, note=""):
    MARKS.append({"kind": kind, "room": room, "note": note})

def bedside_first(draw, wall_xy, room_prefix):
    """4\" + SW + SO along wall at first side table when entering."""
    x, y = wall_xy
    screen4(draw, (x, y)); add("4\"", f"{room_prefix} first bedside")
    pair_wall(draw, (x, y + 28)); add("SW-W", f"{room_prefix} first bedside"); add("SO-W", f"{room_prefix} first bedside")

def bedside_other(draw, wall_xy, room_prefix):
    pair_wall(draw, wall_xy); add("SW-W", f"{room_prefix} other bedside"); add("SO-W", f"{room_prefix} other bedside")

base = Image.open(BASE).convert("RGBA")
bw, bh = base.size
LEGEND_H = 220
PAD = 16
canvas_im = Image.new("RGBA", (bw, bh + LEGEND_H + PAD * 2), (255, 255, 255, 255))
canvas_im.paste(base, (0, 0))
overlay = Image.new("RGBA", canvas_im.size, (0, 0, 0, 0))
d = ImageDraw.Draw(overlay)

# ========== MAIN ENTRY ==========
badge_doorbell(d, (2180, 1520)); add("DB", "Main Entry")
pair_wall(d, (2080, 1480)); add("SW-W", "Main Entry"); add("SO-W", "Main Entry")

# ========== LIVING — SW/SO on wall above sofa SIDE TABLES ==========
# Sofa against west wall; side tables ~ (1811,378) and (1811,690)
pair_wall(d, (1788, 360)); add("SW-W", "Living side table N"); add("SO-W", "Living side table N")
pair_wall(d, (1788, 675)); add("SW-W", "Living side table S"); add("SO-W", "Living side table S")
# 10\" on wall visible from living + dining + kitchen (open-plan junction near dining/bar facing into space)
screen10(d, (1620, 880)); add("10\"", "Living-dining-kitchen view (doorbell)")
# IR/GW near AC (TV / pop-up wall high)
badge_sq_gateway(d, (2140, 420)); add("Surface GW", "Living / near AC")
ir(d, (2210, 415)); add("IR", "Living / near AC")
# CM centered on living curtain-track tips (wavy line at y~331, not deck plants)
cm_at(d, 1780, 331); add("CM", "Living curtain L")
cm_at(d, 2195, 331); add("CM", "Living curtain R")
# Living entry SW — from foyer into living: place on latch wall (east of opening toward pop-up)
sw_only(d, (2050, 1380)); add("SW-W", "Living entry")

# ========== GUEST BEDROOM ==========
# Door ~3'-5" at south; swings into room toward right → entry SW on LEFT (opposite swing)
sw_only(d, (1435, 730)); add("SW-W", "Guest entry")
# First side when enter from south = south side table ~ (1811,690); 4\"+SW+SO on wall
bedside_first(d, (1785, 665), "Guest")
# Other head side tables on north wall
bedside_other(d, (1660, 355), "Guest")
bedside_other(d, (1790, 355), "Guest N2")
# IR/GW near AC high on TV wall
badge_sq_gateway(d, (1365, 300)); add("Surface GW", "Guest / near AC")
ir(d, (1430, 295)); add("IR", "Guest / near AC")
# CM centered on guest curtain wavy ends
cm_at(d, 1460, 228); add("CM", "Guest curtain L")
cm_at(d, 1705, 228); add("CM", "Guest curtain R")
# G. Toilet — basin on LEFT vertical wall; SW/SO vertical (parallel), on dry side of basin (toward WC, opposite shower)
pair_bracket_v(d, (1175, 348)); add("SW-B", "G. Toilet"); add("SO-B", "G. Toilet")

# ========== KID'S BEDROOM ==========
# Door ~2'-11" south; swings left into room → entry SW on RIGHT (opposite swing)
sw_only(d, (905, 735)); add("SW-W", "Kid's entry")
# First side when enter = south side table ~ (633,627)
bedside_first(d, (575, 600), "Kid's")
# Other (north) side table
bedside_other(d, (575, 385), "Kid's")
# IR/GW near AC
badge_sq_gateway(d, (880, 300)); add("Surface GW", "Kid's / near AC")
ir(d, (945, 295)); add("IR", "Kid's / near AC")
# CM centered on kid's curtain wavy ends
cm_at(d, 660, 243); add("CM", "Kid's curtain L")
cm_at(d, 968, 243); add("CM", "Kid's curtain R")
# K. Toilet — basin on RIGHT vertical wall; SW/SO vertical (parallel), LEFT of basin, opposite wet/shower (toward WC)
pair_bracket_v(d, (1068, 348)); add("SW-B", "K. Toilet"); add("SO-B", "K. Toilet")

# ========== MASTER BEDROOM ==========
# Sliding door south; entry SW on wall at opening end (east jamb / HIS side — opposite stack path)
sw_only(d, (500, 845)); add("SW-W", "Master entry")
# First side when enter from south = south side table ~ (225,758)
bedside_first(d, (175, 730), "Master")
# Other (north) side table
bedside_other(d, (175, 430), "Master")
# IR/GW near AC high on TV wall
badge_sq_gateway(d, (500, 470)); add("Surface GW", "Master / near AC")
ir(d, (565, 465)); add("IR", "Master / near AC")
# CM centered on master curtain wavy ends (not dimension line / glass line)
cm_at(d, 160, 265); add("CM", "Master curtain L")
cm_at(d, 535, 265); add("CM", "Master curtain R")
# Walk-in — SW only at sliding into walk-in (optional pair kept as bracket near dressing)
pair_bracket(d, (340, 980)); add("SW-B", "Master walk-in"); add("SO-B", "Master walk-in")
# M. Toilet — basin on south horizontal wall; SW/SO horizontal (parallel), RIGHT of basin (opposite shower/wet)
pair_bracket(d, (730, 1008)); add("SW-B", "M. Toilet"); add("SO-B", "M. Toilet")

# ========== KITCHEN / PW / PASSAGE ==========
sw_only(d, (1565, 1085)); add("SW-W", "Kitchen entry")
# Dining — no extra floating living SW; bar side optional SO omitted
# PW. Toilet — basin at SE corner; SW/SO vertical on right wall of basin (opposite WC/wet)
pair_bracket_v(d, (1330, 965)); add("SW-B", "PW. Toilet"); add("SO-B", "PW. Toilet")
sw_only(d, (1100, 700)); add("SW-W", "Passage")

out = Image.alpha_composite(canvas_im, overlay)

banner = ImageDraw.Draw(out)
bf = load_font(22)
banner.rectangle([40, 10, 1280, 72], fill=(200, 40, 40, 230))
banner.text((55, 18), "PROPOSED FULL AUTOMATION MARKING — FOR REVIEW", font=bf, fill=(255, 255, 255, 255))
sf = load_font(11)
banner.text((55, 48), "Rev4 · 4\"+SW/SO first bedside · CM on curtains · Living SW/SO above side tables · 10\" doorbell view · Entry SW opposite door swing", font=sf, fill=(255, 255, 255, 255))

# Legend in empty bottom margin
leg = Image.open(LEGEND_SRC).convert("RGBA").transpose(Image.Transpose.ROTATE_90)
max_w = bw - 40
scale = min(max_w / leg.width, LEGEND_H / leg.height)
nw, nh = int(leg.width * scale), int(leg.height * scale)
leg = leg.resize((nw, nh), Image.Resampling.LANCZOS)
lx = (bw - nw) // 2
ly = bh + PAD + (LEGEND_H - nh) // 2
panel = Image.new("RGBA", (bw - 20, LEGEND_H + 8), (255, 255, 255, 255))
pd = ImageDraw.Draw(panel)
pd.rectangle([0, 0, bw - 21, LEGEND_H + 7], outline=(0, 0, 0, 255), width=2)
pd.text((10, 4), "viwaves Simplified Automation (attached legend)", font=load_font(11), fill=(0, 0, 0, 255))
out.paste(panel, (10, bh + 4), panel)
out.paste(leg, (lx, ly), leg)

marked_path = f"{OUT_DIR}/marked-plan.png"
out.convert("RGB").save(marked_path, quality=95)
print("saved", marked_path, out.size)

by_room = defaultdict(Counter)
totals = Counter()
for m in MARKS:
    by_room[m["room"]][m["kind"]] += 1
    totals[m["kind"]] += 1

pdf_path = f"{OUT_DIR}/PROPOSED_FULL_AUTOMATION_MARKING_FOR_REVIEW.pdf"
pw, ph = landscape(A3)
c = canvas.Canvas(pdf_path, pagesize=(pw, ph))
c.setFillColor(HexColor("#c82828"))
c.rect(0, ph - 28, pw, 28, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 11)
c.drawString(16, ph - 19, "PROPOSED FULL AUTOMATION MARKING — FOR REVIEW  |  Rev4  |  Not for execution")
ir_img = ImageReader(marked_path)
margin = 10
avail_w, avail_h = pw - 2 * margin, ph - 36
img_w, img_h = out.size
sc = min(avail_w / img_w, avail_h / img_h)
dw, dh = img_w * sc, img_h * sc
c.drawImage(ir_img, margin + (avail_w - dw) / 2, margin, width=dw, height=dh)
c.showPage()

c.setFillColor(HexColor("#1a2744"))
c.rect(0, 0, pw, ph, fill=1, stroke=0)
c.setFillColor(HexColor("#f07a28"))
c.setFont("Helvetica-Bold", 20)
c.drawString(36, ph - 48, "PROVISIONAL AUTOMATION SCHEDULE")
c.setFillColor(white)
c.setFont("Helvetica", 9)
c.drawString(36, ph - 66, "P0 / Rev4b  |  First-side bedside 4\"+SW/SO  |  CM on curtains  |  Living SW/SO at sofa side tables  |  10\" doorbell view  |  Entry SW opposite swing")
c.setFillColor(HexColor("#f07a28"))
c.setFont("Helvetica-Bold", 10)
c.drawRightString(pw - 36, ph - 48, "FOR REVIEW")

kinds = ["DB", "SW-W", "SO-W", "SW-B", "SO-B", '10"', '4"', "CM", "Surface GW", "IR"]
zones = {
    "Main Entry / foyer": ["Main Entry"],
    "Living / dining": ["Living side table N", "Living side table S", "Living-dining-kitchen view (doorbell)", "Living / near AC", "Living curtain L", "Living curtain R", "Living entry"],
    "Guest Bedroom": ["Guest entry", "Guest first bedside", "Guest other bedside", "Guest N2 other bedside", "Guest / near AC", "Guest curtain L", "Guest curtain R"],
    "G. Toilet": ["G. Toilet"],
    "Kid's Bedroom": ["Kid's entry", "Kid's first bedside", "Kid's other bedside", "Kid's / near AC", "Kid's curtain L", "Kid's curtain R"],
    "K. Toilet": ["K. Toilet"],
    "Master Bedroom": ["Master entry", "Master first bedside", "Master other bedside", "Master / near AC", "Master curtain L", "Master curtain R"],
    "Master walk-in / M. Toilet": ["Master walk-in", "M. Toilet"],
    "Kitchen / utility": ["Kitchen entry"],
    "PW. Toilet": ["PW. Toilet"],
    "Passage": ["Passage"],
}

def zone_count(rs, kind):
    return sum(by_room[r][kind] for r in rs)

y = ph - 98
c.setFillColor(HexColor("#f07a28"))
c.rect(36, y - 4, pw - 72, 22, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 8)
c.drawString(42, y + 2, "ZONE")
x0 = 220
for i, k in enumerate(kinds):
    c.drawCentredString(x0 + i * 55, y + 2, k)
y -= 22
c.setFont("Helvetica", 8)
alt = False
for zone, rs in zones.items():
    if alt:
        c.setFillColor(HexColor("#2a3a55"))
        c.rect(36, y - 4, pw - 72, 18, fill=1, stroke=0)
    c.setFillColor(white)
    c.drawString(42, y, zone[:34])
    for i, k in enumerate(kinds):
        n = zone_count(rs, k)
        c.drawCentredString(x0 + i * 55, y, str(n) if n else "—")
    y -= 18
    alt = not alt

c.setFillColor(HexColor("#f07a28"))
c.rect(36, y - 4, pw - 72, 20, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 8)
c.drawString(42, y, "PROVISIONAL TOTAL")
for i, k in enumerate(kinds):
    c.drawCentredString(x0 + i * 55, y, str(totals[k]))
y -= 34
c.setFillColor(HexColor("#f07a28"))
c.setFont("Helvetica-Bold", 11)
c.drawString(36, y, "Review before final issue")
y -= 16
c.setFillColor(white)
c.setFont("Helvetica", 9)
for n in [
    "1. Rev4: 4\" sits with SW/SO on the first bedside wall when entering; other bedside keeps SW/SO on the side-table wall.",
    "2. CM at left/right ends of drawn curtain tracks. Living SW/SO on wall above sofa side tables only.",
    "3. 10\" on open-plan wall with line-of-sight from living, dining, and kitchen for doorbell video.",
    "4. Toilet SW/SO on basin wall (left or right). Room entry = SW only on wall opposite door swing (latch side).",
    "5. No AC labels on base — GW+IR kept high on TV walls (typical indoor-unit zone). Confirm on site.",
    "6. Furniture base only — not for execution until quote/working sheet confirms quantities.",
]:
    c.drawString(36, y, n); y -= 14
c.setFillColor(HexColor("#8899aa"))
c.setFont("Helvetica", 8)
c.drawString(36, 28, "VLights / viwaves proposed automation marking  |  P0 Rev4  |  Not for execution")
c.save()
print("PDF", pdf_path)
print("TOTALS", dict(totals))
print("MARK_COUNT", len(MARKS))
