"""Builds the v0.5 redraws of the original sprites (and resized ones) on the
shared palette, using tools/shade.py for round shapes. Run it to print the
rows; they live in art_pack.py as plain data, so the app never runs this.

    python tools/redraw_v05.py > redraws.txt
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shade import circles, shade  # noqa: E402


def blank(w, h):
    return [["."] * w for _ in range(h)]


def paste(grid, rows, x0, y0, skip="."):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != skip and 0 <= y0 + dy < len(grid) and 0 <= x0 + dx < len(grid[0]):
                grid[y0 + dy][x0 + dx] = ch
    return grid


def rows(grid):
    return ["".join(r) for r in grid]


def box(grid, x0, y0, x1, y1, fill, left=None, right=None, outline="k", top=None):
    """A filled rectangle with an outline; optional lit left / shaded right column."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                grid[y][x] = outline
            elif top and y == y0 + 1:
                grid[y][x] = top
            elif left and x == x0 + 1:
                grid[y][x] = left
            elif right and x == x1 - 1:
                grid[y][x] = right
            else:
                grid[y][x] = fill


# ---------------------------------------------------------------- trees
def tree():
    w, h = 22, 27
    g = blank(w, h)
    # trunk with roots
    for y in range(15, 26):
        g[y][9], g[y][10], g[y][11], g[y][12] = "k", "B", "b", "k"
        if y > 17:
            g[y][10] = "B" if y % 4 else "b"
    paste(g, ["kk.kkBbn.kk.",
              ".kkbBBbbnkk."], 5, 24)
    g[26] = list("......kkkkkkkkkk......")
    b = [(11, 12.5, 6), (6.5, 10.5, 5.5), (16, 11, 5.5), (11, 7, 6.2)]
    crown = shade(circles(w, 18, b), w, 18, "qgGl", blobs=b)
    paste(g, crown, 0, 0)
    return rows(g)


def pine():
    w, h = 16, 24
    mask = set()
    for (top, bottom, half) in ((0, 8, 4.5), (5, 14, 6.0), (10, 20, 7.6)):
        for y in range(top, bottom + 1):
            span = half * (y - top + 1) / (bottom - top + 1)
            for x in range(w):
                if abs(x + 0.5 - 8) <= span + 0.4:
                    mask.add((x, y))
    g = blank(w, h)
    paste(g, shade(mask, w, 21, "qgGl", light=(-1.0, -0.4), bands=(-0.55, 0.05, 0.75)), 0, 0)
    for y in range(20, 23):
        g[y][6], g[y][7], g[y][8], g[y][9] = "k", "B", "b", "k"
    g[23] = list("....kkkkkkkk....")
    return rows(g)


def bush():
    w, h = 16, 10
    b = [(4.5, 6.5, 4), (8, 5, 4.8), (11.8, 6.5, 4)]
    g = blank(w, h)
    paste(g, shade(circles(w, h, b, flat_bottom=8), w, h, "qgGl", blobs=b), 0, 0)
    for y, x in ((4, 5), (3, 10), (6, 12)):          # a few flowers, not noise
        g[y][x] = "P"
    g[9] = list(".kkkkkkkkkkkkkk.")
    return rows(g)


def rock():
    w, h = 13, 8
    b = [(5, 5.5, 4.3), (8.6, 5.6, 4)]
    g = blank(w, h)
    paste(g, shade(circles(w, h, b, flat_bottom=6), w, h, "KsSw", bands=(-0.55, 0.0, 0.7)), 0, 0)
    g[7] = list(".kkkkkkkkkkk.")
    return rows(g)


# ---------------------------------------------------------------- small plants
def flower():
    return [
        "..kkk..",
        ".kpPpk.",
        "kpPyPpk",
        "kpyYypk",
        ".kpPpk.",
        "..kkk..",
        "...kGk.",
        ".kkkGk.",
        "kGlGGk.",
        ".kkkGk.",
        "...kGk.",
        "..kkkkk",
    ]


def grass():
    return [
        "....k......k.",
        "...kGk..k.kGk",
        "k..kGk.kGkkGk",
        "Gk.kGlkkGkGlk",
        "lGkGGlkGGkGGk",
        "kkkkkkkkkkkkk",
    ]


def mushroom():
    w = 11
    cap = shade(circles(w, 7, [(5.5, 6.5, 5.6)], flat_bottom=5), w, 7, "rRRp", bands=(-0.6, -0.1, 0.6))
    g = blank(w, 12)
    paste(g, cap, 0, 0)
    for y, x in ((2, 3), (3, 6), (4, 2), (2, 7)):
        if g[y][x] not in ("k", "."):
            g[y][x] = "w"
    paste(g, ["kkkkkkkkkkk"], 0, 6)
    paste(g, ["..keeeek...",
              "..keYeek...",
              "..keYeek...",
              "..keeeBk...",
              "..kkkkkk..."], 0, 7)
    return rows(g)


def seaweed(phase):
    w, h = 10, 16
    mask = set()
    for strand, (base, amp, height) in enumerate(((3, 1.3, 15), (6.5, 1.0, 11))):
        for y in range(h - height, h - 1):
            t = (h - 1 - y) / height
            cx = base + math.sin(t * 5 + phase + strand * 1.7) * amp * t * 1.6
            for x in range(w):
                if abs(x + 0.5 - cx) <= 2.0 - 0.7 * t:
                    mask.add((x, y))
    g = blank(w, h)
    paste(g, shade(mask, w, h, "tTC", light=(-1, 0), bands=(-0.3, 0.4, 2)), 0, 0)
    g[h - 1] = list(".kkkkkkkk.")
    return rows(g)


# ---------------------------------------------------------------- buildings
def castle():
    w, h = 26, 23
    g = blank(w, h)
    # side towers
    for x0 in (0, 18):
        box(g, x0, 4, x0 + 7, 21, "S", left="w", right="s")
        for i, x in enumerate(range(x0, x0 + 8)):
            g[3][x] = "k" if i in (0, 1, 3, 4, 6, 7) else "."
            if i in (1, 4, 6):
                g[3][x] = "S"
        g[3][x0], g[3][x0 + 2], g[3][x0 + 5], g[3][x0 + 7] = "k", "k", "k", "k"
        paste(g, ["kk", "kk"], x0 + 3, 9)                  # arrow slit
    # middle keep, a little lower
    box(g, 7, 8, 18, 21, "S", left="w", right="s")
    for x in range(7, 19):
        g[7][x] = "k" if (x - 7) % 3 != 1 else "."
    # door
    paste(g, ["..kkkk..",
              ".knnnnk.",
              "knnnnnnk",
              "knnyynnk",
              "knnnnnnk",
              "knnnnnnk"], 9, 15)
    # windows
    paste(g, ["kyk", "kYk"], 11, 10)
    # flag
    paste(g, ["k.", "kR", "kRR", "k."], 3, 0)
    g[22] = list("k" * w)
    return rows(g)


def cottage():
    w, h = 26, 22
    g = blank(w, h)
    # roof: a stepped triangle of shingles
    for y in range(0, 10):
        half = 2 + y * 1.25
        for x in range(w):
            d = abs(x + 0.5 - 13)
            if d <= half:
                edge = d > half - 1.2 or y == 9
                g[y][x] = "k" if edge else ("R" if (x + y) % 4 else "r")
                if not edge and y < 3 + x * 0.2:
                    g[y][x] = "p" if (x + y) % 4 else "R"
    # chimney
    paste(g, ["kkk", "kKk", "kKk"], 18, 1)
    # walls
    box(g, 3, 10, 22, 20, "e", left="Y", right="B")
    # window with warm light
    paste(g, ["kkkkk", "kcCck", "kkkkk", "kcCck", "kkkkk"], 6, 12)
    # door
    paste(g, ["kkkkk", "kBbBk", "kBbBk", "kBByk", "kBbBk", "kBbBk", "kBbBk"], 15, 13)
    g[20][3:23] = list("k" * 20)
    g[21] = list(".." + "k" * 22 + "..")
    return rows(g)


# ---------------------------------------------------------------- pets
def fish(frame):
    """Hand-drawn: body lit from the top, tail swinging up, level, down."""
    return ([
        "....kkkkk....",
        "kk.kOyyyOk...",
        "kOkOyyOOOOkk.",
        "kOOOOOOOOwkOk",
        "kOkOOOOOOOkk.",
        "kk.kBBBBBk...",
        "....kkkkk....",
    ], [
        "....kkkkk....",
        "...kOyyyOk...",
        "kkkOyyOOOOkk.",
        "kOOOOOOOOwkOk",
        "kkkOOOOOOOkk.",
        "...kBBBBBk...",
        "....kkkkk....",
    ], [
        "....kkkkk....",
        "...kOyyyOk...",
        "k.kOyyOOOOkk.",
        "kOkOOOOOOwkOk",
        "kOOOOOOOOOkk.",
        "kk.kBBBBBk...",
        "....kkkkk....",
    ])[frame]


def slime(frame):
    if frame == 0:
        w, h = 12, 10
        b = [(6, 7.5, 5.6)]
        g = blank(w, h)
        paste(g, shade(circles(w, h, b, flat_bottom=8), w, h, "gGGl", bands=(-0.5, -0.1, 0.55)), 0, 0)
        eyes_y, base = 5, 9
    else:
        w, h = 12, 10
        b = [(6, 9, 6.2)]
        g = blank(w, h)
        paste(g, shade(circles(w, h, b, flat_bottom=8), w, h, "gGGl", bands=(-0.5, -0.1, 0.55)), 0, 0)
        eyes_y, base = 6, 9
    g[eyes_y][7], g[eyes_y][9] = "k", "k"                 # eyes on the right (facing right)
    g[eyes_y - 1][7], g[eyes_y - 1][9] = "k", "k"
    for y in range(h):
        for x in range(w):
            if g[y][x] == "l" and (x + y) % 3 == 0:
                g[y][x] = "w"                               # a glossy glint
                break
    g[base] = list(".kkkkkkkkkk.")
    return rows(g)


def cat(frame):
    legs = (["...kOk.kOk.kOk..", "...kk..kk..kk..."],
            ["..kOk..kOk..kOk.", "..kk...kk....kk."])[frame]
    body = [
        "..........k...k.",
        "..........kk.kk.",
        "k.........kOOOOk",
        "kOk.......kOkOkk",
        ".kOk.kkkkkkyOpOk",
        "..kOOOOOOOOOOkk.",
        "..kOyyOOOOOOBk..",
        "..kOOOOOOOOBBk..",
    ]
    if frame == 1:
        body[2], body[3] = "..........kOOOOk", "k.........kOkOkk"
        body[4] = "kOk..kkkkkkyOpOk"
    return body + legs


def bird(frame):
    if frame == 0:     # wings up
        return [
            "...kk.......",
            "..kcUk......",
            "..kUcUk.kk..",
            "...kUUkkUUk.",
            "..kUUUUUUwkk",
            ".kUcccUUUkyy",
            "kUUUUUUUUk..",
            ".kkkkkkkkk..",
            "....kk.kk...",
        ]
    return [               # wings down
        "............",
        "............",
        "........kk..",
        ".......kUUk.",
        "..kkkkkUUwkk",
        ".kUcccUUUkyy",
        "kUUkUUUUUk..",
        ".kUUUkkkkk..",
        "..kkk.kk....",
    ]


def butterfly(frame):
    if frame == 0:
        return [
            ".kk.....kk.",
            "kmVk...kVmk",
            "kVmVk.kVmVk",
            ".kVVkkkVVk.",
            "..kmVkVmk..",
            "..kVk.kVk..",
            "...k...k...",
        ]
    return [
        "...........",
        "....k.k....",
        "...kVkVk...",
        "...kmkmk...",
        "...kVkVk...",
        "....k.k....",
        "...........",
    ]


def lamp():
    return [
        "..kkk..",
        ".kKKKk.",
        "kYyYyYk",
        "kyYYYyk",
        ".kkkkk.",
        "..kKk..",
        "..kKk..",
        "..kKk..",
        "..kKk..",
        "..kKk..",
        "..kKk..",
        ".kKKKk.",
        "kkkkkkk",
    ]


ALL = {
    "tree": [tree()], "pine": [pine()], "bush": [bush()], "rock": [rock()],
    "flower": [flower()], "grass": [grass()], "mushroom": [mushroom()],
    "seaweed": [seaweed(0), seaweed(1.6)], "castle": [castle()], "cottage": [cottage()],
    "fish": [fish(0), fish(1), fish(2)], "slime": [slime(0), slime(1)],
    "cat": [cat(0), cat(1)], "bird": [bird(0), bird(1)], "butterfly": [butterfly(0), butterfly(1)],
    "lamp": [lamp()],
}

if __name__ == "__main__":
    for name, frames in ALL.items():
        print("#", name)
        for f in frames:
            print(f)
