"""Render the README screenshots off-screen (nothing appears on your screen):
docs/park.png, docs/board.png, docs/looks.png, docs/hotbar.png, docs/editor.png.
The weather and night pictures come from weather_demo.py / night_demo.py.

    python tools/screenshots.py [out_dir]       # default: docs
"""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import store  # noqa: E402

_tmp = tempfile.mkdtemp()
store.park_file = lambda: os.path.join(_tmp, "park.json")   # never touch your real park

from PIL import Image  # noqa: E402
from PySide6.QtCore import QEvent, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon  # noqa: E402

import board as boardmod  # noqa: E402
import park as parkmod  # noqa: E402
import ui_style  # noqa: E402
import updates  # noqa: E402
import weather_window as wwmod  # noqa: E402

W, H = 1400, 380
HERO = [("cherry", 40, 3), ("cottage", 120, 3), ("fence", 215, 3), ("lamp", 270, 3),
        ("tree", 330, 3), ("bush", 410, 3), ("campfire", 470, 3), ("flower", 540, 4),
        ("castle", 590, 3), ("stump", 690, 3), ("tulips", 745, 3), ("pond", 800, 3),
        ("pine", 880, 3), ("rock", 940, 3), ("mushroom", 985, 3), ("crystal", 1030, 3),
        ("grass", 1080, 3), ("palm", 1130, 4), ("clock", 1210, 3), ("sunflower", 1300, 3)]
HERO_PETS = [("cat", 250, 3, "walk"), ("bunny", 600, 3, "hop"), ("duck", 860, 3, "walk"),
             ("dog", 1050, 3, "walk"), ("frog", 510, 3, "hop"), ("slime", 1170, 3, "hop"),
             ("butterfly", 450, 3, "fly"), ("bee", 980, 3, "fly"), ("bird", 700, 3, "fly"),
             ("fish", 300, 3, "swim"), ("jelly", 1100, 3, "swim"), ("ghost", 150, 3, "swim")]


def settle(qapp):
    """Let Qt finish removing old widgets before a screenshot."""
    for _ in range(3):
        qapp.sendPostedEvents(None, QEvent.DeferredDelete)
        qapp.processEvents()


def off_screen(self, screen):
    self.setGeometry(-9000, -9000, W, H)
    if hasattr(self, "world"):
        self.world.relocate(W, H)
    else:
        self.weather.resize(W, H)


def main(out_dir="docs"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    parkmod.ParkWindow.fit_screen = off_screen
    wwmod.WeatherWindow.fit_screen = off_screen
    boardmod.Board.place = lambda self, x, y, r: self.move(-9000, -8000)
    QSystemTrayIcon.show = lambda self: None
    updates.latest_release = lambda timeout=10: None
    import desktop_park

    qapp = QApplication(sys.argv)
    app = desktop_park.App(qapp)
    pk = app.park
    pk.timer.stop()
    app.weather.timer.stop()
    app.weather.weather.sky = None

    # -- the hero picture: a row of the park along the bottom of a screen ---------
    ground = pk.world.ground
    pk.world.things = []
    for art_id, x, s in HERO:
        t = pk.make_thing(art_id, scale=s)
        t.x, t.y = x, ground - t.h
        pk.world.things.append(t)
    for art_id, x, s, b in HERO_PETS:
        t = pk.make_thing(art_id, scale=s, behavior="stay")
        t.behavior = b
        t.x = x
        t.y = {"fly": 120, "swim": 170}.get(b, ground - t.h)
        pk.world.things.append(t)
    byid = {t.art_id: t for t in pk.world.things}
    pk.world.poke(byid["bunny"], reaction="love")
    pk.world.poke(byid["duck"], reaction="dance")
    pk.world.poke(byid["cat"], reaction="jump")
    for _ in range(6):
        pk.world.step(0.033)
    for t in pk.world.things:
        t.vx = t.vy = 0

    def hero():
        img = QImage(W, H, QImage.Format_ARGB32)
        p = QPainter(img)
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor("#1b2133"))
        g.setColorAt(1, QColor("#2c3550"))
        p.fillRect(img.rect(), g)
        p.drawPixmap(0, 0, pk.grab())
        p.end()
        img.save(str(out / "park.png"))

    def boards():
        app.board.set_screen_menu(QMenu(), True)
        app.board.grab().save(str(out / "board.png"))
        shots = {}
        for theme in ui_style.THEMES:
            app.set_theme(theme)
            settle(qapp)
            shots[theme] = app.board.grab().toImage()
        a, b = shots["modern"], shots["pixel"]
        pair = QImage(a.width() + b.width() + 24, max(a.height(), b.height()), QImage.Format_ARGB32)
        pair.fill(QColor(0, 0, 0, 0))
        p = QPainter(pair)
        p.drawImage(0, 0, a)
        p.drawImage(a.width() + 24, 0, b)
        p.end()
        pair.save(str(out / "looks.png"))
        # the folded bar in both looks, drawn 2x on a taskbar-coloured strip
        bars = []
        for theme in ui_style.THEMES:
            app.set_theme(theme)
            app.board.set_collapsed(True)
            settle(qapp)
            bars.append(app.board.grab().toImage())
            app.board.set_collapsed(False)
        app.set_theme("modern")
        width = max(i.width() for i in bars) + 24
        strip = QImage(width, 48 * 2 + 8, QImage.Format_ARGB32)
        strip.fill(QColor("#202020"))
        p = QPainter(strip)
        for i, bar in enumerate(bars):
            p.drawImage(12, i * 56 + (48 - bar.height()) // 2, bar)
        p.end()
        strip.save(str(out / "hotbar_1x.png"))
        Image.open(out / "hotbar_1x.png").resize((strip.width() * 2, strip.height() * 2), Image.NEAREST).save(out / "hotbar.png")
        os.remove(out / "hotbar_1x.png")

    def editor():
        from editor import Editor
        ed = Editor(None, app.library.get("bunny"), as_copy=True)
        ed.move(-9000, -7000)
        ed.resize(900, 620)
        ed.show()

        def shot():
            ed._tick_preview()
            ed.grab().save(str(out / "editor.png"))
            ed.close()
            print("wrote screenshots to", out)
            qapp.exit(0)
        QTimer.singleShot(400, shot)

    def run():
        hero()
        boards()
        editor()

    QTimer.singleShot(500, run)
    qapp.exec()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs")
