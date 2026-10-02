"""Draws the weather in its own full-screen window, just behind the pets.

It is its own window so it can ignore the mouse completely: a raindrop
passing under your cursor must never catch a click meant for your app.
"""

import math

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget

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
MOTE = QColor(255, 240, 170)
RAY = (255, 208, 96)
FIREFLY = QColor("#e4ff5c")
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

    def _tick(self):
        if not self.isVisible():
            return
        busy = self.weather.busy()
        if busy:
            self.weather.step(TICK_MS / 1000.0)
        elif self.weather.auto:
            self.weather.step(TICK_MS / 1000.0)  # keep the auto clock running
        if self.on_step:
            self.on_step(self.weather)
        if busy or self._was_busy:
            self.update()
        self._was_busy = busy

    # -- drawing ---------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(event.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        w = self.weather
        if w.sun > 0.01:
            self._rays(p, w)
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
                c = QColor(MOTE)
                c.setAlphaF(0.85 * a * w.sun)
                p.fillRect(int(x), int(y), PX, PX, c)
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
        """A few soft beams fanning out from beyond the top-left corner."""
        width, height = self.width(), self.height()
        ox, oy = -width * 0.08, -height * 0.25
        reach = math.hypot(width, height) * 1.2
        for i, (angle, spread) in enumerate(((0.35, 0.05), (0.52, 0.035), (0.68, 0.06),
                                             (0.86, 0.03), (1.02, 0.045))):
            pulse = 0.65 + 0.35 * math.sin(w.t * 0.4 + i * 1.7)
            c = QColor(*RAY)
            c.setAlphaF(0.11 * pulse * w.sun)
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
