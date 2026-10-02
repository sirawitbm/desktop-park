import os, random, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store
from sim import Thing, World
from weather import MAX_PARTICLES, SNOW_MAX, Weather


def run(w, seconds, seed=0):
    rng = random.Random(seed)
    for _ in range(int(seconds / 0.05)):
        w.step(0.05, rng)


class WeatherTests(unittest.TestCase):
    def test_clear_is_quiet(self):
        w = Weather(1920, 1080)
        run(w, 5)
        self.assertEqual(w.particles, [])
        self.assertFalse(w.busy())

    def test_each_kind_makes_its_particles(self):
        expect = {"rain": "drop", "snow": "flake", "wind": "streak", "sun": "mote"}
        for kind, particle in expect.items():
            w = Weather(1920, 1080)
            w.set_kind(kind)
            run(w, 3)
            self.assertIn(particle, {p[0] for p in w.particles}, kind)
            self.assertTrue(w.busy())

    def test_rain_splashes_and_stays_capped(self):
        w = Weather(1920, 1080)
        w.set_kind("rain")
        run(w, 10)
        kinds = {p[0] for p in w.particles}
        self.assertIn("splash", kinds)
        self.assertLessEqual(len(w.particles), MAX_PARTICLES)

    def test_4k_rain_and_splashes_respect_the_particle_budget(self):
        weather = Weather(3840, 2080)
        weather.set_kind("rain")
        rng = random.Random(7)
        for _ in range(400):
            weather.step(0.05, rng)
            self.assertLessEqual(len(weather.particles), MAX_PARTICLES)
        self.assertIn("splash", {particle[0] for particle in weather.particles})

    def test_snow_piles_up_then_melts(self):
        w = Weather(400, 300)
        w.set_kind("snow")
        run(w, 240)
        self.assertGreater(max(w.snow), SNOW_MAX * 0.5)
        self.assertLessEqual(max(w.snow), SNOW_MAX)
        w.set_kind("clear")
        run(w, 20)
        self.assertEqual(max(w.snow), 0)

    def test_switching_off_lets_particles_finish(self):
        w = Weather(800, 600)
        w.set_kind("rain")
        run(w, 2)
        w.set_kind("clear")
        run(w, 5)
        self.assertEqual(w.particles, [])
        run(w, 15)                            # the rain clouds drift apart too
        self.assertFalse(w.busy())

    def test_wind_builds_up_gradually(self):
        w = Weather(800, 600)
        w.set_kind("wind")
        w.step(0.05)
        self.assertLess(w.wind, 50)
        run(w, 8)
        self.assertGreater(w.wind, 200)

    def test_auto_changes_the_weather(self):
        w = Weather(800, 600)
        w.set_auto(True, random.Random(1))
        seen = set()
        rng = random.Random(2)
        for _ in range(60):
            w.auto_timer = 0
            w.step(0.05, rng)
            seen.add(w.kind)
        self.assertGreaterEqual(len(seen), 4)

    def test_resize_keeps_snow(self):
        w = Weather(400, 300)
        w.snow[5] = 6
        w.resize(800, 300)
        self.assertEqual(w.snow[5], 6)
        self.assertEqual(len(w.snow), 800 // 4 + 1)

    def test_wind_pushes_flyers_not_walkers(self):
        world = World(2000, 600)
        bird = Thing("b", "x", 4, 4, behavior="fly", x=500, y=100)
        bird.state, bird.timer = "idle", 999       # hovering in place
        cat = Thing("c", "x", 4, 4, behavior="walk", x=500, y=600 - 16)
        cat.state, cat.timer = "idle", 999
        world.things += [bird, cat]
        world.wind = 200
        for _ in range(30):
            world.step(0.033)
        self.assertGreater(bird.x, 520)
        self.assertEqual(cat.x, 500)

    def test_weather_is_saved(self):
        d = store.clean({"weather": "snow", "weather_auto": True})
        self.assertEqual((d["weather"], d["weather_auto"]), ("snow", True))
        self.assertEqual(store.clean({"weather": "tornado"})["weather"], "clear")



class CloudTests(unittest.TestCase):
    def test_cover_follows_the_weather(self):
        w = Weather(1920, 1040)
        self.assertEqual(w.cover, 0.0)
        w.set_kind("rain")
        run(w, 15)
        self.assertGreater(w.cover, 0.5)
        self.assertGreater(w.gloom, 0.9)
        w.set_kind("wind")
        run(w, 15)
        self.assertTrue(0.15 < w.cover < 0.3)
        self.assertLess(w.gloom, 0.1)

    def test_how_many_clouds_show(self):
        w = Weather(1920, 1040)
        w.cover = 1.0
        self.assertTrue(all(w.cloud_alpha(i) == 1.0 for i in range(len(w.clouds))))
        w.cover = 0.0
        self.assertTrue(all(w.cloud_alpha(i) == 0.0 for i in range(len(w.clouds))))

    def test_clouds_stay_in_the_top_strip_and_drift(self):
        w = Weather(1920, 1040)
        w.set_kind("wind")
        xs = [c[0] for c in w.clouds]
        run(w, 10)
        self.assertNotEqual(xs, [c[0] for c in w.clouds])
        for c in w.clouds:
            self.assertLessEqual(c[1], 1040 * 0.2)
            self.assertTrue(-400 < c[0] < 1920 + 400)

    def test_sun_and_moon_dim_behind_clouds(self):
        w = Weather(800, 600)
        self.assertEqual(w.sky_strength(), 1.0)
        w.cover = 1.0
        self.assertTrue(0.2 < w.sky_strength() < 0.5)       # dim, but still there


if __name__ == "__main__":
    unittest.main()
