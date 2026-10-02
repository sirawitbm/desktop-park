"""Built-in pixel art.

Every picture is rows of characters. Each character is one pixel and looks
up its colour in that picture's palette; "." is see-through. Pets have more
than one frame - the frames play in order to make the animation.

All art faces RIGHT. The app mirrors it when something moves left.
"""

BEHAVIORS = ("stay", "walk", "hop", "swim", "fly")
BEHAVIOR_LABELS = {
    "stay": "Stay still",
    "walk": "Walk on the ground",
    "hop": "Hop around",
    "swim": "Swim (float anywhere)",
    "fly": "Fly (fast, anywhere)",
}

# A picture: id, name, kind ("deco" or "pet"), the behaviour it starts with,
# palette, frames.
from art_pack import PAL, REDRAWN  # noqa: E402

# The original set, redrawn in v0.5 on the shared palette (art_pack.REDRAWN).
BUILTIN = [
    {"id": "tree", "name": "Tree", "kind": "deco", "behavior": "stay"},
    {"id": "pine", "name": "Pine", "kind": "deco", "behavior": "stay"},
    {"id": "bush", "name": "Bush", "kind": "deco", "behavior": "stay"},
    {"id": "rock", "name": "Rock", "kind": "deco", "behavior": "stay"},
    {"id": "flower", "name": "Flower", "kind": "deco", "behavior": "stay"},
    {"id": "grass", "name": "Grass", "kind": "deco", "behavior": "stay"},
    {"id": "mushroom", "name": "Mushroom", "kind": "deco", "behavior": "stay"},
    {"id": "seaweed", "name": "Seaweed", "kind": "deco", "behavior": "stay"},
    {"id": "castle", "name": "Castle", "kind": "deco", "behavior": "stay"},
    {"id": "fish", "name": "Fish", "kind": "pet", "behavior": "swim"},
    {"id": "cat", "name": "Cat", "kind": "pet", "behavior": "walk"},
    {"id": "slime", "name": "Slime", "kind": "pet", "behavior": "hop"},
    {"id": "bird", "name": "Bird", "kind": "pet", "behavior": "fly"},
]
for _a in BUILTIN:
    _a["palette"], _a["frames"] = PAL, REDRAWN[_a["id"]]

# Little pictures that pop out when you click a pet.
PARTICLES = {
    "heart": ({"r": "#ff4d6d", "w": "#ffd0da"}, [
        ".rr.rr.",
        "rwrrrrr",
        "rrrrrrr",
        ".rrrrr.",
        "..rrr..",
        "...r...",
    ]),
    "star": ({"y": "#ffcd4f", "w": "#fff1a8"}, [
        "...y...",
        "..ywy..",
        "yywwwyy",
        ".ywwwy.",
        ".yy.yy.",
        "y.....y",
    ]),
    "sparkle": ({"w": "#ffffff", "c": "#73eff7"}, [
        "...w...",
        "...c...",
        "wcc.ccw",
        "...c...",
        "...w...",
    ]),
    "note": ({"k": "#1a1c2c", "v": "#8a4fc0"}, [
        "..vvv.",
        "..v.vv",
        "..v..v",
        "..v...",
        "vvv...",
        "vvv...",
    ]),
    "zzz": ({"b": "#73a6f6", "w": "#c9f1ff"}, [
        "wwww.....",
        "..b......",
        ".b...bbb.",
        "bbbb...b.",
        ".....b...",
        ".....bbbb",
    ]),
    "bang": ({"r": "#d6404e", "w": "#ffcdd2"}, [
        ".rr.",
        ".rw.",
        ".rr.",
        ".rr.",
        "....",
        ".rr.",
    ]),
    "drop": ({"c": "#41a6f6", "w": "#c9f1ff"}, [
        "..c..",
        ".ccc.",
        "cwccc",
        "cwccc",
        ".ccc.",
    ]),
}


# Icons for the weather buttons on the board.
WEATHER_ICON_PALETTE = {"y": "#ffcd4f", "Y": "#fff1a8", "w": "#f4f4f4",
                        "S": "#94b0c2", "c": "#41a6f6", "C": "#73eff7",
                        "k": "#1a1c2c", "p": "#ff8a9a", "e": "#e8c48c", "r": "#b13e53",
                        "G": "#38b764", "l": "#a7f070"}
WEATHER_ICONS = {
    "clear": [
        "..SSSSS..",
        ".S....SS.",
        "S....S..S",
        "S...S...S",
        "S..S....S",
        "S.S.....S",
        ".SS....S.",
        "..SSSSS..",
        ".........",
    ],
    "sun": [
        "yYy......",
        "YYY.y....",
        "yYy..y...",
        ".y....y..",
        "..y....y.",
        "...y....y",
        "..y.y....",
        "....y.y..",
        ".....y..y",
    ],
    "rain": [
        "..www....",
        ".wwwwww..",
        "wwwwwwwww",
        ".SSSSSSS.",
        ".........",
        "..c..c..c",
        ".c..c..c.",
        ".........",
        ".c..c..c.",
    ],
    "snow": [
        "....w....",
        ".w..w..w.",
        "..w.C.w..",
        "...wCw...",
        "wwCCwCCww",
        "...wCw...",
        "..w.C.w..",
        ".w..w..w.",
        "....w....",
    ],
    "wind": [
        ".....ww..",
        "......w..",
        "wwwwwww..",
        ".........",
        "SSSSSSSSS",
        "........S",
        "wwwww..S.",
        "....w....",
        "...w.....",
    ],
}

# Icons for the folded board's quick buttons (same palette as the weather ones).
UI_ICONS = {
    "eco": [
        "......GG.",
        "....GllG.",
        "...GlllG.",
        "..GllGlG.",
        ".GllGllG.",
        ".GlGllG..",
        ".GGllG...",
        "..GGG....",
        ".G.......",
    ],
    "day": [
        "....y....",
        ".y.....y.",
        "...yyy...",
        "..yYYYy..",
        "y.yYYYy.y",
        "..yYYYy..",
        "...yyy...",
        ".y.....y.",
        "....y....",
    ],
    "clock": [
        "..wwwww..",
        ".w.....w.",
        "w...y...w",
        "w...y...w",
        "w...yyy.w",
        "w.......w",
        "w.......w",
        ".w.....w.",
        "..wwwww..",
    ],
    "moon": [
        "...wwww..",
        "..ww.....",
        ".ww......",
        ".ww......",
        ".ww......",
        ".ww......",
        ".ww......",
        "..ww.....",
        "...wwww..",
    ],
    "sky": [
        "y.y......",
        ".yyy.....",
        "yyyyy....",
        ".yyy.....",
        "y.y...ww.",
        ".....ww..",
        ".....ww..",
        ".....ww..",
        "......ww.",
    ],
    "pencil": [
        ".......pp",
        "......ypp",
        ".....yyy.",
        "....yyy..",
        "...yyy...",
        "..yyy....",
        ".eey.....",
        ".ke......",
        "k........",
    ],
    "trash": [
        "...www...",
        "wwwwwwwww",
        ".........",
        ".wSwSwSw.",
        ".wSwSwSw.",
        ".wSwSwSw.",
        ".wSwSwSw.",
        ".wwwwwww.",
        ".........",
    ],
    "screen": [
        "wwwwwwwww",
        "wcccccccw",
        "wcCcccccw",
        "wcccccccw",
        "wcccccccw",
        "wwwwwwwww",
        "....w....",
        "..wwwww..",
        ".........",
    ],
    "min": [
        ".......",
        ".......",
        ".......",
        "wwwwwww",
        "wwwwwww",
        ".......",
        ".......",
    ],
    "up": [
        ".......",
        "...w...",
        "..www..",
        ".wwwww.",
        "wwwwwww",
        ".......",
        ".......",
    ],
    "close": [
        ".......",
        "ww...ww",
        ".ww.ww.",
        "..www..",
        ".ww.ww.",
        "ww...ww",
        ".......",
    ],
    "eye": [
        ".........",
        ".........",
        "..wwwww..",
        ".ww.C.ww.",
        "ww.CkC.ww",
        ".ww.C.ww.",
        "..wwwww..",
        ".........",
        ".........",
    ],
    "lock": [
        "..SSSSS..",
        ".S.....S.",
        ".S.....S.",
        "yyyyyyyyy",
        "yyyyyyyyy",
        "yyyyYyyyy",
        "yyyyYyyyy",
        "yyyyyyyyy",
        ".........",
    ],
}

# Colours offered in the drawing editor (PICO-8-ish, plus a few naturals).
EDITOR_COLORS = [
    "#000000", "#1d2b53", "#7e2553", "#008751", "#ab5236", "#5f574f",
    "#c2c3c7", "#fff1e8", "#ff004d", "#ffa300", "#ffec27", "#00e436",
    "#29adff", "#83769c", "#ff77a8", "#ffccaa", "#3b2a1e", "#8a5530",
    "#2d6a3e", "#4caf50", "#8bd06a", "#4a4f5a", "#8a919c", "#ffffff",
]

# Characters used to store pixels of user drawings ("." means see-through).
PIXEL_CHARS = ("abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&*+-=?@^~")


def size_of(art):
    frame = art["frames"][0]
    return (max(len(r) for r in frame) if frame else 0), len(frame)


def builtin_by_id():
    return {a["id"]: dict(a, builtin=True) for a in BUILTIN}


from art_pack import GLOWS, HALLOWEEN, PACK, POSES, WALKS  # noqa: E402  (the bigger shared-palette set)

BUILTIN += PACK + HALLOWEEN
for _a in BUILTIN:
    if _a["id"] in REDRAWN:                     # resized / redrawn in v0.5
        _a["frames"] = REDRAWN[_a["id"]]
    if _a["id"] in GLOWS:
        _a["glow"] = GLOWS[_a["id"]]
    if _a["id"] in WALKS:
        _a["frames"] = WALKS[_a["id"]]
    if _a["id"] in POSES:
        _a["poses"] = POSES[_a["id"]]


# -- the clock decoration: shows the real time ---------------------------------
DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
    ":": [".", "#", ".", "#", "."],
}
CLOCK_ICONS = {
    "sun": ["y.y", ".y.", "yYy", ".y.", "y.y"],
    "moon": [".ww", "ww.", "ww.", "ww.", ".ww"],
}
CLOCK_PALETTE = {"k": "#1a1c2c", "K": "#566c86", "s": "#94b0c2", "u": "#1f2a52",
                 "y": "#ffcd4f", "Y": "#fff1a8", "w": "#e8eeff"}


def clock_rows(text="12:00", body="sun"):
    """A little pixel digital clock reading `text` (HH:MM), with a sun or
    moon icon. 25 x 10 art pixels (v0.5: slimmer, so it isn't the biggest
    thing in the park)."""
    w, h = 25, 10
    g = [["."] * w for _ in range(h)]
    for y in range(9):
        for x in range(w):
            if y in (0, 8) or x in (0, w - 1):
                g[y][x] = "k"
            elif y == 1:
                g[y][x] = "s"                      # light catching the top edge
            else:
                g[y][x] = "u"
    for x in (3, 4, 20, 21):                       # little feet
        g[9][x] = "k"

    def stamp(rows, x0, colour):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    g[2 + dy][x0 + dx] = colour if ch == "#" else ch

    stamp(CLOCK_ICONS.get(body, CLOCK_ICONS["sun"]), 2, "y")
    x = 6
    for ch in text[:5]:
        glyph = DIGITS.get(ch, DIGITS["0"])
        stamp(glyph, x, "y")
        x += len(glyph[0]) + 1
    return ["".join(r) for r in g]


CLOCK = {"id": "clock", "name": "Clock", "kind": "deco", "behavior": "stay",
         "palette": CLOCK_PALETTE, "frames": [clock_rows()], "dynamic": "clock",
         "glow": ("#ffcd4f", 7, (0.55, 0.45), False)}
BUILTIN.append(CLOCK)


# -- the app icon: a little park tile (sky, sun, a tree on grass), 16 x 16 ------------
# Drawn for 16 px (the tray) and scaled by whole pixels for bigger sizes.
APP_ICON = [
    "..kkkkkkkkkkkk..",
    ".kccccccccckyyk.",
    "kcccccccccckyYyk",
    "kcCCcccccccckyyk",
    "kccccckkkcccckkk",
    "kcccckGGGkccccck",
    "kccckGlGGGkccCck",
    "kccckGGGGgkcccck",
    "kccckgGGggkcccck",
    "kcccckkbkkccccck",
    "kccccckbkcccccck",
    "kGGGGGGbGGGGGGGk",
    "kGlGGGGGGGlGGGGk",
    "kgGGGGGGGGGGGGgk",
    ".kggggggggggggk.",
    "..kkkkkkkkkkkk..",
]
