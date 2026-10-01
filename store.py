"""Saving and loading the park.

- Running from source: the git-ignored `local/` folder next to the code.
- Portable exe (a `portable.flag` file beside it): `data/` beside the exe.
- Installed exe: %LOCALAPPDATA%\\DesktopPark.
"""

import json
import os
import sys

from art import BEHAVIORS, PIXEL_CHARS
from weather import KINDS as WEATHER_KINDS

APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))


def data_dir():
    if not getattr(sys, "frozen", False):
        path = os.path.join(APP_DIR, "local")
    elif os.path.exists(os.path.join(APP_DIR, "portable.flag")):
        path = os.path.join(APP_DIR, "data")
    else:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "DesktopPark")
    os.makedirs(path, exist_ok=True)
    return path


def park_file():
    return os.path.join(data_dir(), "park.json")


def empty():
    return {"version": 1, "custom_art": [], "objects": [], "board": {},
            "locked": False, "hidden": False, "seeded": False,
            "weather": "clear", "weather_auto": False, "skip_update": ""}


def load(path=None):
    path = path or park_file()
    for candidate in (path, path + ".bak"):
        try:
            with open(candidate, encoding="utf-8") as f:
                raw = json.load(f)
            return clean(raw)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return empty()


def save(data, path=None):
    path = path or park_file()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    if os.path.exists(path):
        try:
            os.replace(path, path + ".bak")
        except OSError:
            pass
    os.replace(tmp, path)


def _num(v, default=0):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def clean_art(a):
    """A user drawing from disk, checked so a bad file can't crash the app."""
    if not isinstance(a, dict) or not isinstance(a.get("id"), str):
        return None
    palette = a.get("palette")
    frames = a.get("frames")
    if not isinstance(palette, dict) or not isinstance(frames, list) or not frames:
        return None
    palette = {k: v for k, v in palette.items()
               if isinstance(k, str) and len(k) == 1 and k in PIXEL_CHARS
               and isinstance(v, str) and v.startswith("#") and len(v) == 7}
    good = []
    for fr in frames[:8]:
        if isinstance(fr, list) and fr and all(isinstance(r, str) for r in fr):
            good.append([r[:64] for r in fr[:64]])
    if not good:
        return None
    behavior = a.get("behavior") if a.get("behavior") in BEHAVIORS else "stay"
    return {"id": a["id"], "name": str(a.get("name") or "My drawing")[:40],
            "kind": "pet" if a.get("kind") == "pet" else "deco",
            "behavior": behavior, "palette": palette, "frames": good}


def clean(raw):
    data = empty()
    if not isinstance(raw, dict):
        return data
    data["custom_art"] = [a for a in map(clean_art, raw.get("custom_art") or []) if a]
    objs = []
    for o in raw.get("objects") or []:
        if not isinstance(o, dict) or not isinstance(o.get("art"), str):
            continue
        objs.append({
            "uid": str(o.get("uid") or len(objs)),
            "art": o["art"],
            "x": _num(o.get("x")), "y": _num(o.get("y")),
            "scale": int(min(max(_num(o.get("scale"), 4), 1), 12)),
            "behavior": o.get("behavior") if o.get("behavior") in BEHAVIORS else "stay",
            "flip": o.get("flip") is True,
        })
    data["objects"] = objs
    board = raw.get("board") if isinstance(raw.get("board"), dict) else {}
    data["board"] = {k: _num(board.get(k)) for k in ("x", "y") if k in board}
    data["board"]["collapsed"] = board.get("collapsed") is True
    if raw.get("weather") in WEATHER_KINDS:
        data["weather"] = raw["weather"]
    if isinstance(raw.get("skip_update"), str):
        data["skip_update"] = raw["skip_update"][:20]
    for key in ("locked", "hidden", "seeded", "weather_auto"):
        data[key] = raw.get(key) is True
    return data
