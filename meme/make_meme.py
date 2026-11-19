#!/usr/bin/env python3
"""Deterministic generator for the make.fun GTA 6 meme entry (gta6-meme-x-01).

A GTA VI launch-week loading screen: thirteen years of waiting, still stuck at
99%, with make.fun's ghost sitting on the progress bar.

Everything is drawn at 2x (2400x2400) and downscaled once with LANCZOS, which is
what keeps the edges and the letterforms clean at 480x480. No clock, no
randomness, no network: two runs write the same bytes.

    python3 meme/make_meme.py   ->  meme/meme.png
"""

from __future__ import annotations

import hashlib
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MARK = os.path.join(ROOT, "assets", "mark-1024.png")
OUT = os.path.join(HERE, "meme.png")

SIZE = 1200          # final edge, px
S = 2                # supersample factor
W = SIZE * S         # drawing edge, px

# --- palette ---------------------------------------------------------------
SKY_STOPS = (
    (0.00, (0x15, 0x07, 0x26)),
    (0.30, (0x4B, 0x13, 0x50)),
    (0.55, (0xA8, 0x27, 0x5A)),
    (0.72, (0xE0, 0x52, 0x1F)),
    (0.80, (0xF7, 0xA5, 0x3C)),
)
SUN = (0xFF, 0xE3, 0xA3)
INK = (0x12, 0x04, 0x0F)          # stroke + drop shadow
SKYLINE = (0x20, 0x0A, 0x1E)
WINDOW = (0xFF, 0xCF, 0x6B)
GROUND = (0x12, 0x05, 0x13)
PALM = (0x0D, 0x04, 0x10)
BAR_TROUGH = (0x24, 0x0A, 0x20)
BAR_FILL = (0xFF, 0x2F, 0xA8)
HOT_PINK = (0xFF, 0x3F, 0xB0)
LILAC = (0xFF, 0xC9, 0xE8)
FOOT = (0xFF, 0xE9, 0xF6)
WHITE = (0xFF, 0xFF, 0xFF)

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)

HORIZON = 800        # ground line / skyline base
GROUND_TOP = 800.0


# --- helpers ---------------------------------------------------------------
def load_font(px: float) -> ImageFont.FreeTypeFont:
    """A heavy face at `px` final-resolution pixels (drawn `S` times bigger)."""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, int(round(px * S)))
    raise SystemExit("no bold font found")


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def sky_image() -> Image.Image:
    """Vertical gradient, interpolated per row, built one pixel wide then widened."""
    column = Image.new("RGB", (1, W))
    px = column.load()
    for y in range(W):
        f = (y + 0.5) / W
        c = SKY_STOPS[-1][1]
        for i in range(len(SKY_STOPS) - 1):
            f0, c0 = SKY_STOPS[i]
            f1, c1 = SKY_STOPS[i + 1]
            if f <= f0:
                c = c0
                break
            if f <= f1:
                c = lerp(c0, c1, (f - f0) / (f1 - f0))
                break
        px[0, y] = c
    return column.resize((W, W), Image.NEAREST)


def quad(p0, p1, p2, n=44):
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        out.append(
            (
                mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1],
            )
        )
    return out


def taper(spine, half_widths):
    """Turn a spine into a closed, tapered polygon (final-res units, scaled by S)."""
    n = len(spine)
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        if i == 0:
            dx, dy = spine[1][0] - x, spine[1][1] - y
        elif i == n - 1:
            dx, dy = x - spine[-2][0], y - spine[-2][1]
        else:
            dx, dy = spine[i + 1][0] - spine[i - 1][0], spine[i + 1][1] - spine[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = half_widths[i]
        left.append(((x + nx * w) * S, (y + ny * w) * S))
        right.append(((x - nx * w) * S, (y - ny * w) * S))
    return left + right[::-1]


def palm(draw, base_x: float, lean: float, height: float = 470.0) -> None:
    """One silhouette palm: a curving trunk that keeps its thickness, seven blades."""
    base = (base_x, HORIZON)
    top = (base_x + lean, HORIZON - height)
    ctrl = (base_x + lean * 0.04, HORIZON - height * 0.60)

    spine = quad(base, ctrl, top, 64)
    widths = [19.0 - 9.0 * (i / (len(spine) - 1)) ** 1.1 for i in range(len(spine))]
    draw.polygon(taper(spine, widths), fill=PALM)

    # root flare so the trunk meets the ground instead of floating on it
    draw.ellipse([(base_x - 21) * S, (HORIZON - 17) * S, (base_x + 21) * S, (HORIZON + 4) * S], fill=PALM)

    # a small crown hub, so the blades come out of a mass instead of a wire end
    draw.ellipse([(top[0] - 17) * S, (top[1] - 15) * S, (top[0] + 17) * S, (top[1] + 17) * S], fill=PALM)

    # seven fronds: a blade that is widest a third of the way out, arcing up then
    # drooping at the tip, with a soft scalloped edge so it reads as a leaf
    angles = (156.0, 188.0, 216.0, 244.0, 274.0, 304.0, 338.0)
    lengths = (166.0, 194.0, 208.0, 190.0, 206.0, 192.0, 166.0)
    crown = (top[0], top[1] - 8.0)
    n = 60
    for ang, ln in zip(angles, lengths):
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        p1 = (crown[0] + dx * ln * 0.50, crown[1] + dy * ln * 0.50 - ln * 0.20)
        p2 = (crown[0] + dx * ln, crown[1] + dy * ln + ln * 0.46)
        fspine = quad(crown, p1, p2, n)
        fw = []
        for i in range(n + 1):
            t = i / n
            blade = 15.0 * (t ** 0.30) * ((1.0 - t) ** 0.80) * 2.55
            fw.append(max(0.7, blade * (1.0 + 0.07 * math.sin(t * 46.0))))
        draw.polygon(taper(fspine, fw), fill=PALM)


def layer(canvas: Image.Image, paint) -> Image.Image:
    """Draw translucent art on its own layer, then composite it down."""
    lay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    paint(ImageDraw.Draw(lay))
    return Image.alpha_composite(canvas, lay)


def tracked(draw, text, font, tracking, fill, centre_x, baseline_y):
    """Letter-spaced text, centred on its own advance width."""
    adv = [font.getlength(c) for c in text]
    total = sum(adv) + tracking * (len(text) - 1)
    x = centre_x - total / 2.0
    for c, a in zip(text, adv):
        draw.text((x, baseline_y), c, font=font, fill=fill, anchor="ls")
        x += a + tracking


def fit_size(texts, start, stroke_extra, limit):
    """Largest size at which every text fits inside `limit` px (all in drawing units)."""
    size = start
    while size > 40:
        f = load_font(size)
        if all(f.getlength(t) + stroke_extra <= limit for t in texts):
            return size
        size -= 2
    return size


# --- the picture -----------------------------------------------------------
def build() -> Image.Image:
    sky = sky_image()
    canvas = sky.copy().convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # sun: drawn before the skyline, with five sky-coloured bands cut out of its lower half
    cx, cy, r = 600, 760, 210
    draw.ellipse(
        [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=SUN
    )
    band_mask = Image.new("L", canvas.size, 0)
    bm = ImageDraw.Draw(band_mask)
    for i in range(5):
        y0 = cy + 20 + i * 26
        bm.rectangle([0, y0 * S, W, (y0 + 8) * S], fill=255)
    circle_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(circle_mask).ellipse(
        [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=255
    )
    band_mask = ImageChops.multiply(band_mask, circle_mask)
    canvas.paste(sky, (0, 0), band_mask)
    draw = ImageDraw.Draw(canvas)

    # distant skyline: fourteen varied buildings sitting on the horizon
    buildings = (
        (-12, 104, 96), (88, 66, 168), (150, 122, 78), (266, 62, 190),
        (322, 96, 118), (412, 74, 62), (480, 132, 152), (606, 84, 100),
        (684, 60, 186), (740, 118, 88), (852, 72, 140), (918, 128, 108),
        (1040, 62, 172), (1096, 116, 92),
    )
    wins = []
    for i, (bx, bw, bh) in enumerate(buildings):
        draw.rectangle([bx * S, (HORIZON - bh) * S, (bx + bw) * S, HORIZON * S], fill=SKYLINE)
        count = 2 + i % 3
        for k in range(count):
            ww, wh = 7, 11
            wx = bx + 8 + ((k * 37 + i * 11) % max(1, bw - ww - 12))
            wy = HORIZON - bh + 12 + ((k * 29 + i * 7) % max(1, bh - 26))
            wins.append((wx, wy, ww, wh))

    def paint_windows(d):
        for wx, wy, ww, wh in wins:
            d.rectangle([wx * S, wy * S, (wx + ww) * S, (wy + wh) * S], fill=WINDOW + (102,))

    canvas = layer(canvas, paint_windows)

    # ground
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, GROUND_TOP * S, W, W], fill=GROUND)

    # palms behind everything else that matters
    palm(draw, 120, -34)
    palm(draw, 1060, 34)

    # caption: one size for both lines, shrunk only if the stroke would cross
    # x=90..1110
    big = fit_size(("13 YEARS.", "STILL 99%."), 168, 2 * 14 * S, 1020 * S)
    f_small = load_font(44)
    f_big = load_font(big)

    # small letterspaced line above the joke; lifted a touch so the big line's
    # 14 px stroke does not bite into its baseline
    ascent, descent = f_small.getmetrics()
    tracked(draw, "GRAND THEFT AUTO VI", f_small, 10 * S, LILAC,
            600 * S, 272 * S + (ascent - descent) / 2.0)

    stroke = 14 * S

    def shadow(d):
        d.text((600 * S + 6 * S, 430 * S + 6 * S), "13 YEARS.", font=f_big, fill=(0, 0, 0, 140), anchor="ms")
        d.text((600 * S + 6 * S, 600 * S + 6 * S), "STILL 99%.", font=f_big, fill=(0, 0, 0, 140), anchor="ms")

    canvas = layer(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    draw.text((600 * S, 430 * S), "13 YEARS.", font=f_big, fill=WHITE,
              anchor="ms", stroke_width=stroke, stroke_fill=INK)
    draw.text((600 * S, 600 * S), "STILL 99%.", font=f_big, fill=WHITE,
              anchor="ms", stroke_width=stroke, stroke_fill=INK)

    # overprint "99%": the glyphs themselves act as the mask, so the pink can
    # never thicken the letterform or bleed into the stroke
    line2 = "STILL 99%."
    prefix = "STILL "
    left = 600 * S - f_big.getlength(line2) / 2.0
    glyph = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(glyph).text(
        (left + f_big.getlength(prefix), 600 * S), "99%", font=f_big, fill=255, anchor="ls"
    )
    canvas.paste(Image.new("RGBA", canvas.size, HOT_PINK + (255,)), (0, 0), glyph)

    # loading bar, honestly stuck at 99%
    def paint_bar(d):
        d.rounded_rectangle([170 * S, 900 * S, 1030 * S, 966 * S], radius=33 * S, fill=BAR_TROUGH)
        d.rounded_rectangle([178 * S, 908 * S, 1000 * S, 958 * S], radius=27 * S, fill=BAR_FILL)
        d.rounded_rectangle([170 * S, 900 * S, 1030 * S, 966 * S], radius=33 * S,
                            outline=WHITE + (229,), width=6 * S)

    canvas = layer(canvas, paint_bar)

    # make.fun's ghost, sitting on the bar: a soft contact shadow built as a
    # nested falloff mask (PIL does not accumulate alpha between draws, so the
    # outer ellipse must deliberately hold the faintest value)
    shadow = Image.new("L", canvas.size, 0)
    sd = ImageDraw.Draw(shadow)
    for i in range(8):
        t = i / 7.0
        wdt = 200.0 - 74.0 * t
        hgt = 34.0 - 18.0 * t
        sd.ellipse(
            [(900 - wdt / 2) * S, (906 - hgt / 2) * S, (900 + wdt / 2) * S, (906 + hgt / 2) * S],
            fill=int(round(255 * 0.34 * (0.22 + 0.78 * t))),
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(5 * S))
    canvas = Image.composite(Image.new("RGBA", canvas.size, (0, 0, 0, 255)), canvas, shadow)

    # the press mark carries ~7 px of transparent padding inside its 1024 box, so
    # the paste box stops short of the bar: the disc's lowest pixels land 17 px
    # onto the white outline, which is what makes it read as sitting, not hovering
    mark = Image.open(MARK).convert("RGBA").resize((190 * S, 190 * S), Image.LANCZOS)
    canvas.alpha_composite(mark, (805 * S, 734 * S))

    # footer
    draw = ImageDraw.Draw(canvas)
    f_foot = load_font(40)
    draw.text((600 * S, 1120 * S), "make.fun \u00b7 your agent earns while you wait",
              font=f_foot, fill=FOOT + (235,), anchor="mm")

    return canvas.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    img = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    with open(OUT, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print(f"meme/meme.png {img.size[0]}x{img.size[1]} {os.path.getsize(OUT)} bytes sha256={digest}")


if __name__ == "__main__":
    main()
