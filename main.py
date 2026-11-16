#!/usr/bin/env python3
"""The Whale Learned to Fly — ai-excited-01 entry.

Renders a single 1024x1024 scene from scratch with Python 3 stdlib only
(the PNG encoder is hand-written with zlib + struct). Fully deterministic:
no random, no time, no input — two runs produce byte-identical output.

Scene: sunset sky over a sea, a dark city silhouette on the horizon, a giant
blue whale breaching diagonally out of the waves, a tiny astronaut in a white
suit riding on the whale's back, and hand-drawn bitmap text.
"""

import os
import struct
import zlib

W = 1024
H = 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- image core

img = bytearray(W * H * 3)


def _idx(x, y):
    return (y * W + x) * 3


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = _idx(x, y)
        img[i] = r
        img[i + 1] = g
        img[i + 2] = b


def blend(x, y, r, g, b, a):
    """Blend color over the pixel at (x, y); a in 0..1."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = _idx(x, y)
        if a >= 1.0:
            img[i] = r
            img[i + 1] = g
            img[i + 2] = b
        else:
            img[i] = int(img[i] * (1.0 - a) + r * a)
            img[i + 1] = int(img[i + 1] * (1.0 - a) + g * a)
            img[i + 2] = int(img[i + 2] * (1.0 - a) + b * a)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def fill_row(y, color):
    """Fill a whole horizontal row with one color (fast slice fill)."""
    if 0 <= y < H:
        row = bytes(color) * W
        img[y * W * 3:(y + 1) * W * 3] = row


def fill_rect(x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        img[y * W * 3 + x0 * 3:y * W * 3 + x1 * 3] = row


def disc(cx, cy, r, color, alpha=1.0):
    """Filled circle, optionally translucent."""
    r2 = r * r
    for y in range(int(cy - r), int(cy + r) + 1):
        dy = y - cy
        dx = int((r2 - dy * dy) ** 0.5) if r2 - dy * dy >= 0 else 0
        for x in range(int(cx - dx), int(cx + dx) + 1):
            blend(x, y, color[0], color[1], color[2], alpha)


def ellipse(cx, cy, rx, ry, color, alpha=1.0):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem < 0:
            continue
        dx = int(rx * rem ** 0.5)
        for x in range(int(cx - dx), int(cx + dx) + 1):
            blend(x, y, color[0], color[1], color[2], alpha)


def poly(points, color, alpha=1.0):
    """Scanline fill of a simple polygon."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = int(min(ys)), int(max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                blend(x, y, color[0], color[1], color[2], alpha)


def thick_line(x0, y0, x1, y1, w, color, alpha=1.0):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for s in range(steps + 1):
        t = s / steps
        disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w / 2.0, color, alpha)


# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, designed here from scratch. Only the letters the text needs.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00001", "00001", "00001", "00001", "10001", "01110"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "W": ("10001", "10001", "10001", "10001", "10101", "10101", "01010"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_text(text, cx, y, scale, color, shadow=None):
    """Draw text centered on cx, top edge at y."""
    cell = 6 * scale  # 5 px glyph + 1 px gap
    total = len(text) * cell - scale
    x = cx - total // 2
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    bx = x + gx * scale
                    by = y + gy * scale
                    if shadow is not None:
                        fill_rect(bx + 2, by + 2, bx + scale, by + scale,
                                  shadow)
                    fill_rect(bx, by, bx + scale, by + scale, color)
        x += cell


# ---------------------------------------------------------------- scene

def sky():
    # Gradient stops: deep indigo top -> violet -> magenta -> blazing orange
    # at the horizon (y = 640).
    stops = [
        (0, (24, 16, 68)),
        (220, (74, 32, 108)),
        (400, (150, 52, 110)),
        (520, (226, 92, 62)),
        (640, (255, 158, 52)),
    ]
    for y in range(0, 641):
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= y <= y1:
                t = (y - y0) / max(1, y1 - y0)
                fill_row(y, lerp_color(c0, c1, t))
                break
    # Deterministic stars in the upper sky.
    for i in range(160):
        x = (i * 7919 + 131) % W
        y = (i * 104729 + 57) % 210
        s = (i * 31) % 3
        col = (255, 240, 200) if s == 0 else (220, 220, 255)
        put(x, y, *col)
        if s == 0:
            put(x + 1, y, *col)


def sun():
    cx, cy, r = 300, 598, 74
    # Wide glow: concentric soft discs.
    for rr, a in ((260, 0.10), (200, 0.16), (150, 0.24), (110, 0.34)):
        disc(cx, cy, rr, (255, 150, 60), a)
    disc(cx, cy, r, (255, 214, 110))
    disc(cx, cy, r - 14, (255, 236, 170))
    disc(cx, cy, r - 34, (255, 248, 214))
    # Sun rays: short spokes fading outward.
    for k in range(12):
        ang = k * 30.0 * 3.14159265 / 180.0
        import math
        x0 = cx + math.cos(ang) * (r + 6)
        y0 = cy + math.sin(ang) * (r + 6)
        x1 = cx + math.cos(ang) * (r + 34)
        y1 = cy + math.sin(ang) * (r + 34)
        thick_line(x0, y0, x1, y1, 5, (255, 190, 90), 0.75)


def clouds():
    import math
    # A few soft, rounded sunset clouds, brighter underneath.
    puffs = [
        (180, 210, 95, 30, (255, 150, 110)),
        (330, 190, 80, 24, (255, 170, 130)),
        (830, 250, 105, 32, (255, 140, 100)),
        (700, 300, 75, 22, (255, 175, 135)),
        (120, 330, 70, 20, (240, 120, 120)),
        (920, 140, 85, 24, (210, 110, 150)),
    ]
    for (cx, cy, rx, ry, col) in puffs:
        ellipse(cx, cy, rx, ry, col, 0.42)
        ellipse(cx, cy + 6, rx - 22, ry - 6, (255, 205, 150), 0.38)
    # Thin high streaks.
    for k in range(5):
        y = 90 + k * 26
        x0 = (k * 173 + 60) % 700
        thick_line(x0, y, x0 + 190, y - 8, 3, (255, 190, 170), 0.45)


def ocean():
    # Deep blue at the horizon lightening toward teal in the foreground,
    # with a warm sun-path reflection under the sun.
    for y in range(640, H):
        t = (y - 640) / (H - 640)
        base = lerp_color((28, 66, 118), (10, 42, 84), t)
        fill_row(y, base)
    # Sun reflection: shimmering vertical band below the sun.
    import math
    for y in range(648, H):
        t = (y - 648) / (H - 648)
        half = 26 + t * 150
        for x in range(int(300 - half), int(300 + half) + 1):
            wob = math.sin(x * 0.11 + y * 0.23) * 0.5 + 0.5
            a = (0.55 - 0.35 * t) * wob * (1.0 - abs(x - 300) / half)
            if a > 0.02:
                blend(x, y, 255, 170, 80, a)
    # Rolling wave crests: sine lines with white foam.
    for band in range(9):
        yb = 690 + band * 38
        amp = 7 + band * 2
        for x in range(0, W, 2):
            yy = int(yb + math.sin(x * 0.018 + band * 1.7) * amp)
            a = 0.5 - band * 0.04
            for dy in range(3):
                blend(x, yy + dy, 200, 230, 245, a * (1.0 - dy / 3.0))
                blend(x + 1, yy + dy, 200, 230, 245, a * (1.0 - dy / 3.0))


def city():
    # Dark skyline along the horizon, windows glowing warm.
    import math
    x = -10
    b = 0
    while x < W + 10:
        bw = 34 + ((b * 37) % 46)
        bh = 42 + ((b * 53) % 78)
        top = 640 - bh
        fill_rect(x, top, x + bw, 642, (16, 14, 38))
        # Rooftop antenna on some towers.
        if b % 3 == 0:
            fill_rect(x + bw // 2 - 1, top - 16, x + bw // 2 + 1, top,
                      (16, 14, 38))
            put(x + bw // 2, top - 18, 255, 90, 70)
        # Lit windows: deterministic pattern.
        for wy in range(top + 8, 636, 16):
            for wx in range(x + 6, x + bw - 6, 13):
                h = (wx * 7 + wy * 13 + b * 29) % 10
                if h < 4:
                    col = (255, 196, 90) if h < 2 else (140, 220, 255)
                    fill_rect(wx, wy, wx + 5, wy + 7, col)
        x += bw + 6
        b += 1


def whale_spine(t):
    """Spine point at parameter t: 0 = tail tip, 1 = head tip."""
    import math
    x = 218 + 560 * t
    y = 905 - 545 * t + 62 * math.sin(math.pi * t)
    return x, y


def whale_radius(t):
    # Slim tail stock, fat belly, tapered rounded head.
    if t < 0.18:
        return 26 + t * 260
    if t < 0.62:
        return 73 + (t - 0.18) * 70
    return 104 - (t - 0.62) * 130


def whale():
    import math
    # --- tail flukes (behind the body) ---
    tx, ty = whale_spine(0.02)
    fluke = (42, 78, 128)
    poly([(tx, ty), (tx - 118, ty + 96), (tx - 52, ty + 34)], fluke)
    poly([(tx, ty), (tx - 96, ty - 118), (tx - 44, ty - 40)], fluke)
    poly([(tx, ty), (tx - 118, ty + 96), (tx - 52, ty + 34)],
         (28, 58, 104), 0.5)
    # --- body: overlapping discs along the spine ---
    steps = 90
    for i in range(steps + 1):
        t = i / steps
        cx, cy = whale_spine(t)
        r = whale_radius(t)
        # Back is deep blue, belly side paler: paint two offset discs.
        disc(cx, cy, r, (38, 96, 152))
        disc(cx + 4, cy + r * 0.42, r * 0.62, (96, 158, 205), 0.6)
    # Dorsal shading: darker cap along the upper edge.
    for i in range(steps + 1):
        t = i / steps
        cx, cy = whale_spine(t)
        r = whale_radius(t)
        disc(cx - 4, cy - r * 0.42, r * 0.62, (22, 66, 118), 0.55)
    # --- pectoral fin ---
    mx, my = whale_spine(0.52)
    poly([(mx, my + 20), (mx - 30, my + 150), (mx + 46, my + 96)],
         (26, 72, 122))
    # --- head details ---
    hx, hy = whale_spine(0.97)
    # Eye with glint.
    disc(hx - 8, hy - 22, 9, (8, 14, 30))
    disc(hx - 11, hy - 25, 3, (255, 255, 255))
    # Smile / mouth line.
    for k in range(26):
        tt = k / 25.0
        px = hx - 58 + tt * 74
        py = hy + 26 + math.sin(tt * 1.2) * 8 - tt * 10
        disc(px, py, 3, (16, 48, 92))
    # Blowhole spray above the head.
    for k in range(14):
        ang = -90 + (k - 7) * 9
        rad = 26 + (k % 4) * 16
        a = math.radians(ang)
        disc(hx + math.cos(a) * rad, hy - 66 + math.sin(a) * rad * 0.7,
             4 + (k % 3), (235, 245, 255), 0.9)


def splash():
    import math
    # Burst of foam where the tail leaves the water.
    tx, ty = whale_spine(0.03)
    for k in range(60):
        ang = math.radians(-140 + (k * 37 % 200))
        dist = 40 + (k * 53 % 130)
        x = tx + math.cos(ang) * dist
        y = ty + math.sin(ang) * dist * 0.7
        r = 3 + (k * 7 % 9)
        disc(x, y, r, (240, 248, 255), 0.9)
    # Foam ring hugging the waterline around the breach.
    for x in range(170, 400, 8):
        yy = 912 + math.sin(x * 0.05) * 8
        disc(x, yy, 5, (235, 245, 255), 0.7)
        disc(x + 3, yy + 7, 4, (220, 238, 250), 0.55)
    # Droplets arcing off the whale's back.
    for k in range(26):
        t = k / 25.0
        bx, by = whale_spine(0.35 + t * 0.45)
        disc(bx - 30 + (k * 11 % 40), by - 96 - (k * 13 % 46),
             3 + (k % 3), (240, 248, 255), 0.9)


def astronaut():
    # Tiny white-suited astronaut riding the whale's back, one arm waving.
    # Back surface near t=0.66 sits around (585, 505); feet planted there.
    hx, hy = 588, 452          # helmet centre
    # Backpack.
    fill_rect(596, 462, 610, 492, (210, 214, 220))
    fill_rect(596, 462, 610, 470, (255, 120, 60))
    # Legs and boots.
    fill_rect(578, 486, 586, 508, (235, 238, 242))
    fill_rect(590, 486, 598, 508, (235, 238, 242))
    fill_rect(576, 505, 588, 511, (200, 60, 50))
    fill_rect(588, 505, 600, 511, (200, 60, 50))
    # Torso.
    fill_rect(576, 462, 600, 490, (240, 243, 246))
    fill_rect(582, 470, 594, 480, (40, 90, 140))
    # Left arm down, right arm raised waving.
    thick_line(578, 468, 566, 488, 7, (240, 243, 246))
    thick_line(598, 466, 616, 442, 7, (240, 243, 246))
    disc(618, 438, 5, (240, 243, 246))
    # Helmet: white shell, dark visor, glint.
    disc(hx, hy, 17, (245, 247, 250))
    disc(hx, hy, 13, (18, 26, 44))
    disc(hx - 4, hy - 4, 4, (150, 210, 255))
    # Tethers trailing behind in the wind.
    thick_line(600, 490, 636, 470, 2, (255, 255, 255), 0.8)
    thick_line(600, 494, 630, 486, 2, (255, 255, 255), 0.8)


def titles():
    draw_text("THE WHALE", 512, 48, 6, (255, 243, 214), shadow=(30, 10, 60))
    draw_text("LEARNED TO FLY", 512, 106, 6, (255, 214, 130),
              shadow=(30, 10, 60))
    draw_text("HOLD ON, JUDGE.", 512, 952, 3, (255, 255, 255),
              shadow=(10, 20, 50))


# ---------------------------------------------------------------- PNG encoder

def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += img[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def main():
    sky()
    sun()
    clouds()
    ocean()
    city()
    splash()
    whale()
    splash()
    astronaut()
    titles()
    write_png(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
