"""Weather: sun rays, rain, snow and wind. Pure logic - no windows - so it
can be tested. weather_window.py draws it.

Coordinates are screen pixels; the ground is the bottom edge.
"""

import math
import random

KINDS = ("clear", "sun", "rain", "snow", "wind")
LABELS = {"clear": "Clear", "sun": "Sunny", "rain": "Rain", "snow": "Snow", "wind": "Windy"}

MAX_PARTICLES = 700
FIREFLIES = 26           # at most this many on a 1920-pixel-wide screen
SNOW_CELL = 4            # snow piles up in columns this many pixels wide
SNOW_MAX = 16            # tallest the pile gets, in pixels
AUTO_MIN, AUTO_MAX = 4 * 60, 10 * 60     # auto mode changes every 4-10 minutes

# How fast new things appear, per second, on a 1920-pixel-wide screen.
SPAWN = {
    "rain": {"drop": 260.0},
    "snow": {"flake": 45.0},
    "wind": {"streak": 7.0, "leaf": 6.0},
    "sun": {"mote": 3.0},
}
# The wind each weather blows with (px/s, positive = to the right).
WIND = {"clear": 0.0, "sun": 0.0, "rain": 70.0, "snow": 25.0, "wind": 260.0}


class Weather:
    def __init__(self, width=1, height=1):
        self.width, self.height = width, height
        self.kind = "clear"
        self.particles = []          # [kind, x, y, vx, vy, life, seed]
        self.snow = []               # pile height per column
        self.wind = 0.0              # current wind, eases toward the target
        self.sun = 0.0               # 0..1, sun rays fade in and out
        self.t = 0.0
        self.night = 0.0             # 0 day .. 1 night (daycycle.py): fireflies, glows
        self.glows = []              # [(x, y, radius, colour, flickers)] lights in the park
        self.auto = False
        self.auto_timer = 0.0
        self._spawn_debt = {}
        self.resize(width, height)

    def resize(self, width, height):
        self.width, self.height = max(1, width), max(1, height)
        cols = self.width // SNOW_CELL + 1
        self.snow = (self.snow + [0.0] * cols)[:cols]

    def set_kind(self, kind):
        if kind in KINDS:
            self.kind = kind

    def set_auto(self, on, rng=random):
        self.auto = on
        self.auto_timer = rng.uniform(AUTO_MIN, AUTO_MAX)

    def busy(self):
        """True while anything is on screen (so the window must redraw)."""
        return (self.kind != "clear" or self.particles or self.sun > 0.01
                or any(h > 0.05 for h in self.snow)
                or self.night > 0.02)

    def gust(self):
        """Wind that comes and goes a little, so it doesn't look mechanical."""
        return self.wind * (0.75 + 0.25 * math.sin(self.t * 0.9) + 0.1 * math.sin(self.t * 3.1))

    # -- simulation ----------------------------------------------------------
    def step(self, dt, rng=random):
        self.t += dt
        if self.auto:
            self.auto_timer -= dt
            if self.auto_timer <= 0:
                # clear and sunny come up more often than the others
                self.kind = rng.choice(("clear", "clear", "sun", "sun", "rain", "snow", "wind"))
                self.auto_timer = rng.uniform(AUTO_MIN, AUTO_MAX)

        target = WIND[self.kind]
        self.wind += (target - self.wind) * min(1.0, dt * 0.8)
        sun_target = 1.0 if self.kind == "sun" else 0.0
        self.sun += (sun_target - self.sun) * min(1.0, dt * 0.7)

        self._spawn(dt, rng)
        self._move(dt, rng)
        self._melt(dt)

    def _spawn(self, dt, rng):
        rates = dict(SPAWN.get(self.kind, {}))
        # fireflies come out on dry nights
        if self.night > 0.5 and self.kind in ("clear", "sun", "wind"):
            fireflies = sum(1 for p in self.particles if p[0] == "firefly")
            if fireflies < FIREFLIES * self.width / 1920.0:
                rates["firefly"] = 2.0 * self.night
        scale = self.width / 1920.0
        for kind, per_sec in rates.items():
            debt = self._spawn_debt.get(kind, 0.0) + per_sec * scale * dt
            n = int(debt)
            self._spawn_debt[kind] = debt - n
            for _ in range(n):
                if len(self.particles) >= MAX_PARTICLES:
                    return
                self.particles.append(self._new(kind, rng))

    def _new(self, kind, rng):
        w, h = self.width, self.height
        seed = rng.random()
        if kind == "drop":
            # start a bit off the windward edge so the slant fills the screen
            x = rng.uniform(-0.3 * w, w) if self.wind > 0 else rng.uniform(0, 1.3 * w)
            return ["drop", x, rng.uniform(-60, -10), 0.0, rng.uniform(650, 850), 99.0, seed]
        if kind == "flake":
            x = rng.uniform(-0.2 * w, 1.1 * w)
            return ["flake", x, -8.0, 0.0, rng.uniform(35, 70), 99.0, seed]
        if kind == "streak":
            return ["streak", -120.0, rng.uniform(0, h * 0.9), 0.0, 0.0, 99.0, seed]
        if kind == "leaf":
            return ["leaf", -10.0, rng.uniform(0, h * 0.8), 0.0, rng.uniform(-20, 30), 99.0, seed]
        if kind == "firefly":
            # near the ground, where the plants are
            return ["firefly", rng.uniform(0, w), rng.uniform(h * 0.55, h - 10), 0.0, 0.0,
                    rng.uniform(6.0, 12.0), seed]
        # sun mote: a slow sparkle drifting in the light
        return ["mote", rng.uniform(0, w * 0.7), rng.uniform(0, h * 0.7), 0.0, -8.0,
                rng.uniform(2.0, 4.0), seed]

    def _move(self, dt, rng):
        gust = self.gust()
        ground = self.height
        alive = []
        for p in self.particles:
            kind = p[0]
            if kind == "drop":
                p[3] = gust * 1.6
                p[1] += p[3] * dt
                p[2] += p[4] * dt
                if p[2] >= ground - self.snow_at(p[1]):
                    for vx in (-60, 60):
                        alive.append(["splash", p[1], ground - self.snow_at(p[1]) - 2, vx, -90.0, 0.25, 0.0])
                    continue
            elif kind == "flake":
                p[3] = gust + math.sin(self.t * 1.7 + p[6] * 6.3) * 25
                p[1] += p[3] * dt
                p[2] += p[4] * dt
                land = ground - self.snow_at(p[1])
                if p[2] >= land:
                    self._pile(p[1])
                    continue
            elif kind == "splash":
                p[4] += 600 * dt
                p[1] += p[3] * dt
                p[2] += p[4] * dt
                p[5] -= dt
            elif kind == "streak":
                p[1] += (gust * 3.2 + 300) * dt
            elif kind == "leaf":
                p[1] += (gust * 1.4 + 60) * dt
                p[2] += (p[4] + math.sin(self.t * 3 + p[6] * 9) * 40) * dt
            elif kind == "firefly":
                # a lazy wander, nudged by the wind
                p[1] += (math.sin(self.t * 0.7 + p[6] * 20) * 18 + gust * 0.3) * dt
                p[2] += math.sin(self.t * 0.9 + p[6] * 13) * 10 * dt
                p[5] -= dt
            elif kind == "mote":
                p[1] += (gust * 0.4 + math.sin(self.t + p[6] * 5) * 6) * dt
                p[2] += p[4] * dt
                p[5] -= dt
            # gone when off screen or out of life
            if p[5] <= 0 or p[2] > ground + 20 or p[2] < -100:
                continue
            if p[1] > self.width + 150 or p[1] < -0.4 * self.width - 150:
                continue
            alive.append(p)
        self.particles = alive

    # -- snow pile -------------------------------------------------------------
    def snow_at(self, x):
        i = int(x) // SNOW_CELL
        if 0 <= i < len(self.snow):
            return self.snow[i]
        return 0.0

    def _pile(self, x):
        i = int(x) // SNOW_CELL
        if not 0 <= i < len(self.snow):
            return
        for j, amount in ((i, 2.0), (i - 1, 1.0), (i + 1, 1.0)):
            if 0 <= j < len(self.snow):
                self.snow[j] = min(SNOW_MAX, self.snow[j] + amount)

    def _melt(self, dt):
        if self.kind == "snow":
            return
        rate = 4.0 * dt              # px per second
        for i, h in enumerate(self.snow):
            if h > 0:
                self.snow[i] = max(0.0, h - rate)
