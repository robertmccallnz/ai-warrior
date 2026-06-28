"""Generate the AI Warrior social media kit — constructivist posters at platform-correct sizes."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/user/workspace/ai-warrior/assets/social-kit"
os.makedirs(OUT, exist_ok=True)

RED = (215, 38, 30)
BLK = (10, 10, 10)
WHT = (245, 245, 245)

DISPLAY_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
BODY_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

def find_font(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def text_size(d, txt, font):
    bb = d.textbbox((0, 0), txt, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb

def fit_font(d, text, max_w, max_h, candidates, start, min_size=14):
    """Binary-search the largest font size where text fits in max_w × max_h."""
    lo, hi = min_size, start
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        f = find_font(candidates, mid)
        w, h, _ = text_size(d, text, f)
        if w <= max_w and h <= max_h:
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    return find_font(candidates, best)

def draw_poster(w, h, headline_lines, subline, kicker, filename, layout="portrait"):
    img = Image.new("RGB", (w, h), BLK)
    d = ImageDraw.Draw(img, "RGBA")

    # subtle grid
    step = max(40, min(w, h) // 30)
    for x in range(0, w, step): d.line([(x, 0), (x, h)], fill=(255, 255, 255, 10))
    for y in range(0, h, step): d.line([(0, y), (w, y)], fill=(255, 255, 255, 10))

    # red wedge + black diagonal slash
    if layout == "portrait":
        d.polygon([(0,0),(int(w*0.62),0),(int(w*0.30),h),(0,h)], fill=RED)
        d.polygon([(int(w*0.58),0),(w,0),(w,int(h*0.20)),(int(w*0.40),h),(int(w*0.12),h)], fill=BLK)
    elif layout == "square":
        d.polygon([(0,0),(int(w*0.50),0),(int(w*0.20),h),(0,h)], fill=RED)
        d.polygon([(int(w*0.46),0),(w,0),(w,int(h*0.22)),(int(w*0.32),h),(int(w*0.06),h)], fill=BLK)
    else:  # landscape
        d.polygon([(0,0),(int(w*0.42),0),(int(w*0.22),h),(0,h)], fill=RED)
        d.polygon([(int(w*0.38),0),(w,0),(w,int(h*0.32)),(int(w*0.22),h),(int(w*0.02),h)], fill=BLK)

    # AI mark — top-right, clean ring with red AI text
    cx = int(w * 0.84); cy = int(h * (0.18 if layout != "landscape" else 0.24))
    r  = int(min(w, h) * 0.10)
    ring_w = max(5, int(r * 0.08))
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=WHT, width=ring_w)
    inner_r = int(r * 0.78)
    ai_font = find_font(DISPLAY_FONTS, int(r * 1.05))
    tw, th, bb = text_size(d, "AI", ai_font)
    d.text((cx - tw/2 - bb[0], cy - th/2 - bb[1]), "AI", font=ai_font, fill=RED)

    # KICKER
    kicker_font = find_font(DISPLAY_FONTS, max(14, int(h * 0.020)))
    kx = int(w * 0.06); ky = int(h * 0.06)
    d.rectangle([kx, ky, kx + int(w * 0.14), ky + max(3, int(h * 0.008))], fill=WHT)
    d.text((kx, ky + int(h * 0.018)), kicker, font=kicker_font, fill=WHT)

    # HEADLINE — autofit to safe area
    left   = int(w * 0.06)
    right  = int(w * 0.94)
    safe_w = right - left
    bot_pad   = int(h * 0.16)   # space reserved for subline + brand
    head_top  = ky + int(h * 0.10)
    head_bot  = h - bot_pad
    line_gap_factor = 0.10

    # try a size that fits the widest line in width AND the stack in height
    widest = max(headline_lines, key=lambda s: len(s))
    start = int(min(safe_w / max(1, len(widest)) * 1.9, h * 0.30))

    def stack_h(fnt):
        total = 0
        for i, L in enumerate(headline_lines):
            _, lh, _ = text_size(d, L, fnt)
            total += lh
            if i < len(headline_lines) - 1:
                total += int(lh * line_gap_factor)
        return total

    lo, hi, best = 18, start, 18
    while lo <= hi:
        mid = (lo + hi) // 2
        f = find_font(DISPLAY_FONTS, mid)
        max_line_w = max(text_size(d, L, f)[0] for L in headline_lines)
        if max_line_w <= safe_w and stack_h(f) <= (head_bot - head_top):
            best = mid; lo = mid + 1
        else:
            hi = mid - 1
    head_font = find_font(DISPLAY_FONTS, best)

    # draw stack bottom-up from head_bot
    y = head_bot
    for L in reversed(headline_lines):
        _, lh, bb = text_size(d, L, head_font)
        y -= lh
        d.text((left - bb[0], y - bb[1]), L, font=head_font, fill=WHT)
        y -= int(lh * line_gap_factor)

    # SUBLINE — autofit width
    if subline:
        sub_max = safe_w
        sub_font = fit_font(d, subline, sub_max, int(h * 0.05), BODY_FONTS, int(h * 0.04))
        d.text((left, h - int(h * 0.10)), subline, font=sub_font, fill=WHT)

    # bottom red rule + brand
    rule_y = h - int(h * 0.035)
    d.rectangle([left, rule_y, left + int(w * 0.10), rule_y + max(4, int(h * 0.008))], fill=RED)
    brand_font = find_font(DISPLAY_FONTS, max(14, int(h * 0.022)))
    d.text((left, rule_y + int(h * 0.012)), "KIWIDIALECTIC.COM", font=brand_font, fill=WHT)

    out = os.path.join(OUT, filename)
    img.save(out, "PNG", optimize=True)
    print(f"wrote {filename} ({w}x{h})")

specs = [
    (1600, 900,  ["TRAIN THE MIND", "ARM THE CLASS"],     "Six modules. Six thinkers. Free at kiwidialectic.com",  "AI WARRIOR · TWITTER POST", "tw-post-1600x900.png",     "landscape"),
    (1500, 500,  ["AI WARRIOR"],                           "A working-class course in AI literacy",                  "TWITTER / X HEADER",        "tw-header-1500x500.png",   "landscape"),
    (1200, 627,  ["BECOME AN", "AI WARRIOR"],              "Pedagogy of the oppressed, refitted for the algorithm.", "LINKEDIN POST",             "li-post-1200x627.png",     "landscape"),
    (1584, 396,  ["AI WARRIOR"],                           "kiwidialectic.com  ·  Otepoti",                          "LINKEDIN BANNER",           "li-banner-1584x396.png",   "landscape"),
    (1080, 1080, ["BECOME AN", "AI WARRIOR"],              "Six modules. Six thinkers. One praxis.",                 "INSTAGRAM SQUARE",          "ig-square-1080x1080.png",  "square"),
    (1080, 1350, ["TRAIN", "THE MIND", "ARM THE", "CLASS"],"A course by The Kiwi Dialectic — Otepoti, Aotearoa.",    "INSTAGRAM PORTRAIT",        "ig-portrait-1080x1350.png","portrait"),
    (1080, 1920, ["AI", "WARRIOR"],                        "kiwidialectic.com",                                      "INSTAGRAM STORY · REEL",    "ig-story-1080x1920.png",   "portrait"),
    (1000, 1000, ["AI", "WARRIOR"],                        "Kiwi Dialectic",                                         "PROFILE AVATAR",            "avatar-1000x1000.png",     "square"),
]

for s in specs:
    draw_poster(*s)

print("done")
