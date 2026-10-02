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


class SkyTests(unittest.TestCase):
    def test_sun_by_day_moon_by_night(self):
        self.assertEqual(daycycle.sky(at(6))[0], "sun")
        self.assertEqual(daycycle.sky(at(12))[0], "sun")
        self.assertEqual(daycycle.sky(at(21))[0], "moon")
        self.assertEqual(daycycle.sky(at(3))[0], "moon")
        # it travels left to right
        self.assertLess(daycycle.sky(at(8))[1], daycycle.sky(at(16))[1])
        self.assertLess(daycycle.sky(at(20))[1], daycycle.sky(at(4))[1])

    def test_arc_stays_in_the_top_of_the_screen(self):
        prev_x = -1
        for i in range(11):
            x, y, scale = daycycle.arc(i / 10, 1920, 1040)
            self.assertGreater(x, prev_x)
            prev_x = x
            self.assertTrue(0 <= y <= 1040 * 0.25)
            self.assertTrue(0 <= x - 8 * scale and x + 8 * scale <= 1920)   # never off the sides
        corner = daycycle.arc(0.0, 1920, 1040)
        noon = daycycle.arc(0.5, 1920, 1040)
        self.assertEqual(noon[1], 0)                 # at its peak, half off the top
        self.assertGreater(corner[1], 8 * corner[2])   # in the corner, fully on screen
        self.assertGreater(noon[2], corner[2])       # biggest in the middle

    def test_sky_setting_is_saved(self):
        self.assertTrue(store.clean({})["show_sky"])
        self.assertFalse(store.clean({"show_sky": False})["show_sky"])


class TintTests(unittest.TestCase):
    def test_day_is_untouched(self):
        self.assertEqual(daycycle.tint(0.0)[3], 0.0)

    def test_sunset_is_warm_and_night_is_blue(self):
        r, g, b, a = daycycle.tint(0.3)
        self.assertGreater(r, b)
        r, g, b, a = daycycle.tint(1.0)
        self.assertGreater(b, r)
        self.assertGreater(a, 0.4)

    def test_light_keeps_things_bright(self):
        self.assertLess(daycycle.tint(1.0, light=1.0)[3], daycycle.tint(1.0, light=0.0)[3] / 4)


class ClockTests(unittest.TestCase):
    def test_reads_the_time(self):
        a, b = art.clock_rows("09:05", "sun"), art.clock_rows("21:47", "moon")
        self.assertNotEqual(a, b)
        self.assertEqual(len({len(r) for r in a + b}), 1)
        self.assertEqual(len(a), len(b))
        self.assertEqual(daycycle.clock_text(at(7, 3)), "07:03")

    def test_clock_is_a_glowing_decoration(self):
        clock = [a for a in art.BUILTIN if a["id"] == "clock"][0]
        self.assertEqual(clock["kind"], "deco")
        self.assertIn("glow", clock)

    def test_library_updates_the_clock(self):
        try:
            import sprites                    # needs PySide6 (not installed in the CI test job)
        except ImportError:
            self.skipTest("PySide6 not installed")
        lib = sprites.Library([])
        lib.set_clock("23:59", "moon")
        self.assertEqual(lib.get("clock")["frames"][0], art.clock_rows("23:59", "moon"))


class LightTests(unittest.TestCase):
    def test_walkers_head_for_the_fire_at_night(self):
        w = World(2000, 500)
        w.night = 1.0
        w.lights = [(1500, 470, 60)]
        cat = Thing("cat", "x", 10, 8, scale=3, behavior="walk", x=200, y=500 - 24, is_pet=True)
        w.things.append(cat)
        rng = random.Random(5)
        for _ in range(int(90 / 0.05)):
            w.step(0.05, rng)
            if cat.reaction == "sleep":
                cat.reaction = None           # keep it awake for this test
        self.assertGreater(cat.x, 1000)       # it walked most of the way over

    def test_flyers_circle_the_lights(self):
        w = World(2000, 800)
        w.night = 1.0
        w.lights = [(1000, 600, 80)]
        bee = Thing("bee", "x", 10, 8, scale=3, behavior="fly", x=100, y=100, is_pet=True)
        w.things.append(bee)
        rng = random.Random(6)
        near = 0
        for _ in range(int(60 / 0.05)):
            w.step(0.05, rng)
            bee.reaction = None
            if abs(bee.x - 1000) < 200 and abs(bee.y - 600) < 200:
                near += 1
        self.assertGreater(near, 100)

    def test_light_level(self):
        w = World(1000, 500)
        w.lights = [(500, 400, 50)]
        self.assertGreater(w.light_at(500, 400), 0.9)
        self.assertEqual(w.light_at(100, 100), 0.0)


if __name__ == "__main__":
    unittest.main()
