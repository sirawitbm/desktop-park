"""Draws the weather in its own full-screen window, just behind the pets.

It is its own window so it can ignore the mouse completely: a raindrop
passing under your cursor must never catch a click meant for your app.
"""

import math
import random

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget

import daycycle
import winutil
from weather import SNOW_CELL, Weather

TICK_MS = 50            # 20 updates a second is plenty for pixel weather
PX = 3                  # size of one "weather pixel"

RAIN = QColor(150, 200, 255, 170)
RAIN_TIP = QColor(220, 240, 255, 200)
SNOW = QColor(250, 252, 255, 235)
SNOW_SHADE = QColor(190, 215, 240, 235)
STREAK = QColor(255, 255, 255, 90)
LEAVES = (QColor("#38b764"), QColor("#a7f070"), QColor("#ef7d3a"), QColor("#ffcd4f"))
MOTE_DAY = (255, 240, 170)


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))
RAY = (255, 208, 96)              # sunbeams
RAY_MOON = (196, 214, 255)        # moonbeams
# The light-ray beams: (angle from the middle of the fan, half-width), radians.
BEAMS = ((-1.25, 0.05), (-1.07, 0.07), (-0.89, 0.04), (-0.72, 0.075), (-0.55, 0.045),
         (-0.38, 0.08), (-0.21, 0.05), (-0.04, 0.085), (0.13, 0.05), (0.30, 0.075),
         (0.47, 0.045), (0.64, 0.08), (0.81, 0.05), (0.98, 0.07), (1.16, 0.05))
FIREFLY = QColor("#e4ff5c")
MOON_LIGHT = QColor("#f4efcf")
MOON_SHADE = QColor("#c9c09a")
STAR = QColor("#e8eeff")
STARS = 30


def _moon_image(n=14, scale=4):
    """A pixel crescent: a full circle with a smaller circle bitten out."""
    img = QImage(n * scale, n * scale, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            if math.hypot(x - c, y - c) > n / 2 - 0.2:
                continue
            bite = math.hypot(x - c - 3.6, y - c + 1.6)
            if bite < n / 2 - 1.6:
                continue
            col = MOON_SHADE if bite < n / 2 - 0.4 or x < 2 else MOON_LIGHT
            for dy in range(scale):
                for dx in range(scale):
                    img.setPixelColor(x * scale + dx, y * scale + dy, col)
    return img


SUN_CORE = QColor("#ffe27a")
SUN_EDGE = QColor("#ffb83d")
BODY_SCALE = 4                    # the sun and moon are drawn 4x


def _sun_image(n=16, scale=BODY_SCALE):
    """A pixel sun: a round middle with eight short rays."""
    img = QImage(n * scale, n * scale, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c)
            col = None
            if d < 4.2:
                col = SUN_CORE if d < 3.0 else SUN_EDGE
            elif 5.4 < d < 7.6:
                ang = math.degrees(math.atan2(y - c, x - c)) % 45
                if ang < 9 or ang > 36:
                    col = SUN_EDGE
            if col is not None:
                for dy in range(scale):
                    for dx in range(scale):
                        img.setPixelColor(x * scale + dx, y * scale + dy, col)
    return img


GLOW_STEPS = (0.55, 0.36, 0.22, 0.10)   # alpha of each ring, from the middle out


class WeatherWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
                         | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput
                         | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowTitle("Desktop Park weather")
        self.weather = Weather()
        self.on_step = None            # called each tick (the app passes the wind to the pets)
        self._was_busy = False
        self._glow_cache = {}
        self._cloud_cache = {}
        self._bodies = {}               # (sun/moon, pixel size) -> picture
        self._sky_elapsed = 0.0
        rng = random.Random(7)                  # the same sky every night
        self._stars = [(rng.random(), rng.random() * 0.36, rng.random(), rng.random() < 0.2)
                       for _ in range(STARS)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(TICK_MS)

    def fit_screen(self, screen):
        area = screen.availableGeometry()
        self.setGeometry(area)
        self.weather.resize(area.width(), area.height())

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        winutil.no_activate(hwnd)
        winutil.click_through(hwnd, True)       # always: weather never takes clicks

    def set_low_power(self, on):
        self.timer.setInterval(100 if on else TICK_MS)

    def _tick(self):
        if not self.isVisible():
            return
        dt = self.timer.interval() / 1000.0
        busy = self.weather.busy()
        if busy:
            self.weather.step(dt)
        elif self.weather.auto:
            self.weather.step(dt)  # keep the auto clock running
        if self.on_step:
            self.on_step(self.weather)
        if busy or self._was_busy:
            self.update()
        elif self.weather.sky:
            self._sky_elapsed += dt
            if self._sky_elapsed >= 2.0:
                self._sky_elapsed = 0.0
                self.update()
        self._was_busy = busy

    # -- drawing ---------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(event.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        w = self.weather
        if w.night > 0.02:
            self._draw_stars(p, w)
        if w.sun > 0.01:
            self._rays(p, w)
        if w.sky:
            self._body(p, w)
        if w.night > 0.02:
            self._glows(p, w)
        for q in w.particles:
            kind, x, y = q[0], q[1], q[2]
            if kind == "drop":
                self._drop(p, x, y, q[3], q[4])
            elif kind == "flake":
                size = PX + (PX if q[6] > 0.7 else 0)
                p.fillRect(int(x), int(y), size, size, SNOW)
            elif kind == "splash":
                p.fillRect(int(x), int(y), 2, 2, RAIN_TIP)
            elif kind == "streak":
                length = int(40 + q[6] * 90)
                p.fillRect(int(x), int(y), length, 2, STREAK)
                p.fillRect(int(x + length * 0.3), int(y - 2), int(length * 0.4), 2, STREAK)
            elif kind == "leaf":
                self._leaf(p, x, y, q[6], w.t)
            elif kind == "firefly":
                blink = 0.6 + 0.4 * math.sin(w.t * 2.6 + q[6] * 40)   # never fully dark
                fade = min(1.0, q[5] / 1.5)          # fades out at the end of its life
                a = max(0.0, blink * fade * w.night)
                c = QColor(FIREFLY)
                c.setAlphaF(0.35 * a)
                p.fillRect(int(x) - PX, int(y) - PX, PX * 4, PX * 4, c)   # soft halo
                c.setAlphaF(min(1.0, 1.4 * a))
                p.fillRect(int(x), int(y), PX * 2, PX * 2, c)
                p.fillRect(int(x), int(y), PX, PX, QColor(255, 255, 220, int(200 * a)))  # bright middle
            elif kind == "mote":
                a = max(0.0, min(1.0, q[5] / 1.0)) * (0.5 + 0.5 * math.sin(w.t * 4 + q[6] * 9))
                c = QColor(*_mix(MOTE_DAY, RAY_MOON, w.night))
                c.setAlphaF(0.85 * a * w.sun)
                p.fillRect(int(x), int(y), PX, PX, c)
        if w.cover > 0.01:
            self._clouds(p, w)          # in front of the sun, moon and rain
        self._snow_pile(p, w)
        p.end()

    def _glow_pixmap(self, radius, colour):
        """A soft round light made of stepped pixel rings, drawn once and reused."""
        key = (radius, colour)
        pm = self._glow_cache.get(key)
        if pm is None:
            size = radius * 2
            img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent)
            painter = QPainter(img)
            base = QColor(colour)
            cells = max(1, size // PX)
            for gy in range(cells):
                for gx in range(cells):
                    dx = (gx + 0.5) * PX - radius
                    dy = (gy + 0.5) * PX - radius
                    d = math.hypot(dx, dy) / radius
                    if d >= 1:
                        continue
                    c = QColor(base)
                    c.setAlphaF(GLOW_STEPS[min(len(GLOW_STEPS) - 1, int(d * len(GLOW_STEPS)))])
                    painter.fillRect(gx * PX, gy * PX, PX, PX, c)
            painter.end()
            pm = QPixmap.fromImage(img)
            if len(self._glow_cache) > 40:
                self._glow_cache.clear()
            self._glow_cache[key] = pm
        return pm

    def _draw_stars(self, p, w):
        """A few faint twinkling stars near the top of the screen."""
        width, height = self.width(), self.height()
        for fx, fy, phase, big in self._stars:
            a = w.night * (1.0 - w.cover) * (0.35 + 0.3 * math.sin(w.t * (0.8 + phase) + phase * 30))
            if a <= 0.02:
                continue
            c = QColor(STAR)
            c.setAlphaF(min(1.0, a))
            x, y = int(fx * width), int(fy * height)
            p.fillRect(x, y, PX, PX, c)
            if big:                              # a little twinkle cross
                c.setAlphaF(min(1.0, a * 0.5))
                p.fillRect(x - PX, y, PX, PX, c)
                p.fillRect(x + PX, y, PX, PX, c)
                p.fillRect(x, y - PX, PX, PX, c)
                p.fillRect(x, y + PX, PX, PX, c)

    def body_pos(self, w):
        """Centre of the sun or moon on its arc across the top of the screen."""
        x, y, _ = daycycle.arc(w.sky[1], self.width(), self.height())
        return x, y

    def _body_pixmap(self, body, scale):
        key = (body, scale)
        if key not in self._bodies:
            img = _sun_image(scale=scale) if body == "sun" else _moon_image(n=16, scale=scale)
            self._bodies[key] = QPixmap.fromImage(img)
        return self._bodies[key]

    def _body(self, p, w):
        """The sun by day, the moon by night, following the clock."""
        body = w.sky[0]
        strength = ((1.0 - w.night) if body == "sun" else w.night) * w.sky_strength()
        if strength <= 0.02:
            return
        cx, cy, scale = daycycle.arc(w.sky[1], self.width(), self.height())
        pm = self._body_pixmap(body, scale)
        radius = int(pm.width() * 1.25)
        glow = self._glow_pixmap(radius, "#ffe9a8" if body == "sun" else "#cfdcff")
        p.setOpacity(0.35 * strength)
        p.drawPixmap(int(cx - radius), int(cy - radius), glow)
        p.setOpacity(strength)
        p.drawPixmap(int(cx - pm.width() / 2), int(cy - pm.height() / 2), pm)
        p.setOpacity(1.0)

    def _cloud_pixmap(self, seed, size, gloom, night):
        """A pixel cloud: a few round puffs on a flat bottom, a bright top edge
        and a shaded underside. White by day, grey for rain, blue-grey at night."""
        key = (round(seed, 3), size, round(gloom * 4), round(night * 4))
        pm = self._cloud_cache.get(key)
        if pm is not None:
            return pm
        rng = random.Random(seed)
        w, h = size, max(7, int(size * 0.55))
        # a lumpy cumulus: a tall puff near the middle, lower shoulders, a few
        # extra bumps along the top - every cloud a little different
        puffs = [(w * rng.uniform(0.42, 0.58), 0, w * rng.uniform(0.24, 0.3))]
        for side in (-1, 1):
            puffs.append((w * (0.5 + side * rng.uniform(0.22, 0.3)), 0, w * rng.uniform(0.15, 0.21)))
        for _ in range(rng.randint(1, 3)):
            puffs.append((w * rng.uniform(0.25, 0.75), 0, w * rng.uniform(0.1, 0.17)))
        puffs = [(cx, h - r * rng.uniform(0.75, 1.0), r) for cx, _, r in puffs]

        left = min(cx - r * 0.8 for cx, _, r in puffs)
        right = max(cx + r * 0.8 for cx, _, r in puffs)

        def inside(x, y):
            if y >= h or x < 0 or x >= w:
                return False
            if y < 0:
                return False
            if any(math.hypot(x + 0.5 - cx, y + 0.5 - cy) < r for cx, cy, r in puffs):
                return True
            # a flat base under the puffs, so the underside has no notches
            return y >= h - 3 and left <= x + 0.5 <= right

        tone = lambda day, rain, dark: _mix(_mix(day, rain, gloom), dark, night * 0.85)   # noqa: E731
        fill = QColor(*tone((236, 241, 250), (128, 138, 160), (46, 56, 90)))
        top = QColor(*tone((255, 255, 255), (162, 172, 192), (66, 78, 116)))
        under = QColor(*tone((196, 206, 226), (98, 108, 130), (32, 40, 66)))
        s = BODY_SCALE
        img = QImage(w * s, h * s, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        for y in range(h):
            for x in range(w):
                if not inside(x, y):
                    continue
                if not inside(x, y - 1):
                    col = top
                elif y >= h - 2 or not inside(x, y + 2):
                    col = under
                else:
                    col = fill
                for dy in range(s):
                    for dx in range(s):
                        img.setPixelColor(x * s + dx, y * s + dy, col)
        pm = QPixmap.fromImage(img)
        if len(self._cloud_cache) > 120:
            self._cloud_cache.clear()
        self._cloud_cache[key] = pm
        return pm

    def _clouds(self, p, w):
        for i, (x, y, size, seed, _) in enumerate(w.clouds):
            a = w.cloud_alpha(i)
            if a <= 0.01:
                continue
            p.setOpacity(0.88 * a)
            p.drawPixmap(int(x), int(y), self._cloud_pixmap(seed, size, w.gloom, w.night))
        p.setOpacity(1.0)

    def _glows(self, p, w):
        """Lamps, fires and lanterns light up softly as night falls."""
        for x, y, radius, colour, flickers in w.glows:
            strength = w.night
            if flickers:
                strength *= 0.82 + 0.18 * math.sin(w.t * 9 + x * 0.1) * math.sin(w.t * 5.3 + y)
            p.setOpacity(max(0.0, min(1.0, strength)))
            pm = self._glow_pixmap(int(radius), colour)
            p.drawPixmap(int(x - radius), int(y - radius), pm)
        p.setOpacity(1.0)

    def _drop(self, p, x, y, vx, vy):
        # three short stacked pixels, shifted by the wind: a slanted pixel line
        slant = vx / max(1.0, vy) * 5
        for i in range(3):
            p.fillRect(int(x - slant * i), int(y - 5 * i), 2, 5, RAIN)
        p.fillRect(int(x + slant), int(y + 5), 2, 2, RAIN_TIP)

    def _leaf(self, p, x, y, seed, t):
        c = LEAVES[int(seed * len(LEAVES)) % len(LEAVES)]
        flip = int(t * 6 + seed * 10) % 2      # tumbling: two shapes, back and forth
        x, y, u = int(x), int(y), 4
        if flip:
            p.fillRect(x, y, u * 2, u, c)
            p.fillRect(x + u, y + u, u * 2, u, c)
        else:
            p.fillRect(x + u, y, u, u * 2, c)
            p.fillRect(x, y + u, u, u * 2, c)

    def _rays(self, p, w):
        """Light rays: warm sunbeams by day, silver moonbeams by night, fanning
        out from wherever the sun or moon is (or from beyond the top-left
        corner when the sky is hidden)."""
        width, height = self.width(), self.height()
        if w.sky:
            ox, oy = self.body_pos(w)
        else:
            ox, oy = -width * 0.08, -height * 0.25
        colour = _mix(RAY, RAY_MOON, w.night)
        strength = 0.15 - 0.03 * w.night
        reach = math.hypot(width, height) * 1.2
        base = math.atan2(height * 0.9 - oy, width / 2 - ox)     # aim at the park
        for i, (angle, spread) in enumerate(BEAMS):
            angle += base
            pulse = 0.65 + 0.35 * math.sin(w.t * 0.4 + i * 1.7)
            c = QColor(*colour)
            c.setAlphaF(strength * pulse * w.sun)
            a1, a2 = angle - spread, angle + spread
            poly = QPolygonF([QPointF(ox, oy),
                              QPointF(ox + math.cos(a1) * reach, oy + math.sin(a1) * reach),
                              QPointF(ox + math.cos(a2) * reach, oy + math.sin(a2) * reach)])
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawPolygon(poly)
        p.setBrush(Qt.NoBrush)

    def _snow_pile(self, p, w):
        ground = self.height()
        snow = w.snow
        n = len(snow)
        for i in range(n):
            # smooth with the neighbours, then snap to 2-pixel steps (pixel look)
            h = (snow[i] * 2 + (snow[i - 1] if i else snow[i]) + (snow[i + 1] if i + 1 < n else snow[i])) / 4
            h = int(h) // 2 * 2
            if h <= 0:
                continue
            x = i * SNOW_CELL
            p.fillRect(x, ground - h, SNOW_CELL, h, SNOW)
            p.fillRect(x, ground - 2, SNOW_CELL, 2, SNOW_SHADE)
