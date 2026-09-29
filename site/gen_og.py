#!/usr/bin/env python3
"""
Generate the Open Graph image for the BLACKHEART site.

Run:  python3 site/gen_og.py
Out:  site/og-image.png   (1200x630)

Open Graph and Twitter card previews do not render SVG reliably — most
platforms show a blank box. So the card is rendered as a real PNG.

The image is generated rather than hand-placed so it can be regenerated when
the palette, the mark, or the figures change, instead of becoming a stale
artefact nobody remembers the provenance of. Nothing is downloaded: the fonts
are the ones already on the machine, and the output is deterministic for a
given font set.

`og-image.svg` is the vector original of this same card. It is kept because it
is the lossless version and because the repository does not delete prior
material, but it is not the file social platforms are pointed at: a PNG is.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "og-image.png")

W, H = 1200, 630
BG = (7, 11, 17)
PANEL = (14, 21, 33)
LINE = (27, 38, 53)
INK = (232, 238, 247)
INK2 = (182, 196, 214)
MUTED = (125, 142, 165)
ACCENT = (0, 212, 165)
ACCENT2 = (77, 140, 255)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FONT_MONO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def pick(cands):
    for c in cands:
        if os.path.isfile(c):
            return c
    sys.exit("no usable font found; install fonts-dejavu-core")


def font(path, size):
    return ImageFont.truetype(pick(path), size)


def radial_glow(size, colour, centre, radius, strength=70):
    """A soft radial glow drawn on a transparent layer, then blurred."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = centre
    steps = 26
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(strength * (1 - t) ** 2.0)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (a,))
    return layer.filter(ImageFilter.GaussianBlur(radius * 0.18))


def apple_icon():
    """180x180 home-screen icon.

    iOS does not render SVG for the home-screen icon -- it ignores the link and
    falls back to a screenshot of the page. The PNG below is what actually
    gets used, so it is the one that has to be right.
    """
    out = os.path.join(HERE, "apple-touch-icon.png")
    S = 180
    im = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=0, fill=BG)
    cx, cy, R = S / 2, S / 2, S * 0.36
    import math
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
           for a in range(-90, 271, 60)]
    d.line(pts + [pts[0]], fill=ACCENT, width=11, joint="curve")
    d.line([(cx, cy - R * 0.44), (cx, cy + R * 0.44)], fill=ACCENT, width=11)
    d.line([(cx - R * 0.44, cy), (cx + R * 0.44, cy)], fill=ACCENT, width=11)
    im.save(out, "PNG", optimize=True)
    print(f"  {out}  {S}x{S}  {os.path.getsize(out):,} bytes")
    return out


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")

    # ambient glows
    img = Image.alpha_composite(
        img.convert("RGBA"),
        radial_glow((W, H), ACCENT, (140, 110), 520, 62),
    )
    img = Image.alpha_composite(
        img,
        radial_glow((W, H), ACCENT2, (1080, 300), 460, 46),
    )
    d = ImageDraw.Draw(img, "RGBA")

    # faint grid
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=LINE + (70,), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=LINE + (70,), width=1)

    # hex mark
    cx, cy, R = 150, 210, 62
    pts = [(cx + R * 0.866 * __import__("math").cos(__import__("math").radians(a)),
            cy + R * 0.866 * __import__("math").sin(__import__("math").radians(a)))
           for a in range(-90, 271, 60)]
    d.polygon(pts, outline=None, fill=(0, 0, 0, 0))
    d.line(pts + [pts[0]], fill=ACCENT + (255,), width=7, joint="curve")
    d.line([(cx, cy - 26), (cx, cy + 26)], fill=ACCENT + (255,), width=7)
    d.line([(cx - 26, cy), (cx + 26, cy)], fill=ACCENT + (255,), width=7)

    # wordmark
    d.text((248, 168), "BLACKHEART", font=font(FONT_CANDIDATES, 78), fill=INK)
    d.text((252, 262), "A governed security-supply-chain",
           font=font(FONT_REGULAR, 33), fill=INK2)
    d.text((252, 304), "framework for AI agents",
           font=font(FONT_REGULAR, 33), fill=INK2)

    # rule
    d.line([(96, 392), (1104, 392)], fill=LINE + (255,), width=2)

    # tagline
    d.text((96, 424), "Unvetted skills are the vulnerability.",
           font=font(FONT_CANDIDATES, 30), fill=ACCENT)

    # figures
    y = 500
    items = [("3,864", "files verified"),
             ("399", "reviewed adapters"),
             ("19", "audit groups"),
             ("0", "broken authored links")]
    x = 96
    for value, label in items:
        d.text((x, y), value, font=font(FONT_CANDIDATES, 44), fill=ACCENT)
        d.text((x, y + 52), label, font=font(FONT_REGULAR, 20), fill=MUTED)
        x += 250

    d.text((96, 592), "devara1983ntr.github.io/blackheart-security-framework",
           font=font(FONT_MONO, 17), fill=(100, 118, 140))

    img.convert("RGB").save(OUT, "PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"  {OUT}  {img.width}x{img.height}  {size:,} bytes")
    if size > 300_000:
        print("  WARNING: over 300 KB; most platforms downscale anyway")
    apple_icon()


if __name__ == "__main__":
    main()
