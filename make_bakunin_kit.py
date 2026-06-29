#!/usr/bin/env python3
"""Bakunin mō Aotearoa — social kit generator.

Black / white / red Kiwi Dialectic palette.
Motif: black five-point star (Zapatista) anchored on a red poutama (stepped tukutuku)
chevron and a white tāheke (waterfall) line — the Bakunin refrain rendered for Aotearoa.
No AI-generated imagery; pure typographic + geometric vector composition.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math, zipfile

OUT = Path(__file__).parent / "assets" / "social-kit-bakunin"
OUT.mkdir(parents=True, exist_ok=True)

BLACK = (12, 12, 12)
WHITE = (245, 240, 230)   # warm off-white, matches KD palette
RED   = (196, 30, 30)
MUTED = (110, 110, 110)

# Try to find a heavy display font; fall back gracefully.
def font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

# ---------- motif primitives ----------

def star(draw, cx, cy, r, fill, rot=-math.pi/2):
    """Five-point star — the Zapatista/EZLN mark, repatriated in black."""
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    draw.polygon(pts, fill=fill)

def poutama(draw, x, y, step, n, color, flip=False):
    """Red stepped chevron — tukutuku poutama, the staircase of learning."""
    for i in range(n):
        sy = y - i * step if not flip else y + i * step
        draw.rectangle([x + i * step, sy - step, x + (i + 1) * step, sy], fill=color)

def taheke(draw, x1, y1, x2, color, width):
    """White waterfall line — the tāheke that falls and feeds."""
    draw.line([(x1, y1), (x2, y1)], fill=color, width=width)
    # short vertical drops along the line
    for px in range(x1 + 60, x2, 120):
        draw.line([(px, y1), (px, y1 + 40)], fill=color, width=max(2, width // 3))

# ---------- master composition ----------

def compose(W, H, title, sub, tag="THE KIWI DIALECTIC · AI WARRIOR · COURSE 6"):
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)

    # Red poutama band along the very bottom, stepping up — kept clear of subtitle.
    step = max(12, min(W, H) // 60)
    poutama(d, x=int(W * 0.05), y=H - int(H * 0.025), step=step, n=8, color=RED)

    # White tāheke line across mid-upper
    taheke(d, x1=int(W * 0.06), y1=int(H * 0.18), x2=int(W * 0.94), color=WHITE, width=max(3, H // 280))

    # Big black star with red outline halo, top-right anchor
    star_r = int(min(W, H) * 0.18)
    sx, sy = int(W * 0.82), int(H * 0.32)
    # red halo
    star(d, sx, sy, int(star_r * 1.06), RED)
    star(d, sx, sy, star_r, WHITE)
    star(d, sx, sy, int(star_r * 0.86), BLACK)

    # Typography block
    pad = int(W * 0.06)
    tag_f = font(max(14, H // 50))
    title_f = font(max(40, H // 9))
    sub_f = font(max(18, H // 36), bold=False)

    d.text((pad, int(H * 0.28)), tag, font=tag_f, fill=RED)

    # title — uppercase, may wrap manually
    title_y = int(H * 0.36)
    for line in title:
        d.text((pad, title_y), line, font=title_f, fill=WHITE)
        bbox = d.textbbox((pad, title_y), line, font=title_f)
        title_y = bbox[3] + int(H * 0.005)

    d.text((pad, int(H * 0.72)), sub, font=sub_f, fill=WHITE)

    # footer URL — right-aligned, well clear of the poutama band
    foot_f = font(max(14, H // 60))
    foot_text = "kiwidialectic.com/s/courses"
    fb = d.textbbox((0, 0), foot_text, font=foot_f)
    d.text((W - pad - (fb[2] - fb[0]), int(H * 0.83)), foot_text, font=foot_f, fill=MUTED)

    return img

# ---------- avatar (square logo mark) ----------

def avatar(size=1000):
    img = Image.new("RGB", (size, size), BLACK)
    d = ImageDraw.Draw(img)
    # red halo ring
    d.ellipse([size*0.06, size*0.06, size*0.94, size*0.94], outline=RED, width=max(6, size//70))
    star(d, size//2, size//2, int(size*0.32), WHITE)
    star(d, size//2, size//2, int(size*0.27), BLACK)
    # small poutama at base
    poutama(d, x=int(size*0.34), y=int(size*0.82), step=int(size*0.025), n=6, color=RED)
    f = font(max(20, size//28))
    d.text((size*0.5 - size*0.22, size*0.88), "BAKUNIN · AOTEAROA", font=f, fill=WHITE)
    return img

# ---------- specs ----------

TITLE = ["TANGI O TE", "TĀHEKE"]
SUB_LONG = "Bakunin mō Aotearoa — federation from below, refusal of the Leviathan. Six lessons. Free."
SUB_SHORT = "Bakunin for Aotearoa. Six lessons. Free."

SPECS = [
    ("tw-post-1600x900.png",     1600,  900, TITLE, SUB_LONG),
    ("tw-header-1500x500.png",   1500,  500, ["TANGI O TE TĀHEKE"], SUB_SHORT),
    ("ig-square-1080x1080.png",  1080, 1080, TITLE, SUB_SHORT),
    ("ig-portrait-1080x1350.png",1080, 1350, TITLE, SUB_LONG),
    ("ig-story-1080x1920.png",   1080, 1920, TITLE, SUB_LONG),
    ("li-post-1200x627.png",     1200,  627, TITLE, SUB_LONG),
    ("li-banner-1584x396.png",   1584,  396, ["TANGI O TE TĀHEKE — BAKUNIN MŌ AOTEAROA"], SUB_SHORT),
]

made = []
for name, w, h, title, sub in SPECS:
    img = compose(w, h, title, sub)
    p = OUT / name
    img.save(p, "PNG", optimize=True)
    made.append(p)
    print("wrote", p.name)

av = avatar()
ap = OUT / "avatar-1000x1000.png"
av.save(ap, "PNG", optimize=True)
made.append(ap)
print("wrote", ap.name)

# Bundle zip
zp = OUT / "bakunin-mo-aotearoa-social-kit.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for p in made:
        z.write(p, arcname=p.name)
print("wrote", zp.name)
