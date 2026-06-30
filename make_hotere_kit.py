"""
make_hotere_kit.py
------------------
Generates the Ralph Hotere-style trilingual AI Warrior social media kit.
24 posters: 8 sizes × 3 languages (en / mi / tl)

Design principles (from hotere_aesthetic.md Section 8 + spec):
  - Matte black ground #0A0A0A
  - Single narrow vertical red bar (~8% width) off-centre
  - Roman numeral scratched stencil numerals beside the bar
  - Te reo karakia as opening inscription on EVERY poster
  - Stencil-block headline in ivory
  - Corrugated iron texture overlay ~6% opacity (procedural)
  - Subtle scratch/distress lines at low alpha
  - Off-centre X mark in rusty red
  - Numbered litany at foot
  - Strict palette: black, protest red, rusty red, ivory, ochre-gold, slate-blue
"""

import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ─── OUTPUT DIRS ─────────────────────────────────────────────────────────────
BASE_OUT = "/home/user/workspace/ai-warrior/assets/social-kit-hotere"
for lang in ("en", "mi", "tl", "pt"):
    os.makedirs(os.path.join(BASE_OUT, lang), exist_ok=True)

# ─── PALETTE ─────────────────────────────────────────────────────────────────
BLK          = (10,  10,  10)          # matte black #0A0A0A
PROTEST_RED  = (192, 40,  10)          # #C0280A
RUSTY_RED    = (139, 37,  0)           # #8B2500
MURUROA_RED  = (204, 17,  0)           # #CC1100
OCHRE_GOLD   = (201, 168, 76)          # #C9A84C
IVORY        = (242, 238, 212)         # #F2EED4
SLATE_BLUE   = (58,  63,  92)          # #3A3F5C
OFF_WHITE    = (235, 230, 210)

# ─── FONTS ───────────────────────────────────────────────────────────────────
FONT_BOLD       = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_COND_BOLD  = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
FONT_LIB_BOLD   = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_LIB_NARROW = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"
FONT_REGULAR    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO       = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ─── MESSAGING ───────────────────────────────────────────────────────────────
KARAKIA = "Whakangungua te hinengaro. Whakangaihia te iwi."

# headline: list of lines per language per format-key
# format keys: wide (landscape), square, tall (portrait/story)
HEADLINES = {
    "en": {
        "wide":   ["TRAIN THE MIND.", "ARM THE CLASS."],
        "square": ["TRAIN THE MIND.", "ARM THE CLASS."],
        "tall":   ["TRAIN", "THE MIND.", "ARM THE", "CLASS."],
        "banner": ["AI WARRIOR · TRAIN THE MIND · ARM THE CLASS"],
        "avatar": ["KD"],
    },
    "mi": {
        "wide":   ["WHAKANGUNGUA TE HINENGARO.", "WHAKANGAIHIA TE IWI."],
        "square": ["WHAKANGUNGUA TE HINENGARO.", "WHAKANGAIHIA TE IWI."],
        "tall":   ["WHAKA-", "NGUNGUA", "TE HINE-", "NGARO.", "WHAKA-", "NGAIHIA", "TE IWI."],
        "banner": ["WHAKANGUNGUA TE HINENGARO · WHAKANGAIHIA TE IWI"],
        "avatar": ["KD"],
    },
    "tl": {
        "wide":   ["SANAYIN ANG ISIP.", "ARMASAN ANG URI."],
        "square": ["SANAYIN ANG ISIP.", "ARMASAN ANG URI."],
        "tall":   ["SANAYIN", "ANG ISIP.", "ARMASAN", "ANG URI."],
        "banner": ["SANAYIN ANG ISIP · ARMASAN ANG URI · MAGING MANDIRIGMA NG AI"],
        "avatar": ["KD"],
    },
    "pt": {
        "wide":   ["TREINE A MENTE.", "ARME A CLASSE."],
        "square": ["TREINE A MENTE.", "ARME A CLASSE."],
        "tall":   ["TREINE", "A MENTE.", "ARME A", "CLASSE."],
        "banner": ["TREINE A MENTE · ARME A CLASSE · GUERREIRO DA IA"],
        "avatar": ["KD"],
    },
}

SUBLINES = {
    "en": "AI Warrior · Six modules. Six thinkers. One praxis. · kiwidialectic.com",
    "mi": "Toa AI · E ono ngā wāhanga. E ono ngā mātanga. Kotahi te tikanga whakatinana.",
    "tl": "Mandirigma ng AI · Anim na modyul. Anim na nag-isip. Isang praksis.",
    "pt": "Guerreiro da IA · Seis módulos. Seis pensadores. Uma práxis. · kiwidialectic.com",
}

MODULE_ROMAN = ["I", "II", "III", "IV", "V", "VI"]
MODULE_LITANY = "I · II · III · IV · V · VI"

# ─── SIZES SPEC ──────────────────────────────────────────────────────────────
# (w, h, platform_key, format_key, filename_pattern)
SIZES = [
    (1600, 900,  "tw-post",     "wide",   "kd-hotere-tw-post-1600x900.png"),
    (1500, 500,  "tw-header",   "banner", "kd-hotere-tw-header-1500x500.png"),
    (1200, 627,  "li-post",     "wide",   "kd-hotere-li-post-1200x627.png"),
    (1584, 396,  "li-banner",   "banner", "kd-hotere-li-banner-1584x396.png"),
    (1080, 1080, "ig-square",   "square", "kd-hotere-ig-square-1080x1080.png"),
    (1080, 1350, "ig-portrait", "tall",   "kd-hotere-ig-portrait-1080x1350.png"),
    (1080, 1920, "ig-story",    "tall",   "kd-hotere-ig-story-1080x1920.png"),
    (1000, 1000, "avatar",      "avatar", "kd-hotere-avatar-1000x1000.png"),
]

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def text_bbox(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb

def fit_font_single(draw, text, max_w, max_h, font_path, start_size=300, min_size=8):
    """Binary-search largest size where text fits in max_w × max_h."""
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

def fit_font_multiline(draw, lines, max_w, max_h, font_path, start_size=300, min_size=8, gap_ratio=0.12):
    """Binary-search largest size where all lines fit in max_w × max_h."""
    lo, hi, best = min_size, start_size, min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = load_font(font_path, mid)
        line_widths = [text_bbox(draw, L, f)[0] for L in lines]
        line_heights = [text_bbox(draw, L, f)[1] for L in lines]
        total_h = sum(line_heights) + int(line_heights[0] * gap_ratio) * max(0, len(lines)-1)
        if max(line_widths) <= max_w and total_h <= max_h:
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    return load_font(font_path, best)

# ─── PROCEDURAL TEXTURES ─────────────────────────────────────────────────────

def make_corrugated_texture(w, h, opacity=0.06):
    """Vertical sine-wave luminance variation + horizontal grain lines."""
    freq = w / 14.0   # corrugation period ~14 columns
    x_arr = np.arange(w, dtype=np.float32)
    sine_col = (np.sin(x_arr / freq * 2 * math.pi) * 0.5 + 0.5)
    # tile across height
    texture = np.tile(sine_col, (h, 1))
    # horizontal grain at every ~4px
    for row in range(0, h, 4):
        texture[row, :] *= 0.85
    # normalise to 0–255
    texture = (texture * 255 * opacity).astype(np.uint8)
    # build RGBA overlay
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = texture
    arr[:, :, 1] = texture
    arr[:, :, 2] = texture
    arr[:, :, 3] = texture  # alpha same as luminance
    return Image.fromarray(arr, "RGBA")

def apply_scratches(draw, w, h, count=18, seed=42):
    """Draw random thin diagonal scratches at very low alpha."""
    rng = random.Random(seed)
    for _ in range(count):
        x1 = rng.randint(0, w)
        y1 = rng.randint(0, h)
        angle = rng.uniform(25, 65)
        length = rng.randint(int(min(w,h)*0.05), int(min(w,h)*0.20))
        rad = math.radians(angle)
        x2 = x1 + int(length * math.cos(rad))
        y2 = y1 + int(length * math.sin(rad))
        alpha = rng.randint(12, 30)
        draw.line([(x1,y1),(x2,y2)], fill=(242,238,212,alpha), width=1)

def draw_x_mark(draw, cx, cy, size, color_rgb, alpha=45):
    """Draw a faint X mark of given arm size at (cx,cy)."""
    color = color_rgb + (alpha,)
    arm = size // 2
    thick = max(2, size // 10)
    draw.line([(cx-arm, cy-arm),(cx+arm, cy+arm)], fill=color, width=thick)
    draw.line([(cx+arm, cy-arm),(cx-arm, cy+arm)], fill=color, width=thick)

def draw_stencil_numeral(draw, numeral, x, y, size, color, alpha=55, seed=0):
    """Draw a roman numeral with worn-stencil degradation (striped masking)."""
    # Draw full numeral first, then apply horizontal stripe gaps
    font = load_font(FONT_COND_BOLD, size)
    tw, th, bb = text_bbox(draw, numeral, font)
    # Create a small sub-image for the numeral with transparency
    sub = Image.new("RGBA", (tw + 10, th + 10), (0, 0, 0, 0))
    sub_d = ImageDraw.Draw(sub)
    r, g, b = color
    sub_d.text((5 - bb[0], 5 - bb[1]), numeral, font=font, fill=(r, g, b, alpha))
    # Degrade: random horizontal strips of reduced alpha
    rng = random.Random(seed + 17)
    arr = np.array(sub)
    sub_h = arr.shape[0]
    for row in range(0, sub_h, rng.randint(3, 7)):
        if rng.random() < 0.35:
            strip_h = rng.randint(1, 3)
            end_row = min(row + strip_h, sub_h)
            arr[row:end_row, :, 3] = (arr[row:end_row, :, 3] * 0.15).astype(np.uint8)
    sub_degraded = Image.fromarray(arr, "RGBA")
    # Paste back. draw is on an RGBA canvas composite.
    return sub_degraded, x, y  # caller pastes this

# ─── CORE POSTER BUILDER ─────────────────────────────────────────────────────

def build_poster(w, h, lang, fmt_key, out_path, rng_seed=0):
    rng = random.Random(rng_seed)

    # ── BASE: matte black ──
    img = Image.new("RGBA", (w, h), BLK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── CORRUGATED IRON TEXTURE OVERLAY ──
    corr = make_corrugated_texture(w, h, opacity=0.06)
    img.alpha_composite(corr)
    draw = ImageDraw.Draw(img, "RGBA")  # refresh draw after composite

    is_banner  = fmt_key == "banner"
    is_avatar  = fmt_key == "avatar"
    is_tall    = fmt_key in ("tall",)
    is_square  = fmt_key == "square"
    is_wide    = fmt_key == "wide"

    # ── RED BAR — off-centre, ~8% width, full height ──
    bar_w = max(8, int(w * 0.075))
    # Off-centre: about 1/3 from left (never centred)
    # For variety: banner at ~65%, avatar pushed to far right edge so KD/AI WARRIOR stay clean
    if is_banner:
        bar_x = int(w * 0.63)
    elif is_avatar:
        bar_x = int(w * 0.88)
    else:
        bar_x = int(w * 0.32)
    # Use protest red as primary; rusty red as accent for some
    bar_color = PROTEST_RED if rng.random() > 0.3 else RUSTY_RED
    draw.rectangle([bar_x, 0, bar_x + bar_w, h], fill=bar_color + (240,))
    # Thin inner shadow line (dark) for depth
    draw.line([(bar_x + bar_w, 0), (bar_x + bar_w, h)], fill=(0, 0, 0, 80), width=2)

    # ── ROMAN NUMERAL STENCILS beside bar ──
    # Split I-VI into top trio (above headline) and bottom trio (below subline/litany)
    # to avoid colliding with the headline band (0.13h–0.83h).
    if not is_banner:
        roman_size = max(14, int(h * 0.045))
        roman_x = bar_x - int(bar_w * 1.6)  # left of bar
        if roman_x < 8:
            roman_x = bar_x + bar_w + 4     # right of bar if too close to edge
        # Top band: 0.02h–0.11h (above karakia + bar of headline). 3 numerals.
        top_band_top = int(h * 0.115)
        top_band_bot = int(h * 0.185)
        # Bottom band: 0.86h–0.95h (below litany). 3 numerals.
        bot_band_top = int(h * 0.78)
        bot_band_bot = int(h * 0.86)
        top_step = (top_band_bot - top_band_top) // 2 if top_band_bot > top_band_top else 0
        bot_step = (bot_band_bot - bot_band_top) // 2 if bot_band_bot > bot_band_top else 0
        positions = [
            top_band_top + 0 * top_step,
            top_band_top + 1 * top_step,
            top_band_top + 2 * top_step,
            bot_band_top + 0 * bot_step,
            bot_band_top + 1 * bot_step,
            bot_band_top + 2 * bot_step,
        ]
        for i, rom in enumerate(MODULE_ROMAN):
            ry = positions[i]
            sub_img, rx, ry_actual = draw_stencil_numeral(
                draw, rom, roman_x, ry, roman_size, IVORY, alpha=55, seed=rng_seed + i
            )
            img.alpha_composite(sub_img, dest=(rx, ry_actual))
        draw = ImageDraw.Draw(img, "RGBA")  # refresh

    # ── OFF-CENTRE X MARK ── faint, rusty red, asymmetric position
    if not is_banner:
        x_size = max(20, int(min(w,h) * 0.05))
        # Place in upper-right or lower-left quadrant, never centred
        if is_avatar:
            xcx = int(w * 0.22)
            xcy = int(h * 0.78)
        elif is_tall:
            xcx = int(w * 0.72)
            xcy = int(h * 0.27)
        else:
            xcx = int(w * 0.68)
            xcy = int(h * 0.22)
        draw_x_mark(draw, xcx, xcy, x_size, RUSTY_RED, alpha=40)

    # ── KARAKIA — top inscription, small caps, ivory ──
    # On every poster regardless of language
    if is_avatar:
        # Avatar: karakia omitted (too small to read), just KD mark
        pass
    elif is_banner:
        # Banner: single line karakia at far left, very small
        kar_size = max(10, int(h * 0.10))
        kar_font = fit_font_single(draw, KARAKIA, int(w * 0.55), int(h * 0.22),
                                   FONT_COND_BOLD, start_size=kar_size + 20, min_size=8)
        kw, kh, kbb = text_bbox(draw, KARAKIA, kar_font)
        draw.text((int(w * 0.03) - kbb[0], int(h * 0.08) - kbb[1]),
                  KARAKIA, font=kar_font, fill=IVORY + (200,))
    else:
        # Standard: top of poster. Karakia spans full width above the red bar zone.
        # We let it cross the bar (over-painted as Hotere does with text over field).
        kar_margin_x = int(w * 0.04)
        kar_safe_w = w - 2 * kar_margin_x  # full width minus margins on both sides
        kar_start_x = kar_margin_x

        kar_max_h = int(h * 0.07)
        kar_font = fit_font_single(draw, KARAKIA, kar_safe_w, kar_max_h,
                                   FONT_COND_BOLD, start_size=min(80, int(h * 0.055)), min_size=8)
        kw, kh, kbb = text_bbox(draw, KARAKIA, kar_font)
        draw.text((kar_start_x - kbb[0], int(h * 0.025) - kbb[1]),
                  KARAKIA, font=kar_font, fill=IVORY + (180,))
        # Thin ochre underline beneath karakia (spans only the actual text width)
        under_y = int(h * 0.025) + kh + 4
        draw.rectangle([kar_start_x, under_y, kar_start_x + kw, under_y + max(2, int(h*0.003))],
                        fill=OCHRE_GOLD + (120,))

    # ── HEADLINE ──
    headlines = HEADLINES[lang][fmt_key]
    if is_avatar:
        # Large "KD" stencil mark centred
        av_safe_w = int(w * 0.55)
        av_safe_h = int(h * 0.50)
        av_font = fit_font_single(draw, "KD", av_safe_w, av_safe_h,
                                  FONT_BOLD, start_size=400, min_size=40)
        tw, th, tbb = text_bbox(draw, "KD", av_font)
        ax = (w - tw) // 2 - tbb[0]
        ay = int(h * 0.28) - tbb[1]
        draw.text((ax, ay), "KD", font=av_font, fill=IVORY + (240,))
        # "AI WARRIOR" below in smaller stencil
        sub_font = fit_font_single(draw, "AI WARRIOR", int(w * 0.70), int(h * 0.12),
                                   FONT_COND_BOLD, start_size=150, min_size=14)
        sw, sh, sbb = text_bbox(draw, "AI WARRIOR", sub_font)
        draw.text(((w - sw) // 2 - sbb[0], int(h * 0.70) - sbb[1]),
                  "AI WARRIOR", font=sub_font, fill=PROTEST_RED + (220,))
    elif is_banner:
        # Single line headline
        head_text = headlines[0]
        head_safe_w = int(w * 0.58)
        head_safe_h = int(h * 0.55)
        head_font = fit_font_single(draw, head_text, head_safe_w, head_safe_h,
                                    FONT_BOLD, start_size=500, min_size=14)
        hw, hh, hbb = text_bbox(draw, head_text, head_font)
        hx = int(w * 0.03) - hbb[0]
        hy = (h - hh) // 2 - hbb[1]
        draw.text((hx, hy), head_text, font=head_font, fill=IVORY + (245,))
    else:
        # Multi-line: placed below karakia, above foot
        top_reserved = int(h * 0.13)   # karakia area
        bot_reserved = int(h * 0.17)   # subline + litany area
        head_zone_top = top_reserved
        head_zone_h   = h - top_reserved - bot_reserved
        head_safe_w   = int(w * 0.82) if (bar_x > w * 0.5) else int(w * 0.88)

        head_font = fit_font_multiline(draw, headlines, head_safe_w, head_zone_h,
                                       FONT_BOLD, start_size=500, min_size=14, gap_ratio=0.10)
        # compute total stack height
        line_hs = [text_bbox(draw, L, head_font)[1] for L in headlines]
        gap = int(line_hs[0] * 0.10) if line_hs else 0
        total_stack = sum(line_hs) + gap * max(0, len(headlines) - 1)
        # position: bottom-aligned in head zone (allow breathing room)
        y_cursor = head_zone_top + max(0, (head_zone_h - total_stack) // 2)
        left_margin = int(w * 0.04)

        for i, line in enumerate(headlines):
            lw, lh, lbb = text_bbox(draw, line, head_font)
            draw.text((left_margin - lbb[0], y_cursor - lbb[1]),
                      line, font=head_font, fill=IVORY + (245,))
            y_cursor += lh + gap

    # ── SUBLINE ──
    if not is_avatar and not is_banner:
        sub_text = SUBLINES[lang]
        sub_safe_w = int(w * 0.88)
        sub_safe_h = int(h * 0.06)
        sub_font = fit_font_single(draw, sub_text, sub_safe_w, sub_safe_h,
                                   FONT_COND_BOLD, start_size=120, min_size=8)
        sw, sh, sbb = text_bbox(draw, sub_text, sub_font)
        draw.text((int(w * 0.04) - sbb[0], h - int(h * 0.13) - sbb[1]),
                  sub_text, font=sub_font, fill=IVORY + (160,))

    # ── FOOT LITANY: "I · II · III · IV · V · VI" ──
    # Sits above the foot brand bar (which lives at h*0.025 from bottom).
    if not is_avatar and not is_banner:
        lit_safe_w = int(w * 0.88)
        lit_safe_h = int(h * 0.035)
        lit_font = fit_font_single(draw, MODULE_LITANY, lit_safe_w, lit_safe_h,
                                   FONT_MONO, start_size=80, min_size=8)
        lw, lh, lbb = text_bbox(draw, MODULE_LITANY, lit_font)
        # Right-align to keep clear of brand text on the left
        lit_x = w - int(w * 0.04) - lw - lbb[0]
        draw.text((lit_x, h - int(h * 0.075) - lbb[1]),
                  MODULE_LITANY, font=lit_font, fill=OCHRE_GOLD + (160,))
    elif is_banner:
        # Banner: litany in ochre at right side
        lit_safe_w = int(w * 0.15)
        lit_safe_h = int(h * 0.55)
        lit_font = fit_font_single(draw, MODULE_LITANY, lit_safe_w, lit_safe_h,
                                   FONT_MONO, start_size=80, min_size=8)
        lw, lh, lbb = text_bbox(draw, MODULE_LITANY, lit_font)
        draw.text((int(w * 0.95) - lw - lbb[0], (h - lh) // 2 - lbb[1]),
                  MODULE_LITANY, font=lit_font, fill=OCHRE_GOLD + (150,))

    # ── SCRATCHES / DISTRESS ──
    apply_scratches(draw, w, h, count=max(12, int(w * h / 80000)), seed=rng_seed + 100)

    # ── FOOT BAR: small red rectangle + "THE KIWI DIALECTIC · ŌTEPOTI" ──
    if not is_avatar:
        brand_str = "THE KIWI DIALECTIC · ŌTEPOTI AOTEAROA"
        foot_y = h - max(6, int(h * 0.025))
        draw.rectangle([int(w * 0.04), foot_y - max(3, int(h*0.006)),
                         int(w * 0.04) + max(4, int(w * 0.08)), foot_y],
                        fill=PROTEST_RED + (200,))
        brand_font = load_font(FONT_COND_BOLD, max(10, int(h * 0.020)))
        draw.text((int(w * 0.04), foot_y - int(h * 0.032)),
                  brand_str, font=brand_font, fill=IVORY + (130,))

    # ── CONVERT TO RGB AND SAVE ──
    out_img = img.convert("RGB")
    out_img.save(out_path, "PNG", optimize=True)
    print(f"  wrote {os.path.relpath(out_path)}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print("Building Hotere-style social kit…")
    count = 0
    seed_base = 1337
    for lang in ("en", "mi", "tl"):
        print(f"\n  Language: {lang}")
        for (w, h, plat_key, fmt_key, fname) in SIZES:
            out_path = os.path.join(BASE_OUT, lang, fname)
            rng_seed = seed_base + hash(lang + fname) % 9999
            build_poster(w, h, lang, fmt_key, out_path, rng_seed=rng_seed)
            count += 1
    print(f"\nDone — {count} posters written to {BASE_OUT}")
    return count

if __name__ == "__main__":
    main()
