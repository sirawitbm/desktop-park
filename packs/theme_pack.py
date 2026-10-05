"""The Theme Pack: seven ready-made parks and 24 new pictures.

It ships as an optional extra download (DesktopPark-ThemePack-vX.Y.Z-Setup.exe,
or the .parkpack file for the portable app), so the app itself stays as it is.
`python tools/build_pack.py` turns this file into the .parkpack file.

The pictures use the app's shared palette (art_pack.PAL) plus four snow and
sand shades. Their ids start with "scene-"; they arrive as drawings, so they
can be edited like any other. Everything faces right, light from the top-left.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import art  # noqa: E402

PACK_ID = "theme-pack"
PACK_NAME = "Theme Pack"
PACK_VERSION = "1.0.0"     # bump when the pack changes, so existing parks take it in again

PAL = {
    "k": "#1a1c2c", "K": "#333c57", "s": "#566c86", "S": "#94b0c2", "w": "#f4f4f4",
    "q": "#1e4a3a", "g": "#257953", "G": "#38b764", "l": "#a7f070",
    "n": "#3d2a24", "b": "#6e4a30", "B": "#a8703c", "e": "#e8c48c",
    "r": "#8c2a3a", "R": "#d6404e", "p": "#ff8a9a", "P": "#ffcdd2",
    "O": "#ef7d3a", "y": "#ffcd4f", "Y": "#fff1a8",
    "u": "#29366f", "U": "#3b5dc9", "c": "#41a6f6", "C": "#73eff7",
    "v": "#4b2a6b", "V": "#8a4fc0", "m": "#d69cf2",
    "t": "#1f6f73", "T": "#3fb8a8",
    # a few extra shades the themes need
    "a": "#c9e4f0",   # snow shadow
    "d": "#f6dfa8",   # light sand
    "f": "#d9b06c",   # sand mid
    "h": "#b58a4f",   # sand dark
}


def deco(id, name, frames):
    return {"id": "scene-" + id, "name": name, "kind": "deco", "behavior": "stay",
            "palette": PAL, "frames": frames}


def pet(id, name, behavior, frames):
    return {"id": "scene-" + id, "name": name, "kind": "pet", "behavior": behavior,
            "palette": PAL, "frames": frames}


def grid(w, h):
    return [["."] * w for _ in range(h)]


def rows(g):
    return ["".join(r) for r in g]


# -- sakura garden -------------------------------------------------------------

TORII = [
    "kk....................kk",
    "kKkkkkkkkkkkkkkkkkkkkkKk",
    ".kKKKKKKKKKKKKKKKKKKKKk.",
    "..kkkkkkkkkkkkkkkkkkkk..",
    "..kpRRRRRRRRRRRRRRRRrk..",
    "..kkkkkkkkkkkkkkkkkkkk..",
    "....kpRrk.kkkk.kpRrk....",
    "....kpRrk.kYyk.kpRrk....",
    "..kkkkkkkkkkkkkkkkkkkk..",
    "..kpRRRRRRRRRRRRRRRRrk..",
    "..kkkkkkkkkkkkkkkkkkkk..",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "....kpRrk......kpRrk....",
    "...kKKKKKk....kKKKKKk...",
    "...kkkkkkk....kkkkkkk...",
]

LANTERN = [
    "....kk....",
    "...kSsk...",
    ".kkSSSskk.",
    "kSSSSSSssk",
    "kkkkkkkkkk",
    ".kSyYYysk.",
    ".kSyYYysk.",
    ".kkkkkkkk.",
    "..kSSSsk..",
    "...kSsk...",
    "...kSsk...",
    "...kSsk...",
    "...kSsk...",
    "..kSSSsk..",
    ".kSSSSssk.",
    "kkkkkkkkkk",
]


def bridge():
    """A red arched garden bridge, 34 x 14."""
    w, h = 34, 14
    g = grid(w, h)
    rise = 5

    def top(x):                       # deck surface row at column x
        return 9 - round(rise * math.sin(math.pi * (x + 0.5) / w))

    for x in range(w):
        t = top(x)
        # deck: outline, light wood, dark wood, outline
        g[t][x] = "k"
        g[t + 1][x] = "B"
        g[t + 2][x] = "b"
        g[t + 3][x] = "k"
        # railing 3 rows above the deck: top rail red
        g[t - 3][x] = "k"
        g[t - 2][x] = "R"
        g[t - 1][x] = "."
        if x % 6 == 1 or x in (0, w - 1):            # posts
            g[t - 1][x] = "r"
    for x in range(w):                                # rail highlight on the top
        t = top(x)
        if g[t - 2][x] == "R" and x % 3 == 0:
            g[t - 2][x] = "p"
    # end posts reach the ground
    for x in (0, 1, w - 2, w - 1):
        for y in range(top(x) + 4, h):
            g[y][x] = "k" if x in (0, w - 1) else "r"
    return rows(g)


KOI = [[
    "....kkkkk.....",
    "kk.kwwOOwk....",
    "kOkwOOwwwwkk..",
    "kOOwwwwwOOwkk.",
    "kOkwwwwOOOwwkk",
    "kk.kSwwwwwk...",
    "....kkkkkk....",
], [
    "....kkkkk.....",
    "...kwwOOwk....",
    "kkkwOOwwwwkk..",
    "kOOwwwwwOOwkk.",
    "kkkwwwwOOOwwkk",
    "...kSwwwwwk...",
    "....kkkkkk....",
]]

BENCH = [
    "................",
    ".kkkkkkkkkkkkkk.",
    "kBeBeBeBeBeBeBBk",
    "kkkkkkkkkkkkkkkk",
    "..kk........kk..",
    ".kkkkkkkkkkkkkk.",
    "kBeBeBeBeBeBeBbk",
    "kbbbbbbbbbbbbbbk",
    "kkkkkkkkkkkkkkkk",
    ".kKk........kKk.",
    ".kKk........kKk.",
    ".kkk........kkk.",
]


STREAM = [
    "....kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk....",
    "..kkcCcccccCCcccccccccCcccccccCCccccckk.",
    ".kcccccCcccccccccwcccccccccccccccccccUck",
    "kUcccccccccUUcccccccccccUUcccccccccUUUUk",
    ".kUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUk.",
    "..kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk..",
]


# -- forest camp ---------------------------------------------------------------

def tent():
    """An A-frame tent with an open door, 22 x 14."""
    w, h = 22, 14
    g = grid(w, h)
    g[0][11] = "b"
    g[1][11] = "b"
    for i in range(12):               # rows 1..12
        y = i + 1
        left, right = 10 - i, 11 + i
        if left < 0:
            break
        for x in range(left, right + 1):
            if x in (left, right):
                ch = "k"
            elif i >= 5 and abs(x - 10.5) < (i - 4) * 0.55:
                ch = "K" if abs(x - 10.5) < (i - 4) * 0.55 - 1 else "k"
            elif x == left + 1:
                ch = "y"
            elif x <= 10:
                ch = "O"
            elif x == right - 1:
                ch = "r"
            else:
                ch = "R"
            g[y][x] = ch
    for x in range(w):
        g[h - 1][x] = "k" if 0 < x < w - 1 else "."
    g[h - 1][0] = g[h - 1][w - 1] = "."
    # guy ropes and pegs
    g[h - 1][0] = "b"
    g[h - 1][w - 1] = "b"
    return rows(g)


FOX = [[
    "..........k..k....",
    "..........kk.kk...",
    "..........kOOOOk..",
    ".kkk......kOOkOOk.",
    "kOOOk.kkkkkOOOwwkk",
    "kOOOOkOOOOOOOwwwk.",
    "kwOOOOOOOOOOOkkk..",
    ".kwwOOOOOOOOOk....",
    "..kkkOwwwwwOOk....",
    "....knk.knk.knk...",
    "....kk..kk..kk....",
], [
    "..........k..k....",
    "..........kk.kk...",
    "..........kOOOOk..",
    "..kk......kOOkOOk.",
    ".kOOk.kkkkkOOOwwkk",
    "kOOOOkOOOOOOOwwwk.",
    "kwOOOOOOOOOOOkkk..",
    ".kwwOOOOOOOOOk....",
    "..kkkOwwwwwOOk....",
    "...knk..knk.knk...",
    "...kk...kk...kk...",
]]

OWL = [[
    "k..........k",
    "kk.k....k.kk",
    "kBkbkkkkbkBk",
    ".kBbBBBBbBk.",
    "..kewwkwwek.",
    "..kwkwywkwk.",
    "..kBwwkwwBk.",
    "..kBeBBeBbk.",
    "...kBeeBbk..",
    "....kkkkk...",
], [
    "............",
    "...k....k...",
    "..kbkkkkbk..",
    ".kBbBBBBbBk.",
    "kBkewwkwwekk",
    "kBkwkwywkwBk",
    ".kkBwwkwwBk.",
    "..kBeBBeBbk.",
    "...kBeeBbk..",
    "....kkkkk...",
]]

LOG = [
    "...kkkkkkkkkkkk.",
    "..kBBBBBBBBBBkek",
    ".kbBbbBbbbBbkeBe",
    ".kbbbbbbbbbbkebe",
    ".kbbnbbbnbbbkeBe",
    "..knnnnnnnnnnkek",
    "...kkkkkkkkkkkk.",
]


# -- helpers for the bigger pieces ---------------------------------------------

def outline(g, colour="k"):
    """Put a 1px outline round everything that is drawn (4-neighbours)."""
    h, w = len(g), len(g[0])
    out = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and g[ny][nx] not in ".k":
                    out[y][x] = colour
                    break
    return out


def put(g, x, y, ch):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = ch


# -- tropical beach ------------------------------------------------------------

def umbrella():
    w, h = 18, 21
    g = grid(w, h)
    cx = 8.5
    for y in range(1, 7):
        hw = 8.6 * math.sqrt(max(0.0, 1 - ((6.6 - y) / 6.2) ** 2))
        for x in range(w):
            if abs(x - cx) <= hw:
                seg = int((x - (cx - 9)) // 3.6)
                light = x < cx
                if seg % 2 == 0:
                    g[y][x] = "R" if light else "r"
                else:
                    g[y][x] = "w" if light else "S"
    for x in range(w):                       # scalloped edge
        if g[6][x] != "." and x % 4 == 1:
            g[7][x] = g[6][x]
    g[0][8] = g[0][9] = "K"
    for y in range(7, h - 1):
        g[y][8] = "w"
        g[y][9] = "S"
    g = outline(g)
    return rows(g)


SANDCASTLE = [
    ".........k.........",
    ".........kRRk......",
    ".........kRk.......",
    "......kkkkkkk......",
    "......kdkkkdk......",
    "......kdfffhk......",
    "kkk.kkkdfffhkkk.kkk",
    "kdkkkdkdfffhkdkkkdk",
    "kdfffhkdfffhkdfffhk",
    "kdfkfhkdfffhkdfkfhk",
    "kdfffhkdkkkhkdfffhk",
    "kdfffhkdkKkhkdfffhk",
    "kdfffhkdkKkhkdfffhk",
    "kkkkkkkkkkkkkkkkkkk",
]

GULL = [[
    "...kk...........",
    "...kSk..........",
    "....kSk.........",
    "....kSSk..kkkk..",
    ".kk.kSSSkkwwkwk.",
    "kSSkwwwwwwwwwkyy",
    ".kkwwwwSSSSwwk..",
    "...kkkkkkkkkk...",
], [
    "................",
    "................",
    "................",
    "..........kkkk..",
    ".kk.kkkkkkwwkwk.",
    "kSSkwwSSSSwwwkyy",
    ".kkwwkSSSSkwwk..",
    "...kkkkSSkkkk...",
]]

STARFISH = [
    "....kk....",
    "...kOOk...",
    "...kOyk...",
    "kkkkOOkkkk",
    "kOOyOOOyOk",
    ".kkOOyOkk.",
    "..kOOkOOk.",
    ".kOOk.kOOk",
    ".kkk...kkk",
]


# -- snowy village -------------------------------------------------------------

def snowy_pine(pine_rows):
    g = [list(r) for r in pine_rows]
    for y in range(len(g)):
        for x in range(len(g[0])):
            if g[y][x] in "Gg" and (y == 0 or g[y - 1][x] in ".k"):
                g[y][x] = "w"
                if y + 1 < len(g) and g[y + 1][x] in "Gg" and x < len(g[0]) // 2 + 1:
                    g[y + 1][x] = "a"
    return rows(g)


SNOWMAN = [
    "....kkkk....",
    "....kKKk....",
    "...kkkkkk...",
    "...kwwwwak..",
    "...kwkwkak..",
    "...kwwwwOOO.",
    "..kRRRRRRk..",
    "b..kRrwwak.b",
    ".bkwRrwwwakb",
    ".kwwwwkwwwak",
    ".kwwwwwwwaak",
    ".kwwwwkwwaak",
    ".kwwwwwwwaak",
    ".kawwwwwwaak",
    "..kaawwwaak.",
    "..kkkkkkkk..",
]


# -- countryside farm ----------------------------------------------------------

def windmill():
    w, h = 22, 36
    hx, hy = 10, 9  # hub above the cap
    frames = []
    for diagonal in (False, True):
        g = grid(w, h)
        for y in range(14, h - 1):                    # tower
            hw = 4 + (y - 14) * 3.2 / (h - 15)
            left, right = round(10.5 - hw), round(10.5 + hw) - 1
            for x in range(left, right + 1):
                g[y][x] = "w" if x == left else ("s" if x == right else "S")
        for y in range(29, h - 1):                    # door
            for x in (9, 10, 11):
                g[y][x] = "b" if x < 11 else "n"
        for y in (19, 20):                            # window
            g[y][10] = g[y][11] = "K"
        for y, hw in ((9, 2.5), (10, 3.5), (11, 4.5), (12, 5), (13, 5.5), (14, 5.5)):   # cap
            for x in range(w):
                if abs(x - 10.5) <= hw:
                    g[y][x] = "p" if x < 9 else ("R" if x < 12 else "r")
        dirs = ((1, -1), (1, 1), (-1, 1), (-1, -1)) if diagonal else ((0, -1), (1, 0), (0, 1), (-1, 0))
        length = 7 if diagonal else 9
        for dx, dy in dirs:
            px, py = -dy, dx                           # sail on the clockwise side
            for d in range(2, length + 1):
                put(g, hx + dx * d, hy + dy * d, "b")
                if d >= 3:
                    for o in (1, 2):
                        put(g, hx + dx * d + px * o, hy + dy * d + py * o,
                            "e" if (d + o) % 2 else "w")
                    if diagonal:                       # fill the gaps a diagonal leaves
                        put(g, hx + dx * d + px, hy + dy * d, "e")
        for x, y in ((10, 8), (11, 8), (10, 9), (11, 9)):
            put(g, x, y, "K")
        g = outline(g)
        frames.append(rows(g))
    return frames


HAYSTACK = [
    "....kkkkkk....",
    "..kkYYyyyykk..",
    ".kYYyyyyyyyBk.",
    ".kYyyyByyyyBk.",
    "kYyyyyyyyBByBk",
    "kyyyByyyyyyyBk",
    "kyyyyyyByyyBBk",
    "kyByyyyyyyBBBk",
    "kBBBBhBBBBhBBk",
    "kkkkkkkkkkkkkk",
]

SHEEP = [[
    "...kk.kkk......",
    "..kwwkwwwk.kkk.",
    ".kwwwwwwwwkKKKk",
    "kwwwwwwwwwkKwKk",
    "kwwwwwwwwwkKKKk",
    "kwwwwwwwwSSkkk.",
    ".kSwwwwwSSSk...",
    "..kkkkkkkkk....",
    "...kK.kK.kK....",
    "...kK.kK.kK....",
    "...kk.kk.kk....",
], [
    "...kk.kkk......",
    "..kwwkwwwk.kkk.",
    ".kwwwwwwwwkKKKk",
    "kwwwwwwwwwkKwKk",
    "kwwwwwwwwwkKKKk",
    "kwwwwwwwwSSkkk.",
    ".kSwwwwwSSSk...",
    "..kkkkkkkkk....",
    "..kK..kK..kK...",
    "..kK..kK..kK...",
    "..kk..kk..kk...",
]]


# -- under the sea -------------------------------------------------------------

def kelp():
    w, h = 12, 30
    frames = []
    for phase in (0.0, 1.6):
        g = grid(w, h)
        for y in range(h):
            k = (h - y) / h                          # sways more at the top
            x = round(5.5 + 1.6 * k * math.sin(y / 3.5 + phase))
            put(g, x - 1, y, "l")
            put(g, x, y, "G")
            put(g, x + 1, y, "g")
            if y % 5 == 2 and y < h - 4:              # leaves, alternating sides
                if (y // 5) % 2:
                    for dx, dy, ch in ((-2, 0, "l"), (-3, 1, "G"), (-2, 1, "G"), (-3, 2, "g")):
                        put(g, x + dx, y + dy, ch)
                else:
                    for dx, dy, ch in ((2, 0, "G"), (3, 1, "g"), (2, 1, "g"), (3, 2, "q")):
                        put(g, x + dx, y + dy, ch)
        g = outline(g)
        frames.append(rows(g))
    return frames


# -- ground strips (lay several side by side along the bottom) -----------------

def strip(kind, seed):
    import random
    rng = random.Random(seed)
    w, h = 48, 6
    g = grid(w, h)
    for x in range(w):
        if kind == "grass":
            tip = rng.choice((0, 1, 1, 2, 2, 2))
            for y in range(tip, h):
                g[y][x] = ("l" if y == tip and rng.random() < 0.5 else "G") if y < 3 else ("g" if y < 5 else "q")
        elif kind == "sand":
            tip = rng.choice((1, 2, 2, 2))
            for y in range(tip, h):
                g[y][x] = "d" if y < 3 else ("f" if y < 5 else "h")
            if rng.random() < 0.08:
                g[3][x] = "w"
            if rng.random() < 0.08:
                g[4][x] = "h"
        elif kind == "snow":
            tip = 1 + round(0.6 + 0.6 * math.sin(x / 4.0 + seed))
            for y in range(tip, h):
                g[y][x] = "w" if y < 4 else ("a" if y < 5 else "S")
        elif kind == "seabed":
            tip = rng.choice((1, 2, 2, 3))
            for y in range(tip, h):
                g[y][x] = "f" if y < 3 else ("h" if y < 5 else "b")
            if rng.random() < 0.1:
                g[tip][x] = "d"
    for x in range(w):                         # outline only along the top
        for y in range(h):
            if g[y][x] != ".":
                if y > 0:
                    g[y - 1][x] = "k"
                break
    return rows(g)


def app_pine():
    return art.builtin_by_id()["pine"]["frames"][0]


ART = [
    deco("torii", "Torii gate", [TORII]),
    deco("lantern", "Stone lantern", [LANTERN]),
    deco("bridge", "Garden bridge", [bridge()]),
    pet("koi", "Koi", "swim", KOI),
    deco("bench", "Bench", [BENCH]),
    deco("stream", "Stream", [STREAM]),
    deco("tent", "Tent", [tent()]),
    pet("fox", "Fox", "walk", FOX),
    pet("owl", "Owl", "fly", OWL),
    deco("log", "Log", [LOG]),
    deco("umbrella", "Beach umbrella", [umbrella()]),
    deco("sandcastle", "Sandcastle", [SANDCASTLE]),
    pet("gull", "Seagull", "fly", GULL),
    deco("starfish", "Starfish", [STARFISH]),
    deco("snowpine", "Snowy pine", [snowy_pine(app_pine())]),
    deco("snowman", "Snowman", [SNOWMAN]),
    deco("windmill", "Windmill", windmill()),
    deco("haystack", "Haystack", [HAYSTACK]),
    pet("sheep", "Sheep", "walk", SHEEP),
    deco("kelp", "Kelp", kelp()),
    deco("grass-strip", "Grass ground", [strip("grass", 3)]),
    deco("sand-strip", "Sand ground", [strip("sand", 5)]),
    deco("snow-strip", "Snow ground", [strip("snow", 2)]),
    deco("seabed-strip", "Seabed", [strip("seabed", 9)]),
]


# -- the parks -------------------------------------------------------------------
# Laid out on a 1920 x 1032 screen (1080p above the taskbar); Desktop Park fits
# them to any screen. Each item: (art id, x, scale) stands on the ground;
# (art id, x, scale, behavior) for a pet; (art id, x, scale, behavior, y) for
# something in the air. Things are drawn in order: the first are at the back.

W, H = 1920, 1032


def ground(art_id, scale=3, width=48):
    """A ground strip picture laid end to end across the screen."""
    step = width * scale
    return [(art_id, x, scale) for x in range(0, W, step)]


PARKS = [
    {
        "name": "Sakura Garden",
        "weather": "clear", "time_mode": "clock", "show_sky": True,
        "items": ground("scene-grass-strip") + [
            ("cherry", 10, 6), ("cherry", 590, 4), ("cherry", 670, 5), ("cherry", 1370, 4),
            ("cherry", 1460, 5), ("cherry", 1730, 6),
            ("scene-torii", 1180, 5),
            ("bush", 200, 4), ("scene-lantern", 330, 4),
            ("scene-stream", 390, 4), ("scene-bridge", 402, 4), ("rock", 520, 3), ("grass", 380, 3),
            ("scene-lantern", 1135, 4), ("scene-lantern", 1310, 4),
            ("scene-bench", 830, 4), ("lamp", 905, 4), ("bush", 1040, 3),
            ("tulips", 160, 4), ("tulips", 790, 3), ("flower", 960, 4), ("tulips", 990, 4),
            ("bush", 1610, 4), ("tulips", 1680, 3), ("flower", 1350, 4), ("grass", 1880, 3),
            ("grass", 1100, 3), ("flower", 560, 3),
            ("bunny", 260, 4, "hop"), ("cat", 1000, 4, "walk"), ("duck", 700, 4, "walk"),
            ("butterfly", 520, 4, "fly", 760), ("butterfly", 1500, 4, "fly", 820),
            ("bird", 1250, 4, "fly", 600),
        ],
    },
    {
        "name": "Forest Camp",
        "weather": "clear", "time_mode": "night", "show_sky": True,
        "items": ground("scene-grass-strip") + [
            ("pine", 0, 7), ("pine", 90, 5), ("tree", 170, 6), ("pine", 300, 4),
            ("pine", 1140, 4), ("pine", 1230, 5),
            ("pine", 1500, 5), ("pine", 1590, 7), ("tree", 1700, 5), ("pine", 1820, 6),
            ("scene-tent", 560, 6), ("lamp", 470, 4),
            ("stump", 400, 4), ("mushroom", 360, 3), ("mushroom", 445, 4),
            ("scene-log", 760, 4), ("campfire", 860, 5), ("scene-log", 940, 4),
            ("bush", 1080, 4), ("mushroom", 1150, 3), ("rock", 1190, 4),
            ("scene-log", 1300, 5), ("stump", 1420, 4), ("mushroom", 1470, 3), ("grass", 250, 3),
            ("scene-fox", 700, 4, "walk"), ("cat", 1000, 4, "walk"), ("bunny", 1250, 4, "hop"),
            ("scene-owl", 1350, 4, "fly", 520), ("scene-owl", 300, 3, "fly", 600),
        ],
    },
    {
        "name": "Tropical Beach",
        "weather": "sun", "time_mode": "clock", "show_sky": True,
        "items": ground("scene-sand-strip") + [
            ("palm", 0, 7), ("palm", 230, 5), ("palm", 1040, 4), ("palm", 1560, 5), ("palm", 1740, 7),
            ("rock", 420, 5), ("coral", 470, 3), ("rock", 1090, 3),
            ("scene-umbrella", 700, 6), ("scene-umbrella", 860, 5), ("chest", 1180, 4),
            ("scene-sandcastle", 1260, 5), ("scene-starfish", 1370, 3), ("scene-starfish", 620, 3),
            ("coral", 1430, 4), ("rock", 1490, 3), ("scene-starfish", 1660, 3), ("grass", 340, 3),
            ("crab", 560, 4, "walk"), ("crab", 1340, 3, "walk"), ("turtle", 960, 4, "walk"),
            ("scene-gull", 500, 4, "fly", 420), ("scene-gull", 1300, 3, "fly", 300),
        ],
    },
    {
        "name": "Snowy Village",
        "weather": "snow", "time_mode": "clock", "show_sky": True,
        "items": ground("scene-snow-strip") + [
            ("scene-snowpine", 0, 7), ("scene-snowpine", 100, 5), ("scene-snowpine", 190, 6),
            ("scene-snowpine", 1600, 6), ("scene-snowpine", 1700, 8), ("scene-snowpine", 1830, 5),
            ("scene-snowpine", 980, 5), ("cottage", 1060, 4),
            ("cottage", 700, 6), ("lamp", 640, 5), ("lamp", 880, 5),
            ("fence", 380, 4), ("fence", 444, 4), ("fence", 508, 4),
            ("fence", 1200, 4), ("fence", 1264, 4),
            ("scene-snowman", 330, 5), ("scene-snowman", 1350, 4),
            ("rock", 1180, 3), ("scene-snowpine", 1440, 4), ("scene-snowpine", 1500, 5),
            ("penguin", 560, 4, "walk"), ("penguin", 1320, 4, "walk"), ("bunny", 1000, 4, "hop"),
            ("bird", 900, 4, "fly", 500),
        ],
    },
    {
        "name": "Countryside Farm",
        "weather": "clear", "time_mode": "clock", "show_sky": True,
        "items": ground("scene-grass-strip") + [
            ("tree", 0, 7), ("tree", 1000, 4), ("scene-windmill", 1560, 6), ("tree", 1800, 5),
            ("cottage", 220, 5), ("scene-haystack", 380, 5),
            ("fence", 530, 4), ("fence", 594, 4), ("fence", 658, 4), ("fence", 722, 4),
            ("sunflower", 800, 4), ("sunflower", 830, 5), ("sunflower", 880, 4), ("sunflower", 920, 5),
            ("scene-haystack", 1100, 4), ("scene-haystack", 1170, 5),
            ("fence", 1300, 4), ("fence", 1364, 4), ("bush", 1440, 4),
            ("tulips", 1060, 3), ("grass", 780, 3), ("flower", 1500, 4), ("tulips", 1700, 3),
            ("scene-sheep", 600, 4, "walk"), ("scene-sheep", 1250, 4, "walk"),
            ("scene-sheep", 1390, 3, "walk"), ("chick", 470, 3, "walk"), ("chick", 520, 3, "walk"),
            ("duck", 980, 4, "walk"), ("dog", 160, 4, "walk"),
            ("bee", 860, 3, "fly", 860), ("butterfly", 1040, 4, "fly", 780),
        ],
    },
    {
        "name": "Under the Sea",
        "weather": "clear", "time_mode": "day", "show_sky": False,
        "items": ground("scene-seabed-strip") + [
            ("scene-kelp", 20, 6), ("scene-kelp", 90, 4), ("seaweed", 150, 5),
            ("castle", 230, 5), ("coral", 380, 4), ("rock", 440, 5), ("seaweed", 500, 3),
            ("scene-kelp", 560, 5), ("chest", 640, 5), ("crystal", 730, 4),
            ("seaweed", 820, 4), ("coral", 870, 5), ("scene-starfish", 950, 3),
            ("scene-kelp", 1010, 6), ("rock", 1080, 4), ("coral", 1150, 3), ("seaweed", 1220, 5),
            ("scene-kelp", 1280, 4), ("crystal", 1350, 3), ("coral", 1420, 4), ("scene-kelp", 1500, 5),
            ("rock", 1580, 4), ("seaweed", 1650, 4), ("coral", 1700, 3),
            ("scene-kelp", 1740, 6), ("scene-kelp", 1840, 4),
            ("crab", 520, 4, "walk"), ("turtle", 1000, 4, "walk"),
            ("fish", 300, 4, "swim", 700), ("fish", 1300, 3, "swim", 560),
            ("scene-koi", 900, 4, "swim", 780), ("scene-koi", 1600, 4, "swim", 650),
            ("puffer", 600, 4, "swim", 820), ("jelly", 1100, 4, "swim", 500),
            ("jelly", 200, 3, "swim", 450),
        ],
    },
    {
        "name": "Halloween Night",
        "weather": "clear", "time_mode": "night", "show_sky": True,
        "items": ground("scene-grass-strip") + [
            ("spookytree", 0, 7), ("spookytree", 1700, 6), ("spookytree", 1100, 4),
            ("spookytree", 560, 3),
            ("cottage", 260, 5), ("lamp", 210, 4),
            ("fence", 420, 4), ("fence", 484, 4),
            ("grave", 600, 4), ("grave", 660, 5), ("grave", 740, 4),
            ("cauldron", 860, 5), ("jack", 940, 4), ("pumpkin", 990, 3),
            ("grave", 1250, 4), ("jack", 1320, 5), ("lamp", 1420, 4),
            ("pumpkin", 1480, 4), ("jack", 1560, 3), ("mushroom", 1640, 3), ("pumpkin", 1210, 3),
            ("witchcat", 800, 4, "walk"), ("cat", 1200, 4, "walk"),
            ("bat", 500, 4, "fly", 350), ("bat", 1300, 4, "fly", 250), ("bat", 900, 3, "fly", 500),
            ("ghost", 700, 4, "swim", 650), ("ghost", 1500, 3, "swim", 560),
            ("scene-owl", 1050, 4, "fly", 700),
        ],
    },
]


def _objects(park, sizes):
    out = []
    for i, item in enumerate(park["items"]):
        art_id, x, scale = item[:3]
        behavior = item[3] if len(item) > 3 else sizes[art_id][2]
        y = item[4] if len(item) > 4 else H - sizes[art_id][1] * scale     # standing on the ground
        out.append({"uid": "p%d" % (i + 1), "art": art_id, "x": x, "y": y,
                    "scale": scale, "behavior": behavior, "flip": False})
    return out


def build():
    """The pack as written to the .parkpack file."""
    pictures = list(art.builtin_by_id().values()) + ART
    sizes = {a["id"]: art.size_of(a) + (a.get("behavior", "stay"),) for a in pictures}
    parks = [{"name": park["name"], "width": W, "height": H, "objects": _objects(park, sizes),
              "weather": park["weather"], "weather_auto": False,
              "time_mode": park["time_mode"], "show_sky": park["show_sky"]} for park in PARKS]
    return {"format": "desktop-park-pack", "version": 1, "id": PACK_ID, "name": PACK_NAME,
            "pack_version": PACK_VERSION, "drawings": ART, "parks": parks}
