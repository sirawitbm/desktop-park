import os, random, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import art, store
from sim import Thing, World, thing_at


class ArtTests(unittest.TestCase):
    def test_builtin_art_is_well_formed(self):
        for a in art.BUILTIN:
            w, h = art.size_of(a)
            for frame in a["frames"] + list(a.get("poses", {}).values()):
                self.assertEqual(len(frame), h, a["id"])
                for row in frame:
                    self.assertEqual(len(row), w, a["id"])
                    for ch in row:
                        self.assertTrue(ch == "." or ch in a["palette"], (a["id"], ch))
            self.assertIn(a["behavior"], art.BEHAVIORS)

    def test_polished_tree_sizes_and_walks(self):
        pictures = art.builtin_by_id()
        for art_id in ("tree", "cherry", "palm", "spookytree"):
            self.assertTrue(24 <= art.size_of(pictures[art_id])[1] <= 27, art_id)
        for art_id in ("cat", "dog", "duck"):
            self.assertEqual(len(pictures[art_id]["frames"]), 4)
            self.assertEqual(len({tuple(frame) for frame in pictures[art_id]["frames"]}), 4)
            self.assertIn("sleep", pictures[art_id]["poses"])

    def test_icons_have_rectangular_rows_and_palette_colors(self):
        for name, rows in {**art.WEATHER_ICONS, **art.UI_ICONS}.items():
            self.assertEqual(len({len(row) for row in rows}), 1, name)
            for row in rows:
                for character in row:
                    self.assertTrue(character == "." or character in art.WEATHER_ICON_PALETTE,
                                    (name, character))


class SimTests(unittest.TestCase):
    def world_with(self, behavior, **kw):
        w = World(800, 600)
        t = Thing("a", "x", 10, 8, scale=4, behavior=behavior, **kw)
        t.x, t.y = w.drop_spot(t, random.Random(1))
        w.things.append(t)
        return w, t

    def run_for(self, w, seconds, seed=0):
        rng = random.Random(seed)
        for _ in range(int(seconds / 0.033)):
            w.step(0.033, rng)

    def test_everything_stays_on_screen(self):
        for b in art.BEHAVIORS:
            w, t = self.world_with(b)
            for i in range(300):
                w.step(0.033, random.Random(i))
                self.assertTrue(0 <= t.x <= w.width - t.w, b)
                self.assertTrue(0 <= t.y <= w.ground - t.h, b)

    def test_walker_stays_on_ground_and_moves(self):
        w, t = self.world_with("walk")
        xs = set()
        for i in range(400):
            w.step(0.033, random.Random(i))
            self.assertAlmostEqual(t.y + t.h, w.ground, delta=0.6)
            xs.add(round(t.x))
        self.assertGreater(len(xs), 5)

    def test_dropped_walker_falls(self):
        w, t = self.world_with("walk")
        t.y = 50
        w.released(t)
        self.run_for(w, 2)
        self.assertAlmostEqual(t.y + t.h, w.ground, delta=0.6)

    def test_stay_does_not_move(self):
        w, t = self.world_with("stay")
        t.y = 100
        self.run_for(w, 3)
        self.assertEqual(t.y, 100)

    def test_swimmer_wanders(self):
        w, t = self.world_with("swim")
        start = (t.x, t.y)
        self.run_for(w, 8)
        self.assertNotEqual(start, (t.x, t.y))

    def test_love_makes_hearts_and_hop(self):
        w, t = self.world_with("walk")
        w.poke(t, random.Random(0), reaction="love")
        self.assertEqual([p[0] for p in w.particles], ["heart"] * 3)
        self.assertLess(t.vy, 0)
        self.run_for(w, 3)
        self.assertEqual(w.particles, [])

    def test_every_reaction_for_every_behavior(self):
        from sim import REACTIONS
        for b in art.BEHAVIORS:
            for r in REACTIONS:
                w, t = self.world_with(b)
                self.assertEqual(w.poke(t, random.Random(0), reaction=r), r)
                self.assertTrue(w.particles, (b, r))
                for i in range(200):
                    w.step(0.033, random.Random(i))
                    self.assertTrue(0 <= t.x <= w.width - t.w, (b, r))
                    self.assertTrue(0 <= t.y <= w.ground - t.h, (b, r))
                self.assertIsNone(t.reaction, (b, r))     # it ends

    def test_sleep_holds_still_and_snores(self):
        w, t = self.world_with("walk")
        w.poke(t, random.Random(0), reaction="sleep")
        x = t.x
        self.run_for(w, 2.5)
        self.assertEqual(t.x, x)
        self.assertIn("zzz", [p[0] for p in w.particles])

    def test_random_reactions_vary(self):
        w, t = self.world_with("walk")
        rng = random.Random(3)
        got = [w.poke(t, rng) for _ in range(30)]
        self.assertGreaterEqual(len(set(got)), 5)
        self.assertTrue(all(a != b for a, b in zip(got, got[1:])))   # never the same twice in a row

    def test_hit_test_ignores_see_through_pixels(self):
        t = Thing("a", "x", 2, 1, scale=10)
        # only the left art pixel is painted
        opaque = lambda th, ax, ay: ax == 0
        self.assertIs(thing_at([t], 5, 5, opaque), t)
        self.assertIsNone(thing_at([t], 15, 5, opaque))
        t.flip = True    # mirrored: now the right half is painted
        self.assertIsNone(thing_at([t], 5, 5, opaque))
        self.assertIs(thing_at([t], 15, 5, opaque), t)

    def test_frames_play_at_10fps_when_moving(self):
        t = Thing("a", "x", 4, 4, behavior="walk")
        t.vx, t.anim_t = 50, 0.0
        self.assertEqual(t.frame_index(2, True), 0)
        t.anim_t = 0.15
        self.assertEqual(t.frame_index(2, True), 1)
        t.vx = 0
        self.assertEqual(t.frame_index(2, True), 0)   # still pet: first frame

    def test_blink_is_brief_and_sleep_has_a_pose(self):
        thing = Thing("cat", "cat", 16, 10, is_pet=True)
        thing.age = 5.55
        self.assertEqual(thing.pose(), "blink")
        thing.age = 5.8
        self.assertIsNone(thing.pose())
        thing.reaction = "sleep"
        self.assertEqual(thing.pose(), "sleep")


class StoreTests(unittest.TestCase):
    def test_round_trip_and_bad_data(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "park.json")
            data = store.empty()
            data["custom_art"] = [{"id": "my-1", "name": "Frog", "kind": "pet", "behavior": "hop",
                                   "palette": {"a": "#00ff00"}, "frames": [["a.", ".a"]]}]
            data["objects"] = [{"uid": "t1", "art": "cat", "x": 10, "y": 20, "scale": 3,
                                "behavior": "walk", "flip": True}]
            store.save(data, p)
            store.save(data, p)
            back = store.load(p)
            self.assertEqual(back["custom_art"][0]["name"], "Frog")
            self.assertEqual(back["objects"][0]["scale"], 3)
            with open(p, "w") as f:
                f.write("{broken")
            self.assertEqual(store.load(p)["objects"][0]["art"], "cat")   # .bak saves us

    def test_clean_rejects_junk(self):
        d = store.clean({"objects": [{"art": "cat", "x": True, "scale": 99, "behavior": "teleport"}, "junk"],
                         "custom_art": [{"id": "x"}], "locked": "yes"})
        self.assertEqual(d["objects"][0]["x"], 0)
        self.assertEqual(d["objects"][0]["scale"], 12)
        self.assertEqual(d["objects"][0]["behavior"], "stay")
        self.assertEqual(d["custom_art"], [])
        self.assertFalse(d["locked"])

    def test_drawing_frames_share_a_rectangular_canvas(self):
        picture = store.clean_art({"id": "my-test", "palette": {"a": "#ffffff", "b": "#gggggg"},
                                   "frames": [["aa", "a"], ["a"], ["aab", "bb", "aa"]]})
        self.assertEqual(picture["frames"], [["aa", "a."], ["a.", ".."], ["aa", ".."]])
        self.assertEqual(picture["palette"], {"a": "#ffffff"})
        self.assertIsNone(store.clean_art({"id": "empty", "palette": {}, "frames": [[""]]}))

    def test_non_finite_coordinates_and_wrong_container_types(self):
        data = store.clean({"objects": [{"art": "cat", "x": float("nan"), "y": float("inf"),
                                         "scale": float("inf")}], "custom_art": 42})
        self.assertEqual((data["objects"][0]["x"], data["objects"][0]["y"],
                          data["objects"][0]["scale"]), (0, 0, 4))
        self.assertEqual(store.clean({"objects": 42})["objects"], [])

    def test_presets_validate_and_keep_unique_names(self):
        data = store.clean({"presets": [{"name": " Evening ", "width": float("inf"),
                                        "objects": [{"art": "cat", "scale": 3}], "weather": "snow"},
                                       {"name": "evening"}, {"name": ""}, 42]})
        self.assertEqual(len(data["presets"]), 1)
        preset = data["presets"][0]
        self.assertEqual(preset["name"], "Evening")
        self.assertEqual(preset["width"], 1920)
        self.assertEqual(preset["weather"], "snow")
        self.assertEqual(preset["objects"][0]["scale"], 3)

    def test_drawing_export_round_trip_and_wrong_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "drawing.parkart")
            picture = {"id": "my-test", "name": "Test", "kind": "pet", "behavior": "walk",
                       "palette": {"a": "#ffffff"}, "frames": [["aa", "aa"], ["a.", ".a"]]}
            store.export_drawing(picture, path)
            self.assertEqual(store.import_drawing(path), picture)
            store.save({"format": "unknown", "version": 1, "picture": picture}, path)
            with self.assertRaises(ValueError):
                store.import_drawing(path)


if __name__ == "__main__":
    unittest.main()
