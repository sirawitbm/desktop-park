"""Saving and loading the park.

- Running from source: the git-ignored `local/` folder next to the code.
- Portable exe (a `portable.flag` file beside it): `data/` beside the exe.
- Installed exe: %LOCALAPPDATA%\\DesktopPark.

Park packs (*.parkpack files, like the optional Theme Pack) are picked up
from a `packs` folder inside that folder (and beside the exe); their drawings
and parks are added once - see merge_pack().
"""

import json
import math
import os
import re
import sys

from art import BEHAVIORS, PIXEL_CHARS
from weather import KINDS as WEATHER_KINDS

APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))

MAX_PRESETS = 32
PACK_FORMAT = "desktop-park-pack"
PACK_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


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
    return {"version": 1, "custom_art": [], "objects": [], "presets": [], "board": {},
            "locked": False, "hidden": False, "seeded": False,
            "weather": "clear", "weather_auto": False, "skip_update": "", "screen": "", "theme": "modern",
            "time_mode": "clock", "show_sky": True, "low_power": False,
            "packs": {}}          # park packs already taken in: pack id -> pack version


def load(path=None):
    path = path or park_file()
    for candidate in (path, path + ".bak"):
        try:
            with open(candidate, encoding="utf-8") as f:
                raw = json.load(f)
            return clean(raw)
        except (OSError, ValueError, TypeError, AttributeError, RecursionError):
            # RecursionError: deeply nested JSON (a damaged or crafted file) - use the backup
            continue
    return empty()


def save(data, path=None):
    """Save the park: write a temporary file, keep the old file as .bak, then
    swap the new one in, so a crash mid-save can't leave half a file."""
    path = path or park_file()
    _write_json(data, path, backup=True)


def _write_json(data, path, backup):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        if backup and os.path.exists(path):
            try:
                os.replace(path, path + ".bak")
            except OSError:
                pass
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)                  # don't leave a half-written .tmp behind
        except OSError:
            pass
        raise


def _num(v, default=0):
    try:
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else default
    except OverflowError:
        return default


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
               and isinstance(v, str) and v.startswith("#") and len(v) == 7
               and all(ch in "0123456789abcdefABCDEF" for ch in v[1:])}
    good = []
    for fr in frames[:8]:
        if isinstance(fr, list) and fr and all(isinstance(r, str) for r in fr):
            good.append([r[:64] for r in fr[:64]])
    if not good:
        return None
    width = max((len(row) for row in good[0]), default=0)
    height = len(good[0])
    if not width:
        return None
    good = [["".join(ch if ch in palette else "." for ch in row[:width]).ljust(width, ".")
             for row in (frame + [""] * height)[:height]] for frame in good]
    behavior = a.get("behavior") if a.get("behavior") in BEHAVIORS else "stay"
    return {"id": a["id"], "name": str(a.get("name") or "My drawing")[:40],
            "kind": "pet" if a.get("kind") == "pet" else "deco",
            "behavior": behavior, "palette": palette, "frames": good}


def clean(raw):
    data = empty()
    if not isinstance(raw, dict):
        return data
    drawings = raw.get("custom_art")
    data["custom_art"] = [a for a in map(clean_art, drawings if isinstance(drawings, list) else []) if a]
    objs = []
    objects = raw.get("objects")
    for o in objects if isinstance(objects, list) else []:
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
    if raw.get("time_mode") in ("clock", "day", "night"):
        data["time_mode"] = raw["time_mode"]
    if raw.get("theme") in ("modern", "pixel"):
        data["theme"] = raw["theme"]
    if isinstance(raw.get("screen"), str):
        data["screen"] = raw["screen"][:100]
    if isinstance(raw.get("skip_update"), str):
        data["skip_update"] = raw["skip_update"][:20]
    for key in ("locked", "hidden", "seeded", "weather_auto", "low_power"):
        data[key] = raw.get(key) is True
    data["show_sky"] = raw.get("show_sky") is not False          # on unless turned off
    presets = raw.get("presets")
    names = set()
    for preset in presets[:MAX_PRESETS] if isinstance(presets, list) else []:
        preset = clean_preset(preset)
        if preset and preset["name"].casefold() not in names:
            names.add(preset["name"].casefold())
            data["presets"].append(preset)
    packs = raw.get("packs")
    if isinstance(packs, dict):
        data["packs"] = {k: v[:20] for k, v in list(packs.items())[:50]
                         if isinstance(k, str) and PACK_ID.match(k) and isinstance(v, str)}
    return data


def clean_preset(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
        return None
    name = raw["name"].strip()[:40]
    if not name:
        return None
    keys = ("objects", "weather", "weather_auto", "time_mode", "show_sky")
    state = clean({key: raw[key] for key in keys if key in raw})
    return {"name": name, "width": int(min(32768, max(1, _num(raw.get("width"), 1920)))),
            "height": int(min(32768, max(1, _num(raw.get("height"), 1040)))),
            **{key: state[key] for key in keys}}


def export_drawing(picture, path):
    picture = clean_art(picture)
    if picture is None:
        raise ValueError("This drawing has no valid frames.")
    # the user's own file: replace it safely, but leave no .bak or .tmp next to it
    _write_json({"format": "desktop-park-drawing", "version": 1, "picture": picture}, path, backup=False)


def import_drawing(path):
    if os.path.getsize(path) > 1024 * 1024:
        raise ValueError("Drawing files must be smaller than 1 MB.")
    try:
        with open(path, encoding="utf-8") as source:
            raw = json.load(source)
    except RecursionError:
        raise ValueError("This drawing file is damaged.") from None
    if (not isinstance(raw, dict) or raw.get("format") != "desktop-park-drawing"
            or raw.get("version") != 1):
        raise ValueError("This is not a supported Desktop Park drawing file.")
    picture = clean_art(raw.get("picture"))
    if picture is None:
        raise ValueError("This file contains no valid drawing.")
    return picture


# -- park packs ------------------------------------------------------------------
# A pack is a JSON file: {"format": "desktop-park-pack", "version": 1, "id": "theme-pack",
# "name": "Theme Pack", "pack_version": "1.0.0", "drawings": [...], "parks": [...]}.
# Drawings look like custom_art entries, parks like saved parks (presets).

def pack_dirs():
    """Where pack files are picked up: `packs` in the save folder, and beside the exe."""
    dirs = [os.path.join(data_dir(), "packs")]
    if getattr(sys, "frozen", False):
        dirs.append(os.path.join(APP_DIR, "packs"))
    return dirs


def read_pack(path):
    """A pack file, checked like everything else from disk. Raises ValueError."""
    if os.path.getsize(path) > 4 * 1024 * 1024:
        raise ValueError("Park packs must be smaller than 4 MB.")
    try:
        with open(path, encoding="utf-8") as source:
            raw = json.load(source)
    except RecursionError:
        raise ValueError("This park pack is damaged.") from None
    if not isinstance(raw, dict) or raw.get("format") != PACK_FORMAT or raw.get("version") != 1:
        raise ValueError("This is not a supported Desktop Park pack.")
    pack_id = raw.get("id")
    if not isinstance(pack_id, str) or not PACK_ID.match(pack_id):
        raise ValueError("This park pack has no valid id.")
    builtin = set(a["id"] for a in _builtin_art())
    drawings = []
    for picture in raw.get("drawings") if isinstance(raw.get("drawings"), list) else []:
        picture = clean_art(picture)
        # a pack may not replace the built-in art or your own drawings ("my-...")
        if picture and picture["id"] not in builtin and not picture["id"].startswith("my-"):
            drawings.append(picture)
    parks, names = [], set()
    for park in raw.get("parks") if isinstance(raw.get("parks"), list) else []:
        park = clean_preset(park)
        if park and park["name"].casefold() not in names:
            names.add(park["name"].casefold())
            parks.append(park)
    if not drawings and not parks:
        raise ValueError("This park pack is empty.")
    return {"id": pack_id, "name": str(raw.get("name") or pack_id)[:40],
            "pack_version": str(raw.get("pack_version") or "1")[:20],
            "drawings": drawings[:500], "parks": parks[:MAX_PRESETS]}


def _builtin_art():
    from art import BUILTIN
    return BUILTIN


def merge_pack(data, pack):
    """Add a pack's drawings and parks to the park data.

    Drawings with the same id are replaced (the pack owns its ids). Parks are
    only added under names that are free, so a park you changed or renamed to
    the same name is never overwritten. Returns (added park names, park names
    that did not fit under the saved-park limit)."""
    ids = {picture["id"] for picture in pack["drawings"]}
    data["custom_art"] = [a for a in data["custom_art"] if a["id"] not in ids] + list(pack["drawings"])
    names = {park["name"].casefold() for park in data["presets"]}
    added, skipped = [], []
    for park in pack["parks"]:
        if park["name"].casefold() in names:
            continue
        if len(data["presets"]) >= MAX_PRESETS:
            skipped.append(park["name"])
            continue
        data["presets"].append(park)
        names.add(park["name"].casefold())
        added.append(park["name"])
    data["packs"][pack["id"]] = pack["pack_version"]
    return added, skipped


def new_packs(data):
    """Pack files in the pack folders that this park hasn't taken in yet
    (new, or a newer version). Damaged files are skipped quietly."""
    found = {}
    for folder in pack_dirs():
        try:
            names = sorted(os.listdir(folder))
        except OSError:
            continue
        for name in names:
            if not name.lower().endswith(".parkpack"):
                continue
            try:
                pack = read_pack(os.path.join(folder, name))
            except (OSError, ValueError, TypeError, AttributeError):
                continue
            if data["packs"].get(pack["id"]) != pack["pack_version"]:
                found.setdefault(pack["id"], pack)
    return list(found.values())
