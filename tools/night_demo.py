"""Render the README night picture, off-screen (nothing appears on your
screen): docs/night.gif - the park fading from day through sunset into night:
moon and stars, moonlit pets, glowing lamps and lanterns, fireflies. Needs Pillow.

Run:  python tools/night_demo.py
"""

import datetime
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)

import weather_demo as wd  # noqa: E402  (shares the off-screen helpers)

from PIL import Image  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication, QSystemTrayIcon  # noqa: E402

import daycycle  # noqa: E402
import board as boardmod  # noqa: E402
import park as parkmod  # noqa: E402
import updates  # noqa: E402
import weather_window as wwmod  # noqa: E402

W, H = wd.W, wd.H
FPS = 12
SECONDS = 7.5
START = datetime.datetime(2026, 10, 31, 17, 50)   # a sped-up Halloween evening
SPAN = datetime.timedelta(hours=2, minutes=40)     # ... squeezed into SECONDS
BG = "#141827"
SCENE = [("spookytree", 20, 4), ("grave", 105, 3), ("cottage", 160, 4), ("lamp", 255, 3),
         ("fence", 300, 3), ("jack", 380, 3), ("tree", 440, 4), ("campfire", 530, 4),
         ("cauldron", 620, 3), ("grave", 680, 3), ("jack", 730, 3), ("pine", 790, 4),
         ("clock", 852, 3), ("lamp", 945, 3)]
PETS = [("witchcat", 330, 3, "walk", True), ("cat", 590, 3, "walk", True),
        ("bunny", 470, 3, "hop", False), ("duck", 820, 3, "walk", True),
        ("bat", 300, 3, "fly", False), ("bat", 700, 3, "fly", False),
        ("ghost", 520, 3, "swim", False)]


def main():
    parkmod.ParkWindow.fit_screen = wd.off_screen
    wwmod.WeatherWindow.fit_screen = wd.off_screen
    boardmod.Board.place = lambda self, x, y, r: self.move(-9000, -8000)
    QSystemTrayIcon.show = lambda self: None
    updates.latest_release = lambda timeout=10: None
    import desktop_park

    qapp = QApplication(sys.argv)
    app = desktop_park.App(qapp)
    pk, ww = app.park, app.weather
    pk.timer.stop()
    ww.timer.stop()
    rng = random.Random(8)

    ground = pk.world.ground
    pk.world.things = []
    for art_id, x, s in SCENE:
        t = pk.make_thing(art_id, scale=s)
        t.x, t.y = x, ground - t.h
        pk.world.things.append(t)
    sleepers = []
    for art_id, x, s, b, asleep in PETS:
        t = pk.make_thing(art_id, scale=s, behavior=b)
        t.x = x
        t.y = {"fly": 60, "swim": 110}.get(b, ground - t.h)
        pk.world.things.append(t)
        if asleep:
            sleepers.append(t)

    w = ww.weather
    w.set_kind("clear")
    w.night = pk.world.night = 1.0
    for _ in range(int(15 / 0.05)):            # let the fireflies come out
        w.glows = pk.glows()
        w.step(0.05, rng)
    frames = []
    dt = 1.0 / FPS
    asleep = False
    for i in range(int(SECONDS * FPS)):
        clock = START + SPAN * (i / (SECONDS * FPS))
        level = daycycle.night_level(clock)
        w.night = pk.world.night = level
        w.sky = daycycle.sky(clock)
        app.library.set_clock(daycycle.clock_text(clock), "moon" if level >= 0.5 else "sun")
        if level >= 1.0 and not asleep:          # once it is dark, they doze off
            asleep = True
            for t in sleepers:
                pk.world.nap(t, rng)
                t.reaction_t = 99
        w.glows = pk.glows()
        pk.world.lights = [(x, y, r) for x, y, r, _, _ in w.glows]
        pk._shade_key = None
        pk.update()
        w.step(dt, rng)
        pk.world.step(dt, rng)
        img = QImage(W, H, QImage.Format_ARGB32)
        img.fill(QColor(BG))
        p = QPainter(img)
        p.drawPixmap(0, 0, ww.grab())
        p.drawPixmap(0, 0, pk.grab())
        p.end()
        frames.append(wd.label(wd.to_pil(img), daycycle.clock_text(clock)))

    picks = [frames[0], frames[len(frames) // 2], frames[-1]]     # day, sunset, night
    sample = Image.new("RGB", (W, H * 3))
    for i, f in enumerate(picks):
        sample.paste(f, (0, i * H))
    pal = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    gif = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out = ROOT / "docs" / "night.gif"
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=int(1000 / FPS),
                loop=0, optimize=True, disposal=1)
    frames[-1].save(ROOT / "docs" / "night.png")
    print("night.gif", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
