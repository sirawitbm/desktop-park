import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store
from sim import Thing, World


class RelocateTests(unittest.TestCase):
    def world(self):
        w = World(1920, 1040)
        cat = Thing("cat", "x", 10, 8, scale=4, behavior="walk", x=960 - 20, y=1040 - 32)
        bird = Thing("bird", "x", 10, 8, scale=4, behavior="fly", x=100, y=520)
        tree = Thing("tree", "x", 16, 18, scale=4, behavior="stay", x=1920 - 64, y=1040 - 72)
        w.things += [cat, bird, tree]
        return w, cat, bird, tree

    def test_bigger_screen(self):
        w, cat, bird, tree = self.world()
        w.relocate(2560, 1400)
        self.assertAlmostEqual(cat.x + cat.w / 2, 1280, delta=1)       # still in the middle
        self.assertEqual(cat.y + cat.h, 1400)                           # still on the ground
        self.assertEqual(tree.y + tree.h, 1400)
        self.assertLessEqual(tree.x + tree.w, 2560)
        self.assertAlmostEqual(bird.y, 520 / 1040 * 1400, delta=1)      # same height, in proportion

    def test_smaller_screen_keeps_everything_visible(self):
        w, cat, bird, tree = self.world()
        w.relocate(1280, 680)
        for t in (cat, bird, tree):
            self.assertTrue(0 <= t.x <= 1280 - t.w)
            self.assertTrue(0 <= t.y <= 680 - t.h)
        self.assertEqual(cat.y + cat.h, 680)

    def test_round_trip(self):
        w, cat, bird, tree = self.world()
        before = [(round(t.x), round(t.y)) for t in (cat, bird, tree)]
        w.relocate(2560, 1400)
        w.relocate(1920, 1040)
        after = [(round(t.x), round(t.y)) for t in (cat, bird, tree)]
        for (x1, y1), (x2, y2) in zip(before, after):
            self.assertAlmostEqual(x1, x2, delta=2)
            self.assertAlmostEqual(y1, y2, delta=2)

    def test_screen_choice_is_saved(self):
        self.assertEqual(store.clean({"screen": "\\.\DISPLAY2"})["screen"], "\\.\DISPLAY2")
        self.assertEqual(store.clean({"screen": 2})["screen"], "")


if __name__ == "__main__":
    unittest.main()
