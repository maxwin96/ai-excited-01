#!/usr/bin/env python3
"""
ai-excited-01 — "The Whale Learned to Fly"

A 1024x1024 sunset scene drawn entirely from scratch with the Python 3
standard library only (the PNG encoder is handwritten with zlib + struct).

Scene: a giant blue whale breaches diagonally out of a foaming ocean in
front of a coastal city skyline at sunset, a tiny astronaut in a white
suit riding on its back, under the words THE WHALE / LEARNED TO FLY /
HOLD ON, JUDGE.  The letters are drawn with a small 5x7 bitmap font
designed here from scratch.

Fully deterministic: no randomness, no clock, no external assets.
Two runs produce byte-identical output.

Run:  python3 main.py        -> writes /output/entry.png
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
OUT = "/output/entry.png"

img = bytearray(W * H * 3)


# ------------------------------------------------------------------ pixels

def _i(x, y):
    return (y * W + x) * 3


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = _i(x, y)
        img[i] = c[0]
        img[i + 1] = c[1]
        img[i + 2] = c[2]


def blend_px(x, y, c, a):
    """Blend colour c over the current pixel with opacity a (0..1)."""
    if 0 <= x < W and 0 <= y < H:
        i = _i(x, y)
        img[i] = int(img[i] + (c[0] - img[i]) * a)
        img[i + 1] = int(img[i + 1] + (c[1] - img[i + 1]) * a)
        img[i + 2] = int(img[i + 2] + (c[2] - img[i + 2]) * a)


def hspan(x0, x1, y, c):
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W, int(x1))
    if x1 <= x0:
        return
    i = _i(x0, y)
    img[i:i + 3 * (x1 - x0)] = bytes(c) * (x1 - x0)


def blend_span(x0, x1, y, c, a):
    for x in range(max(0, int(x0)), min(W, int(x1))):
        blend_px(x, y, c, a)


def fill_rect(x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        hspan(x0, x0 + w, y, c)


def fill_circle(cx, cy, r, c):
    r = int(r)
    if r <= 0:
        return
    for dy in range(-r, r + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        half = int(math.sqrt(max(0, r * r - dy * dy)))
        hspan(cx - half, cx + half + 1, y, c)


def fill_ellipse(cx, cy, rx, ry, c):
    rx = int(rx)
    ry = int(ry)
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        t = dy / ry
        half = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        hspan(cx - half, cx + half + 1, y, c)


def blend_ellipse(cx, cy, rx, ry, c, a):
    rx = int(rx)
    ry = int(ry)
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        y = cy + dy
        if y < 0 or y >= H:
            continue
        t = dy / ry
        half = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        blend_span(cx - half, cx + half + 1, y, c, a)


def fill_triangle(a, b, c, col):
    pts = sorted([(int(p[0]), int(p[1])) for p in (a, b, c)],
                 key=lambda p: p[1])
    (x1, y1), (x2, y2), (x3, y3) = pts

    def ex(xa, ya, xb, yb, y):
        if yb == ya:
            return float(xa)
        return xa + (xb - xa) * (y - ya) / (yb - ya)

    for y in range(max(0, y1), min(H, y3 + 1)):
        xs = []
        if y1 <= y <= y2:
            xs.append(ex(x1, y1, x2, y2, y))
        if y2 <= y <= y3:
            xs.append(ex(x2, y2, x3, y3, y))
        if y1 <= y <= y3:
            xs.append(ex(x1, y1, x3, y3, y))
        if len(xs) >= 2:
            hspan(int(min(xs)), int(max(xs)) + 1, y, col)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def gradient(stops, y0, y1):
    """Fill rows y0..y1 with a vertical gradient through colour stops."""
    n = y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / max(1, n)
        for k in range(len(stops) - 1):
            p0, c0 = stops[k]
            p1, c1 = stops[k + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                hspan(0, W, y, lerp3(c0, c1, f))
                break
        else:
            hspan(0, W, y, stops[-1][1])


def det(n):
    """Deterministic pseudo-random value in [0,1) from a number.

    No random module is used anywhere; the same input always gives the
    same output, so the picture is identical on every run.
    """
    v = math.sin(n * 12.9898) * 43758.5453
    return v - math.floor(v)


# ------------------------------------------------------------------ sky

HORIZON = 600
SUN = (168, 430)


def draw_sky():
    stops = [
        (0.00, (24, 12, 58)),    # deep indigo, top
        (0.35, (72, 30, 96)),    # violet
        (0.62, (166, 60, 108)),  # magenta rose
        (0.82, (252, 120, 52)),  # burning orange
        (1.00, (255, 186, 92)),  # bright gold at the horizon
    ]
    gradient(stops, 0, HORIZON)


def draw_sun():
    cx, cy = SUN
    r2 = 200 * 200
    for dy in range(-200, 201):
        y = cy + dy
        if y < 0 or y >= HORIZON:
            continue
        half = int(math.sqrt(max(0, r2 - dy * dy)))
        for dx in range(-half, half + 1):
            d2 = dx * dx + dy * dy
            if d2 < r2:
                a = (1.0 - d2 / r2) ** 2 * 0.5
                blend_px(cx + dx, y, (255, 166, 66), a)
    fill_circle(cx, cy, 58, (255, 244, 208))
    fill_circle(cx, cy, 42, (255, 252, 236))


def draw_clouds():
    clouds = [
        (640, 92, 170, 20, (255, 150, 108), 0.45),
        (880, 160, 150, 18, (255, 170, 118), 0.50),
        (150, 292, 140, 18, (190, 100, 150), 0.40),
        (430, 302, 160, 16, (225, 130, 130), 0.40),
        (760, 252, 130, 16, (240, 140, 110), 0.45),
    ]
    for cx, cy, rx, ry, col, a in clouds:
        blend_ellipse(cx, cy, rx, ry, col, a)
        blend_ellipse(cx - rx // 2, cy - 4, rx // 2, ry // 2 + 6, col, a * 0.85)
        blend_ellipse(cx + rx // 2, cy - 2, rx // 2, ry // 2 + 5, col, a * 0.85)
        blend_ellipse(cx, cy - 8, rx // 3, ry // 2 + 4, col, a * 0.9)


# ------------------------------------------------------------------ ocean

def draw_ocean():
    stops = [
        (0.00, (40, 64, 112)),   # dusk blue at the horizon
        (0.45, (20, 38, 80)),
        (1.00, (8, 14, 38)),     # almost black at the bottom
    ]
    gradient(stops, HORIZON, H)
    # wave crest lines, broken into dashes and fading with depth
    for k in range(16):
        y0 = 636 + k * 24
        phase = k * 1.7
        col = lerp3((96, 132, 190), (52, 78, 132), k / 15)
        for x in range(0, W, 4):
            if det(x * 0.13 + k * 7.7) < 0.8:
                y = y0 + int(3.0 * math.sin(x * 0.02 + phase))
                hspan(x, x + 3, y, col)
    # warm sun reflection under the sun, broken into shimmering streaks
    for y in range(HORIZON, H, 4):
        a = 0.16 * (1.0 - (y - HORIZON) / (H - HORIZON)) + 0.04
        for s in range(4):
            cx = 168 + int((det(y * 0.9 + s * 13.7) - 0.5) * 170)
            wdt = 14 + int(det(y * 1.7 + s * 5.3) * 42)
            blend_span(cx - wdt, cx + wdt, y, (255, 176, 92), a)
            blend_span(cx - wdt // 2, cx + wdt // 2, y + 1,
                       (255, 210, 140), a * 0.8)


# ------------------------------------------------------------------ city

def draw_city():
    x = 28
    i = 0
    while x < 996:
        w = 34 + int(det(i * 3 + 1) * 46)
        h = 48 + int(det(i * 7 + 2) * 92)
        top = 622 - h
        fill_rect(x, top, w, h, (10, 12, 28))
        # rooftop antenna on some buildings
        if det(i * 11 + 5) < 0.4:
            ax = x + w // 2
            for yy in range(top - 18, top):
                set_px(ax, yy, (10, 12, 28))
            set_px(ax, top - 19, (255, 120, 90))
        # little lit windows
        for wy in range(top + 10, 614, 14):
            for wx in range(x + 6, x + w - 5, 12):
                d = det(wx * 0.37 + wy * 0.91 + i * 3.1)
                if d < 0.36:
                    fill_rect(wx, wy, 5, 7, (255, 196, 92))
                elif d < 0.48:
                    fill_rect(wx, wy, 5, 7, (150, 200, 255))
        x += w + 6
        i += 1


# ------------------------------------------------------------------ whale

# Bezier spine: tail (290, 872) -> control (430, 758) -> head (772, 398)
P0 = (290.0, 872.0)
P1 = (430.0, 758.0)
P2 = (772.0, 398.0)


def spine(t):
    u = 1.0 - t
    return (u * u * P0[0] + 2 * u * t * P1[0] + t * t * P2[0],
            u * u * P0[1] + 2 * u * t * P1[1] + t * t * P2[1])


def spine_tan(t):
    u = 1.0 - t
    dx = 2 * u * (P1[0] - P0[0]) + 2 * t * (P2[0] - P1[0])
    dy = 2 * u * (P1[1] - P0[1]) + 2 * t * (P2[1] - P1[1])
    n = math.hypot(dx, dy)
    return (dx / n, dy / n)


def spine_normal(t):
    """Unit normal pointing to the whale's back (upper-left side)."""
    tx, ty = spine_tan(t)
    return (ty, -tx)


def whale_r(t):
    """Body radius along the spine: thin tail stock, fat belly, blunt head."""
    return 30.0 + 92.0 * math.sin(math.pi * (0.12 + 0.72 * t))


def draw_whale():
    BODY = (46, 98, 168)
    BACK = (26, 60, 122)
    BELLY = (122, 172, 216)
    EDGE = (18, 44, 96)

    # tail flukes, spread wide behind the tail stock
    fill_triangle((296, 858), (168, 952), (300, 906), EDGE)
    fill_triangle((296, 858), (300, 906), (424, 962), EDGE)
    fill_triangle((300, 862), (182, 944), (300, 900), BODY)
    fill_triangle((300, 862), (300, 900), (410, 954), BODY)

    steps = 120
    # dark outline pass, then the main body
    for k in range(steps + 1):
        t = k / steps
        cx, cy = spine(t)
        fill_circle(int(cx), int(cy), int(whale_r(t)) + 4, EDGE)
    for k in range(steps + 1):
        t = k / steps
        cx, cy = spine(t)
        fill_circle(int(cx), int(cy), int(whale_r(t)), BODY)
    # darker back stripe
    for k in range(steps + 1):
        t = k / steps
        cx, cy = spine(t)
        nx, ny = spine_normal(t)
        r = whale_r(t)
        fill_circle(int(cx + nx * r * 0.45), int(cy + ny * r * 0.45),
                    int(r * 0.55), BACK)
    # lighter belly stripe
    for k in range(steps + 1):
        t = k / steps
        cx, cy = spine(t)
        nx, ny = spine_normal(t)
        r = whale_r(t)
        fill_circle(int(cx - nx * r * 0.42), int(cy - ny * r * 0.42),
                    int(r * 0.52), BELLY)

    # dorsal fin on the back
    t = 0.55
    cx, cy = spine(t)
    nx, ny = spine_normal(t)
    tx, ty = spine_tan(t)
    r = whale_r(t)
    fill_triangle((cx + nx * r * 0.8 + tx * 26, cy + ny * r * 0.8 + ty * 26),
                  (cx + nx * r * 0.8 - tx * 26, cy + ny * r * 0.8 - ty * 26),
                  (cx + nx * (r + 58), cy + ny * (r + 58)), BACK)

    # pectoral fin on the belly side
    t = 0.68
    cx, cy = spine(t)
    nx, ny = spine_normal(t)
    tx, ty = spine_tan(t)
    r = whale_r(t)
    bx, by = cx - nx * r * 0.55, cy - ny * r * 0.55
    fill_triangle((bx + tx * 22, by + ty * 22),
                  (bx - tx * 22, by - ty * 22),
                  (bx - nx * 66 - tx * 30, by - ny * 66 - ty * 30), BACK)

    # eye, near the head on the upper side
    t = 0.90
    cx, cy = spine(t)
    nx, ny = spine_normal(t)
    tx, ty = spine_tan(t)
    r = whale_r(t)
    ex = cx + nx * r * 0.30 + tx * 12
    ey = cy + ny * r * 0.30 + ty * 12
    fill_circle(int(ex), int(ey), 8, (8, 14, 28))
    fill_circle(int(ex) - 2, int(ey) - 2, 3, (255, 255, 255))

    # mouth line along the belly edge near the head
    for k in range(18):
        t = 0.87 + 0.12 * k / 17
        cx, cy = spine(t)
        nx, ny = spine_normal(t)
        r = whale_r(t)
        fill_circle(int(cx - nx * r * 0.66), int(cy - ny * r * 0.66),
                    2, (16, 38, 84))


def draw_splash():
    # droplets scattered around the tail where it leaves the water
    for i in range(90):
        a = det(i * 3 + 7) * math.pi * 2
        d = 30 + det(i * 5 + 11) * 130
        x = 300 + int(math.cos(a) * d * 1.15)
        y = 880 + int(math.sin(a) * d * 0.55)
        fill_circle(x, y, 2 + int(det(i * 7 + 3) * 5), (226, 238, 248))
    # spray along the body where it breaks the surface
    for i in range(60):
        t = 0.08 + det(i * 13 + 2) * 0.30
        cx, cy = spine(t)
        nx, ny = spine_normal(t)
        r = whale_r(t)
        off = r * (0.9 + det(i * 17 + 4) * 0.5)
        x = int(cx + nx * off + det(i * 19 + 6) * 30 - 15)
        y = int(cy + ny * off - det(i * 23 + 8) * 26)
        fill_circle(x, y, 2 + int(det(i * 29 + 1) * 4), (235, 244, 252))
    # foam ring on the waterline around the tail
    for a10 in range(0, 360, 6):
        a = math.radians(a10)
        x = 300 + int(math.cos(a) * 150)
        y = 892 + int(math.sin(a) * 26)
        fill_circle(x, y, 4, (240, 246, 252))


# ------------------------------------------------------------------ astronaut

def draw_astronaut():
    t = 0.45
    cx, cy = spine(t)
    nx, ny = spine_normal(t)
    r = whale_r(t)
    fx = int(cx + nx * (r + 2))
    fy = int(cy + ny * (r + 2))
    WHT = (236, 239, 246)
    GRY = (168, 174, 186)
    # soft shadow on the whale's back under the boots
    fill_ellipse(fx, fy + 2, 19, 6, (20, 48, 98))
    # legs
    fill_rect(fx - 9, fy - 16, 7, 16, WHT)
    fill_rect(fx + 2, fy - 16, 7, 16, WHT)
    # torso
    fill_ellipse(fx, fy - 28, 13, 17, WHT)
    # orange chest stripe
    fill_rect(fx - 10, fy - 33, 20, 4, (255, 122, 40))
    # backpack
    fill_rect(fx + 10, fy - 41, 8, 21, GRY)
    # arm reaching forward toward the head
    fill_rect(fx + 7, fy - 38, 14, 6, WHT)
    # helmet with dark visor
    fill_circle(fx, fy - 52, 13, WHT)
    fill_circle(fx + 4, fy - 53, 8, (18, 30, 52))
    fill_circle(fx + 1, fy - 55, 3, (140, 200, 240))


# ------------------------------------------------------------------ bitmap font

# 5x7 glyphs, designed from scratch for this entry.  Only the letters
# the three captions need are defined, plus comma, period and space.
FONT = {
    "A": ["..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "W": ["#...#", "#...#", "#...#", "#...#", "#...#", "#.#.#", ".#.#."],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    ",": [".....", ".....", ".....", ".....", ".....", ".##..", ".#..."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", ".##.."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def draw_glyph(x, y, ch, scale, col):
    g = FONT.get(ch)
    if g is None:
        return
    for row in range(7):
        bits = g[row]
        for ci in range(5):
            if bits[ci] == "#":
                fill_rect(x + ci * scale, y + row * scale, scale, scale, col)


def draw_text(x, y, s, scale, col):
    cx = x
    for ch in s:
        draw_glyph(cx + scale, y + scale, ch, scale, (16, 8, 36))
        draw_glyph(cx, y, ch, scale, col)
        cx += 6 * scale


# ------------------------------------------------------------------ PNG output

def write_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += img[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (OUT, len(png)))


def main():
    draw_sky()
    draw_sun()
    draw_clouds()
    draw_ocean()
    draw_city()
    draw_whale()
    draw_splash()
    draw_astronaut()
    draw_text(56, 56, "THE WHALE", 7, (255, 238, 190))
    draw_text(56, 132, "LEARNED TO FLY", 7, (255, 196, 110))
    draw_text(600, 928, "HOLD ON, JUDGE.", 4, (255, 255, 255))
    write_png()


if __name__ == "__main__":
    main()
