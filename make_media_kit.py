"""
make_media_kit.py
-----------------
Generates the AI Warrior graduate media kit:
  1. Certificate of completion (A4 landscape 2480×1748)
  2. Three graduate share cards (LinkedIn 1200×627, Twitter 1600×900, Instagram 1080×1080)
     × 3 languages = 9 share cards
  3. Press release template (Markdown)
  4. README (Markdown)

All images use the Ralph Hotere aesthetic.
"""

import os
import math
import random
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ─── OUTPUT DIR ───────────────────────────────────────────────────────────────
MEDIA_OUT = "/home/user/workspace/ai-warrior/assets/media-kit"
os.makedirs(MEDIA_OUT, exist_ok=True)

# ─── PALETTE ──────────────────────────────────────────────────────────────────
BLK          = (10,  10,  10)
PROTEST_RED  = (192, 40,  10)
RUSTY_RED    = (139, 37,  0)
OCHRE_GOLD   = (201, 168, 76)
IVORY        = (242, 238, 212)
SLATE_BLUE   = (58,  63,  92)

# ─── FONTS ────────────────────────────────────────────────────────────────────
FONT_BOLD       = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_COND_BOLD  = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FONT_LIB_BOLD   = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_LIB_NARROW = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"
FONT_REGULAR    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO       = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SERIF      = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_ITALIC     = "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def text_bbox(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb

def fit_font_single(draw, text, max_w, max_h, font_path, start_size=300, min_size=8):
    lo, hi, best = min_size, start_size, min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = load_font(font_path, mid)
        w, h, _ = text_bbox(draw, text, f)
        if w <= max_w and h <= max_h:
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    return load_font(font_path, best)

def fit_font_multiline(draw, lines, max_w, max_h, font_path,
                       start_size=300, min_size=8, gap_ratio=0.12):
    lo, hi, best = min_size, start_size, min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = load_font(font_path, mid)
        lw = [text_bbox(draw, L, f)[0] for L in lines]
        lh = [text_bbox(draw, L, f)[1] for L in lines]
        if not lh:
            best = mid; lo = mid + 1; continue
        total_h = sum(lh) + int(lh[0] * gap_ratio) * max(0, len(lines) - 1)
        if max(lw) <= max_w and total_h <= max_h:
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    return load_font(font_path, best)

def make_corrugated_texture(w, h, opacity=0.06):
    freq = w / 14.0
    x_arr = np.arange(w, dtype=np.float32)
    sine_col = np.sin(x_arr / freq * 2 * math.pi) * 0.5 + 0.5
    texture = np.tile(sine_col, (h, 1))
    for row in range(0, h, 4):
        texture[row, :] *= 0.85
    texture = (texture * 255 * opacity).astype(np.uint8)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = texture
    arr[:, :, 1] = texture
    arr[:, :, 2] = texture
    arr[:, :, 3] = texture
    return Image.fromarray(arr, "RGBA")

def apply_scratches(draw, w, h, count=18, seed=42):
    rng = random.Random(seed)
    for _ in range(count):
        x1 = rng.randint(0, w); y1 = rng.randint(0, h)
        angle = rng.uniform(20, 70)
        length = rng.randint(int(min(w, h) * 0.04), int(min(w, h) * 0.18))
        rad = math.radians(angle)
        x2 = x1 + int(length * math.cos(rad))
        y2 = y1 + int(length * math.sin(rad))
        alpha = rng.randint(10, 25)
        draw.line([(x1, y1), (x2, y2)], fill=(242, 238, 212, alpha), width=1)

def draw_x_mark(draw, cx, cy, size, alpha=40):
    arm = size // 2
    thick = max(2, size // 10)
    c = RUSTY_RED + (alpha,)
    draw.line([(cx - arm, cy - arm), (cx + arm, cy + arm)], fill=c, width=thick)
    draw.line([(cx + arm, cy - arm), (cx - arm, cy + arm)], fill=c, width=thick)

def draw_red_bar(draw, w, h, x_frac=0.30, w_frac=0.07, color=None):
    if color is None:
        color = PROTEST_RED
    bar_w = max(8, int(w * w_frac))
    bar_x = int(w * x_frac)
    draw.rectangle([bar_x, 0, bar_x + bar_w, h], fill=color + (240,))
    draw.line([(bar_x + bar_w, 0), (bar_x + bar_w, h)], fill=(0, 0, 0, 80), width=2)
    return bar_x, bar_w

KARAKIA = "Whakangungua te hinengaro. Whakangaihia te iwi."
MODULE_ROMAN  = ["I", "II", "III", "IV", "V", "VI"]
MODULE_LITANY = "I · II · III · IV · V · VI"

MODULE_NAMES = {
    "en": [
        "I  — See the Frame (Gramsci)",
        "II  — Build with Purpose (Kropotkin)",
        "III — Emotional Sovereignty (Graeber)",
        "IV  — Advocate by Creating (Freire)",
        "V  — Systems Thinking (Deleuze)",
        "VI  — Arm the Class (Bakunin)",
    ],
    "mi": [
        "I  — Kitea te Anga",
        "II  — Hangaia mā te Kaupapa",
        "III — Mana Ngākau",
        "IV  — Tautoko mā te Auaha",
        "V  — Whakaaro Pūnaha",
        "VI  — Whakangaihia te Iwi",
    ],
    "tl": [
        "I  — Tingnan ang Balangkas",
        "II  — Itayo nang may Layunin",
        "III — Soberanya ng Damdamin",
        "IV  — Magtaguyod sa Paglikha",
        "V  — Pag-iisip Sistematiko",
        "VI  — Armasan ang Uri",
    ],
}

GRAD_COPY = {
    "en": [
        "I trained the mind.",
        "Now I arm the class.",
    ],
    "mi": [
        "Kua whakangungua e au tōku hinengaro.",
        "Ināianei, ka whakangaihia e au te iwi.",
    ],
    "tl": [
        "Sinanay ko ang isip.",
        "Ngayon, aarmasan ko ang uri.",
    ],
}

GRAD_SUBLINE = {
    "en": "AI Warrior · graduate of The Kiwi Dialectic  · Six modules. Six thinkers. One praxis.",
    "mi": "Toa AI · tauira whakaoti o Te Kōrero Kiwi · E ono ngā wāhanga. Kotahi te tikanga whakatinana.",
    "tl": "Mandirigma ng AI · nagtapos sa The Kiwi Dialectic · Anim na modyul. Anim na nag-isip. Isang praksis.",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CERTIFICATE
# ═══════════════════════════════════════════════════════════════════════════════

def build_certificate():
    W, H = 2480, 1748  # A4 landscape @ 300dpi
    img = Image.new("RGBA", (W, H), BLK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Corrugated texture
    corr = make_corrugated_texture(W, H, opacity=0.07)
    img.alpha_composite(corr)
    draw = ImageDraw.Draw(img, "RGBA")

    # Red bar — left side ~25%
    bar_x, bar_w = draw_red_bar(draw, W, H, x_frac=0.24, w_frac=0.055)

    # Outer border: thin ivory rectangle
    border_pad = 40
    draw.rectangle([border_pad, border_pad, W - border_pad, H - border_pad],
                   outline=IVORY + (80,), width=3)
    # Inner thin border
    inner_pad = 70
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad],
                   outline=OCHRE_GOLD + (60,), width=1)

    # ── Module names listed on the left panel (left of bar) ──
    left_panel_w = bar_x - 80
    mod_start_x = 50
    mod_start_y = int(H * 0.28)
    mod_size = max(18, int(H * 0.030))
    mod_font = load_font(FONT_COND_BOLD, mod_size)
    for i, mname in enumerate(MODULE_NAMES["en"]):
        ry = mod_start_y + i * int(H * 0.085)
        # Roman numeral in red
        rom = MODULE_ROMAN[i]
        rom_font = load_font(FONT_BOLD, max(18, int(H * 0.038)))
        rw, rh, rbb = text_bbox(draw, rom, rom_font)
        draw.text((mod_start_x - rbb[0], ry - rbb[1]), rom,
                  font=rom_font, fill=PROTEST_RED + (200,))
        # Module title after the numeral
        title = mname.split("—", 1)[-1].strip() if "—" in mname else mname
        title_font = load_font(FONT_COND_BOLD, max(14, int(H * 0.024)))
        draw.text((mod_start_x + rw + 8, ry + (rh - text_bbox(draw, title, title_font)[1]) // 2),
                  title, font=title_font, fill=IVORY + (160,))

    # ── Karakia top centre ──
    kar_font = fit_font_single(draw, KARAKIA, int(W * 0.70), int(H * 0.055),
                               FONT_COND_BOLD, start_size=120, min_size=10)
    kw, kh, kbb = text_bbox(draw, KARAKIA, kar_font)
    kx = bar_x + bar_w + (W - bar_x - bar_w - kw) // 2
    draw.text((kx - kbb[0], int(H * 0.05) - kbb[1]),
              KARAKIA, font=kar_font, fill=IVORY + (190,))
    # Underline
    ul_y = int(H * 0.05) + kh + 6
    draw.rectangle([kx, ul_y, kx + kw, ul_y + 3], fill=OCHRE_GOLD + (120,))

    # ── "CERTIFICATE OF COMPLETION" heading ──
    cert_str = "CERTIFICATE OF COMPLETION"
    cert_font = fit_font_single(draw, cert_str, int(W * 0.66), int(H * 0.075),
                                FONT_BOLD, start_size=200, min_size=14)
    cw, ch, cbb = text_bbox(draw, cert_str, cert_font)
    cx_pos = bar_x + bar_w + (W - bar_x - bar_w - cw) // 2
    draw.text((cx_pos - cbb[0], int(H * 0.15) - cbb[1]),
              cert_str, font=cert_font, fill=IVORY + (240,))

    # Thick ochre rule below heading
    rule_y = int(H * 0.15) + ch + 16
    draw.rectangle([bar_x + bar_w + 40, rule_y,
                    W - 80, rule_y + max(4, int(H * 0.005))],
                   fill=OCHRE_GOLD + (180,))

    # ── "This certifies that" in italic serif ──
    certifies_str = "This certifies that"
    cert2_font = load_font(FONT_ITALIC, max(20, int(H * 0.030)))
    c2w, c2h, c2bb = text_bbox(draw, certifies_str, cert2_font)
    c2x = bar_x + bar_w + (W - bar_x - bar_w - c2w) // 2
    draw.text((c2x - c2bb[0], int(H * 0.33) - c2bb[1]),
              certifies_str, font=cert2_font, fill=IVORY + (180,))

    # ── NAME placeholder (large stencil) ──
    name_str = "{NAME}"
    name_font = fit_font_single(draw, name_str, int(W * 0.65), int(H * 0.12),
                                FONT_BOLD, start_size=400, min_size=30)
    nw, nh, nbb = text_bbox(draw, name_str, name_font)
    nx = bar_x + bar_w + (W - bar_x - bar_w - nw) // 2
    draw.text((nx - nbb[0], int(H * 0.42) - nbb[1]),
              name_str, font=name_font, fill=IVORY + (245,))
    # Underline under name
    name_ul_y = int(H * 0.42) + nh + 8
    draw.rectangle([bar_x + bar_w + 80, name_ul_y,
                    W - 80, name_ul_y + max(2, int(H * 0.003))],
                   fill=IVORY + (80,))

    # ── "has completed AI WARRIOR" ──
    has_str = "has completed AI WARRIOR · The Kiwi Dialectic"
    has_font = fit_font_single(draw, has_str, int(W * 0.65), int(H * 0.055),
                               FONT_COND_BOLD, start_size=180, min_size=14)
    haw, hah, habb = text_bbox(draw, has_str, has_font)
    hax = bar_x + bar_w + (W - bar_x - bar_w - haw) // 2
    draw.text((hax - habb[0], int(H * 0.58) - habb[1]),
              has_str, font=has_font, fill=OCHRE_GOLD + (220,))

    # ── "Six modules…" ──
    six_str = "Six modules. Six thinkers. One praxis."
    six_font = load_font(FONT_COND_BOLD, max(14, int(H * 0.026)))
    sw, sh, sbb = text_bbox(draw, six_str, six_font)
    sx = bar_x + bar_w + (W - bar_x - bar_w - sw) // 2
    draw.text((sx - sbb[0], int(H * 0.655) - sbb[1]),
              six_str, font=six_font, fill=IVORY + (160,))

    # ── DATE placeholder ──
    date_str = "Completed: {DATE}"
    date_font = load_font(FONT_COND_BOLD, max(14, int(H * 0.026)))
    dw, dh, dbb = text_bbox(draw, date_str, date_font)
    draw.text((bar_x + bar_w + 60 - dbb[0], int(H * 0.76) - dbb[1]),
              date_str, font=date_font, fill=IVORY + (180,))

    # ── Signature line — Robert McCall ──
    sig_str = "Robert McCall · The Kiwi Dialectic"
    sig_font = load_font(FONT_ITALIC, max(14, int(H * 0.028)))
    sig2_font = load_font(FONT_COND_BOLD, max(10, int(H * 0.020)))
    sig_y = int(H * 0.80)
    # Underline for signature
    sig_ul_w = int(W * 0.22)
    sig_ul_x = W - 80 - sig_ul_w
    draw.rectangle([sig_ul_x, sig_y, sig_ul_x + sig_ul_w, sig_y + max(2, int(H * 0.002))],
                   fill=IVORY + (120,))
    sw2, sh2, sbb2 = text_bbox(draw, sig_str, sig_font)
    draw.text((sig_ul_x + (sig_ul_w - sw2) // 2 - sbb2[0], sig_y + 8 - sbb2[1]),
              sig_str, font=sig_font, fill=IVORY + (200,))
    # "Kaiako / Instructor" label
    role_str = "Kaiako · Instructor"
    rsw, rsh, rsbb = text_bbox(draw, role_str, sig2_font)
    draw.text((sig_ul_x + (sig_ul_w - rsw) // 2 - rsbb[0], sig_y + sh2 + 14 - rsbb[1]),
              role_str, font=sig2_font, fill=IVORY + (130,))

    # ── Off-centre X mark ──
    draw_x_mark(draw, int(W * 0.72), int(H * 0.27), max(30, int(min(W, H) * 0.04)), alpha=35)

    # ── Foot note ──
    foot_str = "Toa AI · Te Kōrero Kiwi · Ōtepoti Aotearoa"
    foot_font = load_font(FONT_COND_BOLD, max(14, int(H * 0.022)))
    fw, fh, fbb = text_bbox(draw, foot_str, foot_font)
    fx = bar_x + bar_w + (W - bar_x - bar_w - fw) // 2
    draw.text((fx - fbb[0], H - int(H * 0.058) - fbb[1]),
              foot_str, font=foot_font, fill=PROTEST_RED + (190,))

    # ── Litany at foot ──
    lit_font = fit_font_single(draw, MODULE_LITANY, int(W * 0.60), int(H * 0.04),
                               FONT_MONO, start_size=100, min_size=8)
    lw2, lh2, lbb2 = text_bbox(draw, MODULE_LITANY, lit_font)
    lx = bar_x + bar_w + (W - bar_x - bar_w - lw2) // 2
    draw.text((lx - lbb2[0], H - int(H * 0.035) - lbb2[1]),
              MODULE_LITANY, font=lit_font, fill=OCHRE_GOLD + (150,))

    # ── Scratches ──
    apply_scratches(draw, W, H, count=30, seed=2480)

    out_path = os.path.join(MEDIA_OUT, "certificate-blank.png")
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {os.path.relpath(out_path)}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GRADUATE SHARE CARDS
# ═══════════════════════════════════════════════════════════════════════════════

SHARE_CARD_SIZES = [
    (1200, 627,  "li-announce",  "li-post"),
    (1600, 900,  "tw-card",      "tw-post"),
    (1080, 1080, "ig-square",    "ig-square"),
]

def build_share_card(w, h, lang, fmt_label, out_fname, rng_seed=5000):
    img = Image.new("RGBA", (w, h), BLK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Corrugated texture
    corr = make_corrugated_texture(w, h, opacity=0.06)
    img.alpha_composite(corr)
    draw = ImageDraw.Draw(img, "RGBA")

    # Red bar
    bar_x, bar_w = draw_red_bar(draw, w, h, x_frac=0.68, w_frac=0.065,
                                 color=RUSTY_RED)

    # Karakia top
    kar_font = fit_font_single(draw, KARAKIA, int(w * 0.87), int(h * 0.07),
                               FONT_COND_BOLD, start_size=100, min_size=8)
    kw, kh, kbb = text_bbox(draw, KARAKIA, kar_font)
    draw.text((int(w * 0.04) - kbb[0], int(h * 0.04) - kbb[1]),
              KARAKIA, font=kar_font, fill=IVORY + (170,))
    ul_y = int(h * 0.04) + kh + 4
    draw.rectangle([int(w * 0.04), ul_y, int(w * 0.04) + kw, ul_y + max(2, int(h * 0.004))],
                   fill=OCHRE_GOLD + (100,))

    # Graduate copy lines
    lines = GRAD_COPY[lang]
    head_safe_w = int(w * 0.88) if bar_x > w * 0.6 else int(w * 0.60)
    head_safe_h = int(h * 0.42)
    head_font = fit_font_multiline(draw, lines, head_safe_w, head_safe_h,
                                   FONT_BOLD, start_size=400, min_size=14, gap_ratio=0.10)
    lhs = [text_bbox(draw, L, head_font)[1] for L in lines]
    gap = int(lhs[0] * 0.10) if lhs else 0
    total_h = sum(lhs) + gap * max(0, len(lines) - 1)
    y_cur = int(h * 0.18) + max(0, (head_safe_h - total_h) // 2)
    for i, line in enumerate(lines):
        lw2, lh2, lbb2 = text_bbox(draw, line, head_font)
        draw.text((int(w * 0.04) - lbb2[0], y_cur - lbb2[1]),
                  line, font=head_font, fill=IVORY + (245,))
        y_cur += lh2 + gap

    # Bottom stack — ordered: {NAME} (tallest) → subline → litany.
    # Reserve from bottom: litany h*0.05, subline h*0.06, name h*0.10 with gaps.
    name_str = "{NAME}"
    name_safe_h = int(h * 0.085)
    name_font = fit_font_single(draw, name_str, int(w * 0.45), name_safe_h,
                                FONT_COND_BOLD, start_size=200, min_size=14)
    nw, nh, nbb = text_bbox(draw, name_str, name_font)

    sub_text = GRAD_SUBLINE[lang]
    sub_safe_h = int(h * 0.05)
    sub_font = fit_font_single(draw, sub_text, int(w * 0.88), sub_safe_h,
                               FONT_COND_BOLD, start_size=100, min_size=8)
    sw, sh, sbb = text_bbox(draw, sub_text, sub_font)

    lit_safe_h = int(h * 0.04)
    lit_font = fit_font_single(draw, MODULE_LITANY, int(w * 0.55), lit_safe_h,
                               FONT_MONO, start_size=80, min_size=8)
    lw2, lh2, lbb2 = text_bbox(draw, MODULE_LITANY, lit_font)

    # Place from bottom up. Outer margin from bottom edge:
    outer_b = int(h * 0.035)
    # Litany at bottom
    lit_y_bottom = h - outer_b
    draw.text((int(w * 0.04) - lbb2[0], lit_y_bottom - lh2 - lbb2[1]),
              MODULE_LITANY, font=lit_font, fill=OCHRE_GOLD + (150,))
    # Subline above litany with small gap
    sub_gap = int(h * 0.015)
    sub_y_bottom = lit_y_bottom - lh2 - sub_gap
    draw.text((int(w * 0.04) - sbb[0], sub_y_bottom - sh - sbb[1]),
              sub_text, font=sub_font, fill=IVORY + (150,))
    # {NAME} above subline with gap + underline
    name_gap = int(h * 0.020)
    name_y_bottom = sub_y_bottom - sh - name_gap
    draw.rectangle([int(w * 0.04), name_y_bottom - 6, int(w * 0.04) + int(w * 0.38), name_y_bottom - 4],
                   fill=IVORY + (80,))
    draw.text((int(w * 0.04) - nbb[0], name_y_bottom - nh - nbb[1] - 10),
              name_str, font=name_font, fill=PROTEST_RED + (210,))

    # X mark
    draw_x_mark(draw, int(w * 0.78), int(h * 0.30),
                max(20, int(min(w, h) * 0.05)), alpha=40)

    # Scratches
    apply_scratches(draw, w, h, count=15, seed=rng_seed + 200)

    out_path = os.path.join(MEDIA_OUT, out_fname)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    print(f"  wrote {os.path.relpath(out_path)}")
    return out_path


def build_all_share_cards():
    paths = []
    for lang in ("en", "mi", "tl"):
        for (w, h, fmt_label, _plat) in SHARE_CARD_SIZES:
            fname = f"grad-share-{lang}-{fmt_label}-{w}x{h}.png"
            seed = hash(lang + fname) % 9999 + 5000
            p = build_share_card(w, h, lang, fmt_label, fname, rng_seed=seed)
            paths.append(p)
    return paths


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PRESS RELEASE TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════

PRESS_RELEASE = """\
# {NAME} Becomes AI Warrior — Completes The Kiwi Dialectic's Course in Working-Class AI Literacy

**{CITY, COUNTRY — DATE}**

{NAME} has completed *AI Warrior*, the six-module course in working-class AI literacy offered by The Kiwi Dialectic, based in Ōtepoti (Dunedin), Aotearoa New Zealand. The course equips everyday people — workers, community organisers, educators, and activists — with the critical, practical, and political skills needed to read, use, and resist AI tools on their own terms. Drawing on thinkers including Gramsci, Kropotkin, Graeber, Freire, Deleuze, and Bakunin, *AI Warrior* refits the pedagogy of the oppressed for the algorithmic age.

{NAME} joins a growing cohort of AI Warriors who have worked through the six modules: *See the Frame*, *Build with Purpose*, *Emotional Sovereignty*, *Advocate by Creating*, *Systems Thinking*, and *Arm the Class*. {NAME} intends to apply this praxis to [DESCRIBE INTENDED APPLICATION — e.g. community organising / workplace advocacy / digital education in their context]. "QUOTE FROM {NAME}," said {NAME}.

*AI Warrior* is a free, open-access course: free to read, free to share, free to walk with. It is produced by The Kiwi Dialectic in partnership with Te Pā — an open educational kaupapa for indigenous AI and data sovereignty education based in Aotearoa. A charitable trust is being established — expressions of interest open for founding board / kaitiaki seats. The course and all materials are available at <https://robertmccallnz.github.io/ai-warrior/>. Te Pā's work can be followed at <https://te-pa.org/>.

---

**Contact:** hello@te-pa.org

---

## About Te Pā

Te Pā is an open educational kaupapa dedicated to indigenous AI and data sovereignty education in Aotearoa New Zealand and the wider Pacific. A charitable trust is being established — expressions of interest open for founding board / kaitiaki seats. Te Pā works alongside communities, schools, and organisations to ensure that AI literacy is accessible, grounded in te Tiriti o Waitangi, and built on working-class and indigenous epistemologies rather than corporate capture.
"""


def write_press_release():
    path = os.path.join(MEDIA_OUT, "press-release-template.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(PRESS_RELEASE)
    print(f"  wrote {os.path.relpath(path)}")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# 4. README
# ═══════════════════════════════════════════════════════════════════════════════

README_CONTENT = """\
# AI Warrior Graduate Media Kit

This media kit is for graduates of *AI Warrior — The Kiwi Dialectic*.
It contains everything you need to announce your completion on social media,
apply for jobs, or issue a local press release.

---

## Files in this kit

| File | Description |
|------|-------------|
| `certificate-blank.png` | A4 landscape certificate of completion (2480×1748 px, 300 dpi). Hotere-aesthetic design with your name ({NAME}) and date ({DATE}) as placeholders. |
| `grad-share-en-li-announce-1200x627.png` | LinkedIn announcement card — English (1200×627 px) |
| `grad-share-en-tw-card-1600x900.png` | Twitter / X share card — English (1600×900 px) |
| `grad-share-en-ig-square-1080x1080.png` | Instagram square share card — English (1080×1080 px) |
| `grad-share-mi-li-announce-1200x627.png` | LinkedIn announcement card — Te reo Māori (1200×627 px) |
| `grad-share-mi-tw-card-1600x900.png` | Twitter / X share card — Te reo Māori (1600×900 px) |
| `grad-share-mi-ig-square-1080x1080.png` | Instagram square share card — Te reo Māori (1080×1080 px) |
| `grad-share-tl-li-announce-1200x627.png` | LinkedIn announcement card — Tagalog (1200×627 px) |
| `grad-share-tl-tw-card-1600x900.png` | Twitter / X share card — Tagalog (1600×900 px) |
| `grad-share-tl-ig-square-1080x1080.png` | Instagram square share card — Tagalog (1080×1080 px) |
| `press-release-template.md` | Paste-ready press release template in Markdown. Fill in {NAME}, {DATE}, {CITY, COUNTRY}, and your quote. |
| `README.md` | This file. |

---

## How to personalise the certificate and share cards

The certificate and share cards contain `{NAME}` and `{DATE}` placeholders
as stencilled text. To replace them with your actual name and date:

- **Affinity Publisher / Photo:** open the PNG, add a text layer over the placeholder
- **Adobe Photoshop / Illustrator:** open, add type layer, match font (DejaVu Sans Bold or similar heavy condensed sans)
- **GIMP:** Script-Fu or Text Tool — create a text layer, flatten, export
- **Preview (macOS):** use the Markup toolbar → Text tool to add annotation directly
- **Canva / Google Slides:** import the PNG as background image, add a text box over the placeholder

Recommended font to match the Hotere aesthetic: **DejaVu Sans Bold**, **Liberation Sans Bold**,
or any heavy condensed sans-serif. All-caps, ivory (#F2EED4) or near-white.

---

## Social post copy (paste-ready)

### English
> I trained the mind. Now I arm the class.
> AI Warrior · graduate of The Kiwi Dialectic
> Six modules. Six thinkers. One praxis.
> Free course: https://robertmccallnz.github.io/ai-warrior/

### Te reo Māori
> Kua whakangungua e au tōku hinengaro. Ināianei, ka whakangaihia e au te iwi.
> Toa AI · tauira whakaoti o Te Kōrero Kiwi
> E ono ngā wāhanga. E ono ngā mātanga. Kotahi te tikanga whakatinana.
> https://robertmccallnz.github.io/ai-warrior/

### Tagalog
> Sinanay ko ang isip. Ngayon, aarmasan ko ang uri.
> Mandirigma ng AI · nagtapos sa The Kiwi Dialectic
> Anim na modyul. Anim na nag-isip. Isang praksis.
> https://robertmccallnz.github.io/ai-warrior/

---

## Links

- Course: <https://robertmccallnz.github.io/ai-warrior/>
- Te Pā: <https://te-pa.org/>
- Contact: hello@te-pa.org

---

*Whakangungua te hinengaro. Whakangaihia te iwi.*
*Train the mind. Arm the class.*
"""


def write_readme():
    path = os.path.join(MEDIA_OUT, "README.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(README_CONTENT)
    print(f"  wrote {os.path.relpath(path)}")
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ZIP
# ═══════════════════════════════════════════════════════════════════════════════

def build_media_kit_zip():
    zip_path = os.path.join(MEDIA_OUT, "ai-warrior-graduate-media-kit.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(MEDIA_OUT):
            if fname.endswith(".zip"):
                continue
            fpath = os.path.join(MEDIA_OUT, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=fname)
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  wrote media-kit ZIP: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("\nBuilding AI Warrior graduate media kit…")

    print("\n[1/4] Certificate…")
    cert_path = build_certificate()

    print("\n[2/4] Graduate share cards…")
    card_paths = build_all_share_cards()

    print("\n[3/4] Press release + README…")
    pr_path = write_press_release()
    rm_path = write_readme()

    print("\n[4/4] ZIP…")
    zip_path = build_media_kit_zip()

    total = 1 + len(card_paths) + 2  # cert + cards + pr + readme
    print(f"\nDone — {total} files + 1 ZIP in {MEDIA_OUT}")
    return total


if __name__ == "__main__":
    main()
