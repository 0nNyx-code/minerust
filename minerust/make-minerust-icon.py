#!/usr/bin/env python3
"""Draw the Minerust launcher icon (flat, vector-like) with Pillow.

Output: 1024px master plus the 512px drawable the APK ships.
Everything is drawn at 4x and downsampled, so edges stay clean.
"""

import sys
from PIL import Image, ImageDraw, ImageFilter

S = 4                      # supersample factor
N = 1024 * S               # working canvas


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return m


def gradient(size, c0, c1, diagonal=True):
    g = Image.new("RGB", (size, size))
    px = g.load()
    for y in range(size):
        for x in range(0, size, 8):
            t = ((x + y) / (2 * size)) if diagonal else (y / size)
            col = lerp(c0, c1, t)
            for k in range(8):
                px[x + k, y] = col
    return g


def m_polygon():
    """Chunky M with chiselled top edges, in 1024-space normalized coords."""
    pts = [
        (250, 762), (250, 344),           # left stem, outer bottom -> top
        (286, 310), (404, 310),           # chisel cut on the left shoulder
        (512, 470),                       # valley
        (620, 310), (738, 310), (774, 344),
        (774, 762), (652, 762),           # right stem
        (652, 548), (512, 700), (372, 548),
        (372, 762),
    ]
    return [(x * S, y * S) for x, y in pts]


def build(size=1024):
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))

    # --- tile -------------------------------------------------------------
    tile = gradient(N, (26, 26, 32), (9, 9, 13)).convert("RGBA")
    canvas.paste(tile, (0, 0), rounded_mask(N, round(N * 0.22)))

    # faint top sheen, clipped to the tile
    sheen = Image.new("L", (N, N), 0)
    sd = ImageDraw.Draw(sheen)
    for y in range(round(N * 0.42)):
        sd.line([(0, y), (N, y)],
                fill=round(14 * (1 - y / (N * 0.42)) ** 2))
    sheen = Image.composite(sheen, Image.new("L", (N, N), 0),
                            rounded_mask(N, round(N * 0.22)))
    canvas.paste(Image.new("RGBA", (N, N), (255, 255, 255, 255)), (0, 0), sheen)

    # --- horizon: glow + crisp line ---------------------------------------
    horizon_y = round(N * 0.626)
    glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        (N * 0.10, horizon_y - N * 0.020, N * 0.90, horizon_y + N * 0.020),
        radius=N * 0.02, fill=(255, 96, 48, 120))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(N * 0.022)))

    line = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(line).rounded_rectangle(
        (N * 0.11, horizon_y - N * 0.006, N * 0.89, horizon_y + N * 0.006),
        radius=N * 0.006, fill=(255, 122, 62, 235))
    canvas.alpha_composite(line)

    # --- monogram ---------------------------------------------------------
    poly = m_polygon()
    # soft dark outline so the mark separates from the horizon glow
    halo = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(halo).polygon(poly, fill=(8, 8, 11, 255))
    canvas.alpha_composite(halo.filter(ImageFilter.GaussianBlur(N * 0.012)))

    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    # a slightly inset mask leaves a dark rim inside the silhouette
    rim = Image.new("L", (N, N), 0)
    inset = N * 0.010
    d = ImageDraw.Draw(rim)
    d.polygon([(x, y) for x, y in poly], fill=255)
    d.line(poly + [poly[0]], fill=0, width=round(inset * 2), joint="curve")

    mark = gradient(N, (255, 62, 40), (255, 182, 74)).convert("RGBA")
    canvas.paste(mark, (0, 0), rim)

    return canvas.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "icon-1024.png"
    icon = build(1024)
    icon.save(out)
    icon.resize((512, 512), Image.LANCZOS).save(
        out.replace("1024", "512"))
    print("wrote", out)
