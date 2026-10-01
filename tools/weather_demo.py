"""Render the README weather pictures, off-screen (nothing appears on your
screen): docs/weather.gif (animated), docs/weather.png (all four at once)
and docs/board.png. Needs Pillow.

Run:  python tools/weather_demo.py
"""

import io
import os
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import store  # noqa: E402

_tmp = tempfile.mkdtemp()
store.park_file = lambda: os.path.join(_tmp, "park.json")   # never touch your real park

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication, QSystemTrayIcon  # noqa: E402

import board as boardmod  # noqa: E402
import park as parkmod  # noqa: E402
import updates  # noqa: E402
import weather_window as wwmod  # noqa: E402

W, H = 1000, 340
FPS = 14
BG = "#1e2436"
CLIPS = (("sun", "Sunny", 6, 2.6), ("rain", "Rain", 3, 2.6),
         ("snow", "Snow", 140, 3.0), ("wind", "Windy", 6, 2.6))   # kind, label, warm-up s, length s

SCENE = [("cherry", 30, 4), ("cottage", 120, 4), ("fence", 205, 3), ("lamp", 290, 3),
         ("tree", 380, 4), ("bush", 445, 3), ("campfire", 520, 3), ("stump", 590, 3),
         ("tulips", 655, 3), ("pond", 715, 3), ("pine", 800, 4), ("crystal", 860, 3),
         ("palm", 920, 4)]
PETS = [("cat", 330, 3, "walk"), ("bunny", 560, 3, "hop"), ("duck", 760, 3, "walk"),
        ("frog", 470, 3, "hop"), ("butterfly", 250, 3, "fly"), ("bee", 700, 3, "fly"),
        ("fish", 120, 3, "swim"), ("jelly", 880, 3, "swim")]


def off_screen(self, screen):
    self.setGeometry(-9000, -9000, W, H)
    if hasattr(self, "world"):
        self.world.resize(W, H)
    else:
        self.weather.resize(W, H)


def to_pil(qimg):
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    qimg.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGB")


def label(img, text):
    """A small rounded tag in the corner saying which weather this is."""
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=18)
    w = d.textlength(text, font=font)
    d.rounded_rectangle([14, 14, 14 + w + 22, 44], radius=8, fill="#2c3449", outline="#5b7bd5", width=2)
    d.text((25, 18), text, fill="#ffffff", font=font)
    return img


def main():
    parkmod.ParkWindow.fit_screen = off_screen
    wwmod.WeatherWindow.fit_screen = off_screen
    boardmod.Board.place = lambda self, x, y, r: self.move(-9000, -8000)
    QSystemTrayIcon.show = lambda self: None
    updates.latest_release = lambda timeout=10: None
    import desktop_park

    qapp = QApplication(sys.argv)
    app = desktop_park.App(qapp)
    pk, ww = app.park, app.weather
    pk.timer.stop()
    ww.timer.stop()
    rng = random.Random(11)

    def build_scene():
        pk.world.things = []
        pk.world.particles = []
        ground = pk.world.ground
        for art_id, x, s in SCENE:
            t = pk.make_thing(art_id, scale=s)
            t.x, t.y = x, ground - t.h
            pk.world.things.append(t)
        for art_id, x, s, b in PETS:
            t = pk.make_thing(art_id, scale=s, behavior=b)
            t.x = x
            t.y = {"fly": 70, "swim": 120}.get(b, ground - t.h)
            pk.world.things.append(t)

    def frame():
        img = QImage(W, H, QImage.Format_ARGB32)
        img.fill(QColor(BG))
        p = QPainter(img)
        p.drawPixmap(0, 0, ww.grab())
        p.drawPixmap(0, 0, pk.grab())
        p.end()
        return to_pil(img)

    frames, stills = [], []
    dt = 1.0 / FPS
    for kind, text, warm, length in CLIPS:
        build_scene()
        w = ww.weather
        w.particles, w.snow = [], [0.0] * len(w.snow)
        w.wind, w.sun = 0.0, 0.0
        w.set_kind(kind)
        for _ in range(int(warm / dt)):
            w.step(dt, rng)
        for i in range(int(length * FPS)):
            w.step(dt, rng)
            pk.world.wind = w.gust()
            pk.world.step(dt, rng)
            img = frame()
            frames.append(label(img.copy(), text))
            if i == int(length * FPS * 0.6):
                stills.append(img)

    docs = ROOT / "docs"
    # one shared palette for every frame keeps the GIF small and steady
    # palette from a frame of every clip, so the sun keeps its warm colours
    sample = Image.new("RGB", (W, H * len(stills)))
    for i, s in enumerate(stills):
        sample.paste(s, (0, i * H))
    pal = sample.quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    gif = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    gif[0].save(docs / "weather.gif", save_all=True, append_images=gif[1:],
                duration=int(1000 / FPS), loop=0, optimize=True, disposal=1)

    # full-size crops (shrinking pixel art ruins it): the best part of each
    cw = W // 2
    crops = [(0, 0), (250, 0), (500, 0), (250, 0)]
    tiles = [label(s.crop((x, y, x + cw, y + H)), text)
             for s, (x, y), (_, text, _, _) in zip(stills, crops, CLIPS)]
    grid = Image.new("RGB", (cw * 2 + 6, H * 2 + 6), "#11141c")
    for i, t in enumerate(tiles):
        grid.paste(t, ((i % 2) * (cw + 6), (i // 2) * (H + 6)))
    grid.save(docs / "weather.png")

    ww.weather.set_kind("snow")
    app.board.set_weather("snow")
    app.board.grab().save(str(docs / "board.png"))
    for name in ("weather.gif", "weather.png", "board.png"):
        print(name, os.path.getsize(docs / name) // 1024, "KB")


if __name__ == "__main__":
    main()
