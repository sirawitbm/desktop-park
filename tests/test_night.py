import datetime
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import art
import daycycle
import store
from sim import Thing, World
from weather import FIREFLIES, Weather


def at(h, m=0):
    return datetime.datetime(2026, 10, 2, h, m)


class DayCycleTests(unittest.TestCase):
    def test_levels_through_the_day(self):
        self.assertEqual(daycycle.night_level(at(12)), 0.0)
        self.assertEqual(daycycle.night_level(at(23)), 1.0)
        self.assertEqual(daycycle.night_level(at(3)), 1.0)
        dusk = daycycle.night_level(at(18, 45))
        dawn = daycycle.night_level(at(6, 15))
        self.assertTrue(0.2 < dusk < 0.8 and 0.2 < dawn < 0.8)
        self.assertLess(daycycle.night_level(at(18, 10)), daycycle.night_level(at(19, 20)))

    def test_modes(self):
        self.assertEqual(daycycle.night_level(at(12), "night"), 1.0)
        self.assertEqual(daycycle.night_level(at(23), "day"), 0.0)

    def test_halloween_season(self):
        self.assertTrue(daycycle.is_halloween_season(datetime.date(2026, 10, 31)))
        self.assertFalse(daycycle.is_halloween_season(datetime.date(2026, 11, 1)))

    def test_time_mode_is_saved(self):
        self.assertEqual(store.clean({"time_mode": "night"})["time_mode"], "night")
        self.assertEqual(store.clean({"time_mode": "dusk"})["time_mode"], "clock")


class NapTests(unittest.TestCase):
    def world(self, night):
        w = World(1000, 500)
        w.night = night
        cat = Thing("cat", "x", 10, 8, scale=3, behavior="walk", x=400, y=500 - 24, is_pet=True)
        tree = Thing("tree", "x", 10, 8, scale=3, behavior="walk", x=100, y=500 - 24)   # not a pet
        w.things += [cat, tree]
        return w, cat, tree

    def naps_in(self, night, seconds=120):
        w, cat, tree = self.world(night)
        rng = random.Random(4)
        slept = tree_slept = False
        for _ in range(int(seconds / 0.05)):
            w.step(0.05, rng)
            slept |= cat.reaction == "sleep"
            tree_slept |= tree.reaction == "sleep"
        return slept, tree_slept

    def test_pets_nap_at_night(self):
        slept, tree_slept = self.naps_in(1.0)
        self.assertTrue(slept)
        self.assertFalse(tree_slept)          # decorations never nap

    def test_no_naps_in_the_day(self):
        self.assertEqual(self.naps_in(0.0), (False, False))

    def test_napping_pet_snores_and_stays_put(self):
        w, cat, _ = self.world(1.0)
        w.nap(cat, random.Random(1))
        x = cat.x
        for _ in range(60):
            w.step(0.05, random.Random(2))
        self.assertEqual(cat.x, x)
        self.assertIn("zzz", [p[0] for p in w.particles])


class FireflyTests(unittest.TestCase):
    def run_weather(self, kind, night, seconds=20):
        w = Weather(1920, 1040)
        w.set_kind(kind)
        w.night = night
        rng = random.Random(3)
        for _ in range(int(seconds / 0.05)):
            w.step(0.05, rng)
        return [p for p in w.particles if p[0] == "firefly"]

    def test_fireflies_at_night(self):
        flies = self.run_weather("clear", 1.0)
        self.assertTrue(flies)
        self.assertLessEqual(len(flies), FIREFLIES)
        self.assertTrue(all(p[2] > 1040 * 0.4 for p in flies))     # down near the plants

    def test_no_fireflies_by_day_or_in_rain(self):
        self.assertEqual(self.run_weather("clear", 0.0), [])
        self.assertEqual(self.run_weather("rain", 1.0), [])

    def test_night_keeps_the_weather_window_busy(self):
        w = Weather(800, 600)
        self.assertFalse(w.busy())
        w.night = 1.0
        self.assertTrue(w.busy())


class HalloweenArtTests(unittest.TestCase):
    def test_set_is_complete(self):
        ids = {a["id"] for a in art.BUILTIN if a.get("set") == "halloween"}
        self.assertEqual(ids, {"bat", "witchcat", "jack", "spookytree", "grave", "cauldron"})

    def test_glow_points_are_inside_the_picture(self):
        for a in art.BUILTIN:
            if "glow" in a:
                colour, radius, (fx, fy), _ = a["glow"]
                self.assertTrue(0 <= fx <= 1 and 0 <= fy <= 1, a["id"])
                self.assertTrue(colour.startswith("#") and radius > 0, a["id"])


if __name__ == "__main__":
    unittest.main()
