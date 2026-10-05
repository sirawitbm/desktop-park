"""Render the README picture of the Theme Pack, off-screen (nothing appears
on your screen): docs/theme-pack.png - the bottom of each of its seven parks,
labelled. Needs Pillow.

Run:  python tools/pack_preview.py
"""

import datetime
import io
import os
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "packs"))
os.chdir(ROOT)

import store  # noqa: E402

_tmp = tempfile.mkdtemp()
store.park_file = lambda: os.path.join(_tmp, "park.json")   # never touch your real park
store.data_dir = lambda: _tmp                                # and never take in real packs

import weather_demo as wd  # noqa: E402
from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication, QSystemTrayIcon  # noqa: E402

import board as boardmod  # noqa: E402
import daycycle  # noqa: E402
import park as parkmod  # noqa: E402
import theme_pack  # noqa: E402
import updates  # noqa: E402
import weather_window as wwmod  # noqa: E402

W, H = theme_pack.W, theme_pack.H
BAND = 330                          # how much of the bottom of each park to show
DAY = datetime.datetime(2026, 10, 5, 10, 30)
NIGHT = datetime.datetime(2026, 10, 5, 22, 30)
BG = {"day": "#2a3550", "night": "#141827"}


def off_screen(self, screen):
    self.setGeometry(-9000, -9000, W, H)
    if hasattr(self, "world"):
        self.world.resize(W, H)
    else:
        self.weather.resize(W, H)


def main():
    parkmod.ParkWindow.fit_screen = off_screen
    wwmod.WeatherWindow.fit_screen = off_screen
    boardmod.Board.place = lambda self, x, y, r: self.move(-9000, -8000)
    QSystemTrayIcon.show = lambda self: None
    updates.latest_release = lambda timeout=10: None
    import desktop_park

    qapp = QApplication(sys.argv)
    app = desktop_park.App(qapp)
    pack = theme_pack.build()
    for picture in pack["drawings"]:
        app.library.set_custom(picture)
    pk, ww = app.park, app.weather
    pk.timer.stop()
    ww.timer.stop()
    tiles = []
    for park in pack["parks"]:
        rng = random.Random(4)
        pk.load_things(park["objects"])
        night = 1.0 if park["time_mode"] == "night" else 0.0
        w = ww.weather
        w.particles, w.snow = [], [0.0] * len(w.snow)
        w.wind, w.sun = 0.0, 0.0
        w.set_kind(park["weather"])
        w.sky = daycycle.sky(NIGHT if night else DAY) if park["show_sky"] else None
        w.night = pk.world.night = night
        for _ in range(int(12 / 0.05)):                # let snow settle and fireflies come out
            w.glows = pk.glows() if night else []
            pk.world.lights = [(x, y, r) for x, y, r, _, _ in w.glows]
            w.step(0.05, rng)
        pk._shade_key = None
        pk.update()
        img = QImage(W, H, QImage.Format_ARGB32)
        img.fill(QColor(BG["night" if night else "day"]))
        p = QPainter(img)
        p.drawPixmap(0, 0, ww.grab())
        p.drawPixmap(0, 0, pk.grab())
        p.end()
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        shot = Image.open(io.BytesIO(bytes(buf.data()))).convert("RGB").crop((0, H - BAND, W, H))
        shot = shot.resize((W * 2 // 3, BAND * 2 // 3), Image.NEAREST)   # 2/3 keeps it crisp enough
        tiles.append(wd.label(shot, park["name"]))
    sheet = Image.new("RGB", (tiles[0].width, sum(t.height + 6 for t in tiles) - 6), "#11141c")
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height + 6
    out = ROOT / "docs" / "theme-pack.png"
    sheet.save(out, optimize=True)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
