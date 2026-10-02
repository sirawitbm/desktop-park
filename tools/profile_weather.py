"""Measure weather raster-paint cost off-screen; never opens or saves a park.

    python tools/profile_weather.py --frames 32
"""

import argparse
import os
import random
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

import daycycle
import ui_style
from weather_window import WeatherWindow


def measure(width, height, kind, frames):
    window = WeatherWindow()
    window.timer.stop()
    window.resize(width, height)
    window.weather.resize(width, height)
    window.weather.night = 1.0
    window.weather.sky = daycycle.sky(mode="night")
    window.weather.set_kind(kind)
    rng = random.Random(7)
    for _ in range(200):
        window.weather.step(0.05, rng)
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    samples = []
    for index in range(frames + 4):
        image.fill(Qt.transparent)
        start = time.perf_counter()
        painter = QPainter(image)
        try:
            window.render(painter, QPoint())
        finally:
            painter.end()
        if index >= 4:
            samples.append((time.perf_counter() - start) * 1000)
    median = statistics.median(samples)
    print("%dx%d night %-5s median=%.2f ms  particles=%d  updates/s=20 (low power: 10)" %
          (width, height, kind, median, len(window.weather.particles)))
    window.deleteLater()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=32)
    args = parser.parse_args()
    if not 1 <= args.frames <= 500:
        parser.error("--frames must be between 1 and 500")
    app = QApplication([])
    ui_style.install(app)
    print("Interpreter:", sys.executable)
    print("Off-screen raster rendering only; does not measure Windows compositing or GPU cost.")
    for width, height in ((1920, 1040), (3840, 2080)):
        for kind in ("clear", "rain", "snow"):
            measure(width, height, kind, args.frames)
        app.processEvents()


if __name__ == "__main__":
    main()