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
BUILTIN = [
    {
        "id": "tree", "name": "Tree", "kind": "deco", "behavior": "stay",
        "palette": {"g": "#2d6a3e", "G": "#4caf50", "l": "#8bd06a",
                    "b": "#8a5530", "d": "#5a3418"},
        "frames": [[
            "......gggg......",
            "....ggGGGGgg....",
            "...gGGGlGGGGg...",
            "..gGGlllGGGGGg..",
            "..gGGGlGGGGlGg..",
            ".gGGGGGGGGlllGg.",
            ".gGlGGGGGGGlGGg.",
            ".gGllGGGGGGGGGg.",
            ".ggGlGGGGlGGGgg.",
            "..gGGGGGlllGGg..",
            "..ggGGGGGlGGgg..",
            "...gggGGGGggg...",
            ".....ggbdgg.....",
            ".......bd.......",
            ".......bd.......",
            ".......bd.......",
            "......bbdd......",
            ".....bb..dd.....",
        ]],
    },
    {
        "id": "pine", "name": "Pine", "kind": "deco", "behavior": "stay",
        "palette": {"g": "#1f5236", "G": "#2f7d4f", "l": "#5fb37a",
                    "b": "#6b4024"},
        "frames": [[
            ".......g.......",
            "......gGg......",
            ".....gGlGg.....",
            "....gGGGlGg....",
            "......gGg......",
            ".....gGGlg.....",
            "....gGGGGlg....",
            "...gGlGGGGGg...",
            ".....gGGGg.....",
            "....gGGGGlg....",
            "...gGGlGGGGg...",
            "..gGGGGGGlGGg..",
            ".gggggggggggg..",
            "......bbb......",
            "......bbb......",
        ]],
    },
    {
        "id": "bush", "name": "Bush", "kind": "deco", "behavior": "stay",
        "palette": {"g": "#2d6a3e", "G": "#4caf50", "l": "#8bd06a",
                    "r": "#e04b3f"},
        "frames": [[
            "....gggg.ggg....",
            "..ggGGGGgGGGgg..",
            ".gGGlGGGGGlGGGg.",
            "gGGllGrGGGGGrGGg",
            "gGGGGGGGGlGGGGGg",
            "gGrGGGGGlllGGGGg",
            ".gGGGlGGGGGGGrg.",
            "..gggggggggggg..",
        ]],
    },
    {
        "id": "rock", "name": "Rock", "kind": "deco", "behavior": "stay",
        "palette": {"k": "#4a4f5a", "K": "#8a919c", "w": "#c3c9d2",
                    "d": "#636a75"},
        "frames": [[
            "....kkkkk...",
            "..kkKKKKKkk.",
            ".kKKwwKKKKk.",
            "kKKwKKKKKKKk",
            "kKKKKKKKKKdk",
            "kdKKKKKKKddk",
            ".kkddddddkk.",
        ]],
    },
    {
        "id": "flower", "name": "Flower", "kind": "deco", "behavior": "stay",
        "palette": {"p": "#e05a8a", "P": "#ff8fb5", "y": "#ffd84a",
                    "g": "#3f8f3f", "l": "#6cc24a"},
        "frames": [[
            "..ppp..",
            ".pPyPp.",
            "..ppp..",
            "...g...",
            ".l.g...",
            "..lg.l.",
            "...gl..",
            "...g...",
        ]],
    },
    {
        "id": "grass", "name": "Grass", "kind": "deco", "behavior": "stay",
        "palette": {"g": "#3f8f3f", "l": "#6cc24a"},
        "frames": [[
            "...l....l.",
            ".l.gl..lg.",
            ".gl.g.lg.l",
            "lgg.glgg.g",
            "gggggggggg",
        ]],
    },
    {
        "id": "mushroom", "name": "Mushroom", "kind": "deco", "behavior": "stay",
        "palette": {"r": "#b8322f", "R": "#e04b3f", "w": "#ffffff",
                    "c": "#f1e3c6", "C": "#d9c49c"},
        "frames": [[
            "...rrrr...",
            ".rrRwRRrr.",
            "rRwRRRwRRr",
            "rRRRRRRRwr",
            "rrrrrrrrrr",
            "...cccc...",
            "...cCcc...",
            "...ccCc...",
            "..cccccc..",
        ]],
    },
    {
        "id": "seaweed", "name": "Seaweed", "kind": "deco", "behavior": "stay",
        "palette": {"g": "#1e7a4c", "G": "#3fbf7a"},
        "frames": [
            [
                "..g.....",
                "..gG....",
                "...gG...",
                "...gG.g.",
                "..gG..gG",
                "..gG.gG.",
                "...gGgG.",
                "...gGgG.",
                "..gG.gG.",
                "..gG..gG",
                "...gG.gG",
                "...gGgG.",
            ],
            [
                "...g....",
                "...gG...",
                "..gG....",
                "..gG..g.",
                "...gG.gG",
                "...gGgG.",
                "..gG.gG.",
                "..gG..gG",
                "...gG.gG",
                "...gGgG.",
                "..gG.gG.",
                "...gGgG.",
            ],
        ],
    },
    {
        "id": "castle", "name": "Castle", "kind": "deco", "behavior": "stay",
        "palette": {"k": "#5b5f6e", "K": "#9aa0b0", "w": "#c9cede",
                    "d": "#2a2c36", "f": "#e04b3f"},
        "frames": [[
            "..........f.....",
            "..........ff....",
            "..........k.....",
            "k.k.k....kKk....",
            "kKKKk....kKk....",
            "kKdKk.k.kKKKk.k.",
            "kKKKkkKkKKKKKkKk",
            "kKKKKKKKKKdKKKKk",
            "kKwKKKKKKKKKKwKk",
            "kKKKKKdddKKKKKKk",
            "kKKKKdddddKKKKKk",
            "kKKKKdddddKKKKKk",
            "kkkkkdddddkkkkkk",
        ]],
    },
    {
        "id": "fish", "name": "Fish", "kind": "pet", "behavior": "swim",
        "palette": {"d": "#c85a14", "o": "#ff8a2a", "O": "#ffb25a",
                    "w": "#ffffff", "e": "#1a1a1a"},
        "frames": [
            [
                "....dddd....",
                "d..doOOOod..",
                "dddoOOOOOwd.",
                "ddooOOOOOeod",
                "dddoOOOOOOd.",
                "d..dooooodd.",
                "....dddd....",
            ],
            [
                "....dddd....",
                "...doOOOod..",
                ".ddoOOOOOwd.",
                "dddoOOOOOeod",
                ".ddoOOOOOOd.",
                "...dooooodd.",
                "....dddd....",
            ],
        ],
    },
    {
        "id": "cat", "name": "Cat", "kind": "pet", "behavior": "walk",
        "palette": {"k": "#3b2a1e", "c": "#e8a04a", "C": "#f5c27a",
                    "e": "#1a1a1a", "p": "#ff9fb0"},
        "frames": [
            [
                "..........k...k.",
                "k.........kk.kk.",
                "kc........kcccck",
                ".kc.......kcecek",
                ".kc.kkkkkkkCCpCk",
                "..kccccccccckkk.",
                "..kcCcccCcccck..",
                "..kcccccccccck..",
                "...kck.kck.kck..",
                "...kk..kk..kk...",
            ],
            [
                "..........k...k.",
                "..........kk.kk.",
                "k.........kcccck",
                "kc........kcecek",
                ".kc.kkkkkkkCCpCk",
                "..kccccccccckkk.",
                "..kcCcccCcccck..",
                "..kcccccccccck..",
                "..kck..kck..kck.",
                "..kk...kk....kk.",
            ],
        ],
    },
    {
        "id": "slime", "name": "Slime", "kind": "pet", "behavior": "hop",
        "palette": {"k": "#1f6b3a", "g": "#4fd27a", "l": "#b8f5c8",
                    "e": "#123320"},
        "frames": [
            [
                "............",
                "....kkkk....",
                "..kkggggkk..",
                ".kglgggggek.",
                ".kgllggggek.",
                "kgggggggggk.",
                "kgggggggggk.",
                ".kkkkkkkkk..",
            ],
            [
                "............",
                "............",
                "............",
                "...kkkkkk...",
                ".kkglgggekk.",
                "kgglggggggek",
                "kggggggggggk",
                "kkkkkkkkkkkk",
            ],
        ],
    },
    {
        "id": "bird", "name": "Bird", "kind": "pet", "behavior": "fly",
        "palette": {"k": "#1d3557", "b": "#4a90d9", "B": "#9cc9f5",
                    "y": "#ffc93c", "e": "#111111"},
        "frames": [
            [
                "...kk.......",
                "...kbk......",
                "....kbk.kk..",
                "..kkbbbkbek.",
                ".kbbbbBBbbyy",
                "kbbbbBBBbk..",
                ".kkkkkkkk...",
            ],
            [
                "............",
                "............",
                "........kk..",
                "..kkkkkkbek.",
                ".kbbbbBBbbyy",
                "kbbbkbBBbk..",
                ".kkkbbkkk...",
            ],
        ],
    },
]

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
                        "k": "#1a1c2c", "p": "#ff8a9a", "e": "#e8c48c", "r": "#b13e53"}
WEATHER_ICONS = {
    "clear": [
        ".........",
        ".........",
        "...SSS...",
        "..SSSSS..",
        ".SSSSSSSS",
        "SSSSSSSSS",
        ".SSSSSSS.",
        ".........",
        ".........",
    ],
    "sun": [
        "...yYy...",
        "...yyy...",
        "..y.y.y..",
        "..y.y.y..",
        ".y..y..y.",
        ".y..y..y.",
        "y...y...y",
        "y...y...y",
        ".........",
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
        "..wwwww..",
        ".w.....w.",
        "w..ccc..w",
        "w..cCc..w",
        "w..ccc..w",
        ".w.....w.",
        "..wwwww..",
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


from art_pack import GLOWS, HALLOWEEN, PACK  # noqa: E402  (the bigger shared-palette set)

BUILTIN += PACK + HALLOWEEN
for _a in BUILTIN:
    if _a["id"] in GLOWS:
        _a["glow"] = GLOWS[_a["id"]]


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
    "sun": [".y.y.", "..y..", "yyyyy", "..y..", ".y.y."],
    "moon": [".ww..", "ww...", "ww...", "ww...", ".ww.."],
}
CLOCK_PALETTE = {"k": "#1a1c2c", "K": "#566c86", "s": "#94b0c2", "u": "#1f2a52",
                 "y": "#ffcd4f", "w": "#e8eeff"}


def clock_rows(text="12:00", body="sun"):
    """A little pixel digital clock reading `text` (HH:MM), with a sun or
    moon icon. 29 x 12 art pixels."""
    w, h = 29, 12
    g = [["."] * w for _ in range(h)]
    for y in range(11):
        for x in range(w):
            if y in (0, 10) or x in (0, w - 1):
                g[y][x] = "k"
            elif y == 1:
                g[y][x] = "s"                      # light catching the top edge
            elif y == 9 or x in (1, w - 2):
                g[y][x] = "K"
            else:
                g[y][x] = "u"
    for x in (4, 5, 23, 24):                       # little feet
        g[11][x] = "k"

    def stamp(rows, x0, colour):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    g[3 + dy][x0 + dx] = colour if ch == "#" else ch

    stamp(CLOCK_ICONS.get(body, CLOCK_ICONS["sun"]), 3, "y")
    x = 9
    for ch in text[:5]:
        glyph = DIGITS.get(ch, DIGITS["0"])
        stamp(glyph, x, "y")
        x += len(glyph[0]) + 1
    return ["".join(r) for r in g]


CLOCK = {"id": "clock", "name": "Clock", "kind": "deco", "behavior": "stay",
         "palette": CLOCK_PALETTE, "frames": [clock_rows()], "dynamic": "clock",
         "glow": ("#ffcd4f", 7, (0.55, 0.45), False)}
BUILTIN.append(CLOCK)
