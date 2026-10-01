"""Draws the weather in its own full-screen window, just behind the pets.

It is its own window so it can ignore the mouse completely: a raindrop
passing under your cursor must never catch a click meant for your app.
"""

import math

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPolygonF
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
            elif kind == "mote":
                a = max(0.0, min(1.0, q[5] / 1.0)) * (0.5 + 0.5 * math.sin(w.t * 4 + q[6] * 9))
                c = QColor(MOTE)
                c.setAlphaF(0.85 * a * w.sun)
                p.fillRect(int(x), int(y), PX, PX, c)
        self._snow_pile(p, w)
        p.end()

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
