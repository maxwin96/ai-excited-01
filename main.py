#!/usr/bin/env python3
"""The Whale Learned to Fly -- make.fun ai-excited-01 entry.

A single 1024x1024 picture drawn from scratch with the Python 3 standard
library only. No image file is loaded and no third-party package is used:
every pixel is computed in this file and the PNG bytes are encoded here
with zlib + struct. The drawing is fully deterministic, so two runs
produce byte-identical output.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
OUT = "/output/entry.png"

# Pixel buffer, row-major RGB.
buf = bytearray(W * H * 3)

HORIZON = 625  # y where the sea meets the city skyline


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def put(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = rgb[0]
        buf[i + 1] = rgb[1]
        buf[i + 2] = rgb[2]


def hline(x0, x1, y, rgb):
    if y < 0 or y >= H:
        return
    x0 = _clamp(x0, 0, W - 1)
    x1 = _clamp(x1, 0, W - 1)
    if x1 < x0:
        return
    n = x1 - x0 + 1
    i = (y * W + x0) * 3
    buf[i:i + n * 3] = bytes(rgb) * n


def fill_rect(x, y, w, h, rgb):
    for yy in range(y, y + h):
        hline(x, x + w - 1, yy, rgb)


def lerp(a, b, t):
    return int(a + (b - a) * t + 0.5)


def mix(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t),
            lerp(c1[2], c2[2], t))


def disc(cx, cy, r, rgb):
    """Filled circle."""
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        rem = r2 - dy * dy
        if rem < 0:
            continue
        dx = int(math.sqrt(rem))
        hline(cx - dx, cx + dx, y, rgb)


def ring(cx, cy, r0, r1, rgb):
    """Filled annulus between radii r0 and r1."""
    for y in range(cy - r1, cy + r1 + 1):
        dy = y - cy
        o2 = r1 * r1 - dy * dy
        if o2 < 0:
            continue
        ox = int(math.sqrt(o2))
        i2 = r0 * r0 - dy * dy
        if i2 <= 0:
            hline(cx - ox, cx + ox, y, rgb)
        else:
            ix = int(math.sqrt(i2))
            hline(cx - ox, cx - ix - 1, y, rgb)
            hline(cx + ix + 1, cx + ox, y, rgb)


def ellipse_rot(cx, cy, a, b, ang_deg, rgb):
    """Filled ellipse with semi-axes a, b rotated by ang_deg degrees."""
    th = math.radians(ang_deg)
    c = math.cos(th)
    s = math.sin(th)
    span = int(a + b) + 2
    for y in range(cy - span, cy + span + 1):
        dy = y - cy
        A = (c * c) / (a * a) + (s * s) / (b * b)
        B = 2 * dy * (c * s / (a * a) - s * c / (b * b))
        Cc = dy * dy * (s * s / (a * a) + c * c / (b * b)) - 1
        discr = B * B - 4 * A * Cc
        if discr < 0:
            continue
        sq = math.sqrt(discr)
        x0 = int((-B - sq) / (2 * A)) + cx
        x1 = int((-B + sq) / (2 * A)) + cx
        hline(x0, x1, y, rgb)


def polygon(pts, rgb):
    """Filled polygon given as a list of (x, y) vertices."""
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            hline(int(xs[k]), int(xs[k + 1]), y, rgb)


def line(x0, y0, x1, y1, rgb):
    """Bresenham line."""
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(x0, y0, rgb)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def hash2(i, j):
    """Small deterministic integer hash, used instead of random."""
    v = (i * 2654435761 + j * 40503) & 0xFFFFFFFF
    v ^= v >> 13
    v = (v * 2246822519) & 0xFFFFFFFF
    v ^= v >> 16
    return v


# ---------------------------------------------------------------- sky

def draw_sky():
    stops = [
        (0.00, (26, 18, 66)),
        (0.45, (110, 52, 128)),
        (0.75, (216, 84, 72)),
        (1.00, (255, 132, 52)),
    ]
    for y in range(HORIZON):
        t = y / HORIZON
        for k in range(len(stops) - 1):
            t0, c0 = stops[k]
            t1, c1 = stops[k + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                hline(0, W - 1, y, mix(c0, c1, f))
                break
    # Early stars high up, where the sky is darkest.
    for i in range(90):
        x = (i * 911 + 37) % W
        y = (i * 373 + 11) % 250
        b = 150 + (i % 3) * 40
        put(x, y, (b, b, min(255, b + 30)))
        if i % 4 == 0:
            put(x + 1, y, (b, b, min(255, b + 30)))


def draw_sun():
    cx, cy = 690, 470
    disc(cx, cy, 150, (255, 112, 58))
    disc(cx, cy, 122, (255, 152, 72))
    disc(cx, cy, 96, (255, 192, 92))
    disc(cx, cy, 70, (255, 236, 172))
    disc(cx, cy, 58, (255, 248, 214))


def cloud(cx, cy, s, rgb):
    disc(cx, cy, int(46 * s), rgb)
    disc(cx - int(52 * s), cy + int(8 * s), int(34 * s), rgb)
    disc(cx + int(54 * s), cy + int(10 * s), int(36 * s), rgb)
    disc(cx + int(8 * s), cy - int(16 * s), int(30 * s), rgb)


def draw_clouds():
    cloud(190, 150, 1.0, (255, 150, 118))
    cloud(430, 105, 0.8, (236, 110, 132))
    cloud(830, 180, 0.9, (255, 158, 122))
    cloud(120, 320, 0.7, (214, 96, 128))
    cloud(880, 330, 0.6, (240, 120, 110))


# ---------------------------------------------------------------- city

CITY = (14, 11, 28)
WIN_LIT = (255, 196, 92)
WIN_DIM = (150, 110, 60)


def draw_city():
    x = 0
    i = 0
    while x < W:
        wdt = 46 + hash2(i, 1) % 50
        hgt = 55 + hash2(i, 2) % 95
        top = HORIZON - hgt
        fill_rect(x, top, wdt, hgt, CITY)
        if hash2(i, 3) % 3 == 0:  # rooftop antenna on some towers
            fill_rect(x + wdt // 2 - 1, top - 22, 3, 22, CITY)
            put(x + wdt // 2, top - 24, (255, 90, 70))
        for wy in range(top + 12, HORIZON - 6, 16):
            for wx in range(x + 7, x + wdt - 7, 14):
                r = hash2(wx, wy) % 5
                if r == 0:
                    fill_rect(wx, wy, 5, 7, WIN_LIT)
                elif r == 1:
                    fill_rect(wx, wy, 5, 7, WIN_DIM)
        x += wdt + 4
        i += 1


# ---------------------------------------------------------------- sea

FOAM = (226, 240, 246)
FOAM_DIM = (150, 190, 210)


def draw_sea():
    stops = [
        (0.00, (26, 74, 122)),
        (0.50, (16, 48, 92)),
        (1.00, (6, 20, 48)),
    ]
    depth = H - HORIZON
    for y in range(HORIZON, H):
        t = (y - HORIZON) / depth
        for k in range(len(stops) - 1):
            t0, c0 = stops[k]
            t1, c1 = stops[k + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                hline(0, W - 1, y, mix(c0, c1, f))
                break


def wave(y0, amp, k, ph, rgb, thick):
    for x in range(W):
        y = int(y0 + amp * math.sin(x * k + ph))
        for t in range(thick):
            put(x, y + t, rgb)


def draw_waves():
    wave(700, 14, 0.018, 0.4, FOAM_DIM, 3)
    wave(782, 17, 0.014, 2.1, FOAM, 3)
    wave(864, 12, 0.021, 4.4, FOAM_DIM, 3)
    wave(946, 16, 0.012, 1.2, FOAM, 4)
    wave(660, 8, 0.03, 0.9, FOAM, 2)


def draw_splash():
    # Foam rings where the whale bursts out of the water.
    ring(255, 645, 96, 112, FOAM)
    ring(255, 645, 122, 130, FOAM_DIM)
    ring(255, 645, 70, 80, FOAM)
    drops = [
        (178, 602, 10), (212, 566, 8), (262, 556, 12), (302, 582, 9),
        (332, 622, 7), (158, 652, 9), (228, 692, 8), (292, 662, 10),
        (352, 664, 6), (196, 716, 7), (330, 700, 8), (120, 610, 6),
        (380, 620, 5), (250, 520, 6), (300, 528, 5),
    ]
    for (dx, dy, r) in drops:
        disc(dx, dy, r, FOAM)


# ---------------------------------------------------------------- whale

WHALE = (64, 108, 168)
WHALE_DARK = (44, 82, 138)
BELLY = (150, 192, 226)
EYE = (10, 20, 40)


def draw_whale():
    # Body: long ellipse tilted so the head rises to the upper right
    # and the tail stays down in the waves at the lower left.
    ellipse_rot(505, 445, 320, 108, -36, WHALE)
    # Paler belly along the underside.
    ellipse_rot(526, 473, 258, 60, -36, BELLY)
    # Dorsal fin on the upper edge.
    polygon([(398, 332), (472, 298), (442, 348)], WHALE_DARK)
    # Pectoral fin tucked under the body.
    polygon([(548, 506), (628, 548), (566, 552)], WHALE_DARK)
    # Tail flukes fanning out from the tail stock.
    polygon([(250, 630), (138, 544), (186, 656)], WHALE)
    polygon([(250, 630), (148, 702), (202, 652)], WHALE)
    # Eye near the head, with a small glint.
    disc(696, 296, 8, EYE)
    disc(698, 294, 3, (255, 255, 255))
    # A gentle smiling mouth line under the head.
    px, py = None, None
    for k in range(13):
        t = k / 12.0
        mx = int(648 + t * 96)
        my = int(348 + 16 * math.sin(t * 1.4) - t * 34)
        if px is not None:
            line(px, py, mx, my, WHALE_DARK)
        px, py = mx, my


# ---------------------------------------------------------------- astronaut

SUIT = (238, 238, 240)
VISOR = (30, 44, 66)


def draw_astronaut():
    # A tiny astronaut riding on the whale's back, upright.
    ax, ay = 446, 364
    line(ax, ay + 26, ax, ay + 34, SUIT)          # tether to the whale
    disc(ax, ay, 11, SUIT)                        # helmet
    disc(ax + 2, ay, 7, VISOR)                    # visor
    fill_rect(ax - 8, ay + 11, 16, 20, SUIT)      # torso
    fill_rect(ax - 12, ay + 12, 4, 12, SUIT)      # backpack
    fill_rect(ax - 7, ay + 31, 5, 12, SUIT)       # left leg
    fill_rect(ax + 2, ay + 31, 5, 12, SUIT)       # right leg
    fill_rect(ax - 13, ay + 14, 5, 10, SUIT)      # left arm
    fill_rect(ax + 8, ay + 14, 5, 10, SUIT)       # right arm
    put(ax - 2, ay + 42, (200, 60, 50))           # boot tip


# ---------------------------------------------------------------- text

# 5x7 bitmap glyphs, drawn by hand for the letters this picture needs.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00100", "01000"),
}


def draw_text(s, x, y, scale, rgb):
    cx = x
    for ch in s:
        g = GLYPHS.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    fill_rect(cx + c * scale, y + r * scale,
                              scale, scale, rgb)
        cx += 6 * scale


def draw_titles():
    shadow = (24, 12, 44)
    ink = (255, 244, 214)
    draw_text("THE WHALE", 74, 68, 7, shadow)
    draw_text("THE WHALE", 70, 64, 7, ink)
    draw_text("LEARNED TO FLY", 74, 124, 7, shadow)
    draw_text("LEARNED TO FLY", 70, 120, 7, ink)
    draw_text("HOLD ON, JUDGE.", 74, 944, 5, shadow)
    draw_text("HOLD ON, JUDGE.", 70, 940, 5, ink)


# ---------------------------------------------------------------- png out

def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def save_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("wrote", OUT, len(data), "bytes")


def main():
    draw_sky()
    draw_sun()
    draw_clouds()
    draw_city()
    draw_sea()
    draw_waves()
    draw_splash()
    draw_whale()
    draw_astronaut()
    draw_titles()
    save_png()


if __name__ == "__main__":
    main()
