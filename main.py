#!/usr/bin/env python3
"""The World in One Page - 20 November 2026.

Draws a newspaper front page as a 1024x1024 PNG using only the
Python standard library. The image is built pixel by pixel in
memory and encoded with zlib/struct so the output is fully
deterministic: no clock, no randomness, no network.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

CREAM = (255, 248, 231)
INK = (18, 18, 18)
RED = (196, 30, 42)
GREY = (90, 90, 90)
LIGHT_GREY = (200, 195, 180)

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 characters.
# '#' marks a filled pixel. Defined fresh for this entry.
# ---------------------------------------------------------------------------
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["#####", "....#", "....#", "....#", "....#", "#...#", ".###."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ";": [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."],
    "(": ["...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"],
    ")": ["##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "*": [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
}

GLYPH_W = 5
GLYPH_H = 7
GLYPH_ADV = 6


class Canvas:
    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.buf = bytearray(width * height * 3)
        r, g, b = bg
        for i in range(width * height):
            o = i * 3
            self.buf[o] = r
            self.buf[o + 1] = g
            self.buf[o + 2] = b

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 3
            self.buf[o], self.buf[o + 1], self.buf[o + 2] = color

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = yy * self.w * 3
            for xx in range(x0, x1):
                o = base + xx * 3
                self.buf[o] = r
                self.buf[o + 1] = g
                self.buf[o + 2] = b

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def circle(self, cx, cy, radius, color, filled=True):
        r2 = radius * radius
        for yy in range(cy - radius, cy + radius + 1):
            for xx in range(cx - radius, cx + radius + 1):
                d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if filled:
                    if d2 <= r2:
                        self.set_px(xx, yy, color)
                else:
                    if r2 - radius * 3 <= d2 <= r2:
                        self.set_px(xx, yy, color)


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * GLYPH_ADV * scale - scale


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT["?"])
        for row in range(GLYPH_H):
            line = glyph[row]
            for col in range(GLYPH_W):
                if line[col] == "#":
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += GLYPH_ADV * scale
    return cx


def draw_centered(cv, y, text, scale, color):
    w = text_width(text, scale)
    x = (cv.w - w) // 2
    draw_text(cv, x, y, text, scale, color)
    return w


def draw_spiral(cv, cx, cy, max_r, color):
    # Archimedean spiral drawn as small filled squares.
    steps = 900
    for i in range(steps):
        t = i / steps * math.pi * 6.0
        r = max_r * (i / steps)
        x = int(cx + r * math.cos(t))
        y = int(cy + r * math.sin(t))
        cv.rect(x - 2, y - 2, 5, 5, color)
    # Eye of the storm.
    cv.circle(cx, cy, 7, CREAM, filled=True)
    cv.circle(cx, cy, 7, color, filled=False)


def draw_flags(cv, y):
    # Three flag-like rectangles: striped banner, solid disc banner,
    # and a cross banner. Kept abstract on purpose.
    fw, fh = 170, 128
    gap = 46
    total = fw * 3 + gap * 2
    x0 = (W - total) // 2
    # Flag 1: horizontal stripes, red top stripe.
    x = x0
    cv.frame(x, y, fw, fh, INK, t=3)
    cv.rect(x + 3, y + 3, fw - 6, 30, RED)
    cv.rect(x + 3, y + 33, fw - 6, 30, CREAM)
    cv.rect(x + 3, y + 63, fw - 6, 30, INK)
    cv.rect(x + 3, y + 93, fw - 6, fh - 96, CREAM)
    # Flag 2: red field with cream disc.
    x = x0 + fw + gap
    cv.frame(x, y, fw, fh, INK, t=3)
    cv.rect(x + 3, y + 3, fw - 6, fh - 6, RED)
    cv.circle(x + fw // 2, y + fh // 2, 36, CREAM, filled=True)
    # Flag 3: cream field, red cross.
    x = x0 + (fw + gap) * 2
    cv.frame(x, y, fw, fh, INK, t=3)
    cv.rect(x + 3, y + 3, fw - 6, fh - 6, CREAM)
    cv.rect(x + fw // 2 - 10, y + 3, 20, fh - 6, RED)
    cv.rect(x + 3, y + fh // 2 - 10, fw - 6, 20, RED)
    # Poles.
    for i in range(3):
        px = x0 + i * (fw + gap) - 4
        cv.rect(px, y - 10, 4, fh + 26, INK)


def build_page():
    cv = Canvas(W, H, CREAM)

    margin = 56
    inner_w = W - margin * 2

    # Outer border.
    cv.frame(18, 18, W - 36, H - 36, INK, t=3)
    cv.frame(26, 26, W - 52, H - 52, INK, t=1)

    # Masthead.
    y = 64
    cv.rect(margin, y, inner_w, 3, INK)
    y += 16
    draw_centered(cv, y, "THE WORLD IN ONE PAGE", 6, INK)
    y += 7 * 6 + 14
    cv.rect(margin, y, inner_w, 3, INK)
    y += 12
    # Dateline with red rule.
    draw_centered(cv, y, "FRIDAY 20 NOVEMBER 2026", 3, INK)
    y += 7 * 3 + 10
    cv.rect(margin, y, inner_w, 4, RED)
    y += 30

    # Lead story.
    draw_centered(cv, y, "TRUMP XI PUTIN MEET", 5, INK)
    y += 7 * 5 + 16
    draw_centered(cv, y, "FIRST THREE-WAY TALKS IN CHINA", 4, INK)
    y += 7 * 4 + 16
    draw_centered(cv, y, "NUCLEAR RISKS TOP AGENDA", 4, RED)
    y += 7 * 4 + 30

    draw_flags(cv, y)
    y += 128 + 30

    # Thin divider.
    cv.rect(margin, y, inner_w, 2, INK)
    y += 16

    # Second story: text left, cyclone swirl right.
    story_y = y
    draw_text(cv, margin, story_y, "CYCLONE AKVAN NEARS ODISHA", 3, INK)
    story_y += 7 * 3 + 12
    draw_text(cv, margin, story_y, "LANDFALL TODAY - 80000 MOVED", 3, RED)
    story_y += 7 * 3 + 14
    draw_text(cv, margin, story_y, "COASTAL TOWNS EVACUATED AS", 2, GREY)
    story_y += 7 * 2 + 10
    draw_text(cv, margin, story_y, "WINDS RISE AND SEAS SWELL.", 2, GREY)
    draw_spiral(cv, W - margin - 92, y + 58, 62, INK)
    y = story_y + 7 * 2 + 28
    cv.rect(margin, y, inner_w, 2, INK)
    y += 16

    # Smaller headlines in two columns.
    left_items = [
        "WORLD CHILDRENS DAY TODAY",
        "FIJI DROUGHT EMERGENCY",
        "CRIMEA BRIDGE HIT - RAIL CUT",
    ]
    right_items = [
        "NORTH KOREA URANIUM GROWS",
        "ANTHROPIC AT 1.5 TRILLION",
        "NICHOLLS CENTURY IN WELLINGTON",
    ]
    col_w = inner_w // 2
    # Column divider.
    cv.rect(margin + col_w - 1, y, 2, 7 * 2 * 3 + 44 * 2, LIGHT_GREY)
    cy = y
    for item in left_items:
        cv.rect(margin, cy + 4, 10, 10, RED)
        draw_text(cv, margin + 20, cy, item, 2, INK)
        cy += 7 * 2 + 44
    cy = y
    for item in right_items:
        cv.rect(margin + col_w + 14, cy + 4, 10, 10, RED)
        draw_text(cv, margin + col_w + 34, cy, item, 2, INK)
        cy += 7 * 2 + 44
    y = cy + 6

    # Bottom rule and footer.
    cv.rect(margin, y, inner_w, 3, INK)
    y += 14
    draw_centered(cv, y, "ONE IMAGE - ONE DAY - 20 NOV 2026", 3, INK)
    y += 7 * 3 + 10
    cv.rect(margin, y, inner_w, 4, RED)

    return cv


def encode_png(cv):
    raw = bytearray()
    row_bytes = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)  # filter type 0 (None) for every row
        start = yy * row_bytes
        raw.extend(cv.buf[start:start + row_bytes])
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        body = tag + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    canvas = build_page()
    png = encode_png(canvas)
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as fh:
        fh.write(png)
    print(f"wrote {out_path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
