"""Park packs (the optional Theme Pack): reading, merging, finding new ones.
Pure logic - no PySide6 needed, so these also run in the release job."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "packs"))

import art  # noqa: E402
import store  # noqa: E402
import theme_pack  # noqa: E402

DRAWING = {"id": "scene-dot", "name": "Dot", "kind": "deco", "behavior": "stay",
           "palette": {"a": "#ff0000"}, "frames": [["a"]]}


def park(name, art_id="tree"):
    return {"name": name, "width": 1920, "height": 1032, "weather": "snow", "weather_auto": False,
            "time_mode": "night", "show_sky": True,
            "objects": [{"uid": "p1", "art": art_id, "x": 10, "y": 1000, "scale": 4,
                         "behavior": "stay", "flip": False}]}


def pack(**changes):
    raw = {"format": "desktop-park-pack", "version": 1, "id": "test-pack", "name": "Test Pack",
           "pack_version": "1.0.0", "drawings": [DRAWING], "parks": [park("Snowy"), park("Dotty", "scene-dot")]}
    raw.update(changes)
    return raw


class PackTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def write(self, raw, name="test.parkpack", folder=None):
        folder = folder or self.dir
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw if isinstance(raw, str) else json.dumps(raw))
        return path

    def test_reads_a_valid_pack(self):
        result = store.read_pack(self.write(pack()))
        self.assertEqual((result["id"], result["name"], result["pack_version"]),
                         ("test-pack", "Test Pack", "1.0.0"))
        self.assertEqual([p["name"] for p in result["parks"]], ["Snowy", "Dotty"])
        self.assertEqual(result["parks"][0]["weather"], "snow")
        self.assertEqual(result["drawings"][0]["id"], "scene-dot")

    def test_rejects_files_that_are_not_packs(self):
        for raw in ("not json", "[" * 100000 + "]" * 100000, {"format": "desktop-park-drawing"},
                    pack(version=2), pack(id="Bad Id!"), pack(drawings=[], parks=[])):
            with self.subTest(raw=str(raw)[:40]):
                with self.assertRaises(ValueError):
                    store.read_pack(self.write(raw))

    def test_a_pack_cannot_replace_built_in_art_or_your_drawings(self):
        sneaky = [dict(DRAWING, id="cat"), dict(DRAWING, id="my-123")]
        result = store.read_pack(self.write(pack(drawings=sneaky + [DRAWING])))
        self.assertEqual([d["id"] for d in result["drawings"]], ["scene-dot"])

    def test_merge_adds_parks_and_drawings_once_and_never_overwrites_yours(self):
        data = store.empty()
        data["presets"] = [park("snowy")]                 # yours, same name (any case)
        data["presets"][0]["weather"] = "rain"
        data["custom_art"] = [dict(DRAWING, name="Old dot"), dict(DRAWING, id="my-1")]
        added, skipped = store.merge_pack(data, store.read_pack(self.write(pack())))
        self.assertEqual((added, skipped), (["Dotty"], []))
        self.assertEqual(data["presets"][0]["weather"], "rain")
        self.assertEqual(sorted(d["id"] for d in data["custom_art"]), ["my-1", "scene-dot"])
        self.assertEqual(next(d for d in data["custom_art"] if d["id"] == "scene-dot")["name"], "Dot")
        self.assertEqual(data["packs"], {"test-pack": "1.0.0"})

    def test_merge_stops_at_the_saved_park_limit(self):
        data = store.empty()
        data["presets"] = [park("Mine %d" % i) for i in range(store.MAX_PRESETS - 1)]
        added, skipped = store.merge_pack(data, store.read_pack(self.write(pack())))
        self.assertEqual((added, skipped), (["Snowy"], ["Dotty"]))
        self.assertEqual(len(data["presets"]), store.MAX_PRESETS)

    def test_new_packs_finds_only_packs_not_taken_in_yet(self):
        folder = os.path.join(self.dir, "packs")
        self.write(pack(), folder=folder)
        self.write("damaged", name="broken.parkpack", folder=folder)
        self.write(pack(id="other"), name="ignored.json", folder=folder)
        data = store.empty()
        with patch("store.pack_dirs", return_value=[folder, os.path.join(self.dir, "missing")]):
            self.assertEqual([p["id"] for p in store.new_packs(data)], ["test-pack"])
            data["packs"]["test-pack"] = "1.0.0"
            self.assertEqual(store.new_packs(data), [])
            data["packs"]["test-pack"] = "0.9.0"               # an updated pack comes in again
            self.assertEqual(len(store.new_packs(data)), 1)

    def test_taken_in_packs_survive_saving_and_loading(self):
        data = store.empty()
        data["packs"] = {"theme-pack": "1.0.0", "Bad Id": "1", "x": 5}
        path = os.path.join(self.dir, "park.json")
        store.save(data, path)
        self.assertEqual(store.load(path)["packs"], {"theme-pack": "1.0.0"})


class ThemePackTests(unittest.TestCase):
    def test_theme_pack_reads_back_whole(self):
        built = theme_pack.build()
        path = os.path.join(tempfile.mkdtemp(), "theme.parkpack")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(built, f)
        result = store.read_pack(path)
        self.assertEqual(len(result["drawings"]), len(built["drawings"]))
        self.assertEqual(len(result["parks"]), 7)
        self.assertEqual(result["drawings"], built["drawings"])

    def test_every_park_uses_known_pictures_and_stands_on_the_ground(self):
        built = theme_pack.build()
        pictures = {a["id"]: a for a in list(art.builtin_by_id().values()) + built["drawings"]}
        for p in built["parks"]:
            for obj in p["objects"]:
                with self.subTest(park=p["name"], art=obj["art"]):
                    self.assertIn(obj["art"], pictures)
                    w, h = art.size_of(pictures[obj["art"]])
                    self.assertLessEqual(obj["x"] + w * obj["scale"], p["width"] + w * obj["scale"])
                    if obj["behavior"] not in ("fly", "swim"):
                        self.assertEqual(obj["y"] + h * obj["scale"], p["height"])

    def test_pack_pictures_are_named_and_use_their_palette(self):
        for picture in theme_pack.build()["drawings"]:
            with self.subTest(picture=picture["id"]):
                self.assertTrue(picture["id"].startswith("scene-"))
                frames = picture["frames"]
                self.assertTrue(all(len(f) == len(frames[0]) for f in frames))
                for frame in frames:
                    self.assertEqual(len({len(row) for row in frame}), 1)
                    self.assertTrue(set("".join(frame)) <= set(picture["palette"]) | {"."})


if __name__ == "__main__":
    unittest.main()
