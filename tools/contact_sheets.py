"""Contact sheets of every built-in picture, for design reviews. Off-screen.

    python tools/contact_sheets.py review/v0.5/after

Writes 1_pets.png, 2_decor.png, 3_particles_icons.png, 4_sun_moon.png and
5_clouds.png into the folder (sprites enlarged on their pixel grid).
"""

import os
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def sheet(items, path, scale=5, cols=8, bg="#5a6f94"):
    cell = max(max(img.width(), img.height()) for _, img in items) * scale + 30
    rows = (len(items) + cols - 1) // cols
    out = QImage(cols * cell, rows * (cell + 16), QImage.Format_ARGB32)
    out.fill(QColor(bg))
    p = QPainter(out)
    f = QFont("Segoe UI")
    f.setPixelSize(12)
    p.setFont(f)
    p.setPen(QColor("white"))
    for i, (label, img) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + 16)
        big = img.scaled(img.width() * scale, img.height() * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        p.drawImage(x + (cell - big.width()) // 2, y + (cell - big.height()) // 2, big)
        p.drawText(x + 4, y + cell + 12, label)
    p.end()
    out.save(str(path))


def animation(library, path):
    pictures = [library.get(art_id) for art_id in ("cat", "dog", "duck", "bunny")]
    frames = []
    durations = [100] * 12 + [900, 160, 700, 1800]
    for index in range(len(durations)):
        canvas = QImage(640, 150, QImage.Format_RGBA8888)
        canvas.fill(QColor("#5a6f94"))
        painter = QPainter(canvas)
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI")
        font.setPixelSize(14)
        painter.setFont(font)
        for column, picture in enumerate(pictures):
            if index < 12:
                frame = index % len(picture["frames"])
            elif index == 13:
                frame = library.pose_frame(picture["id"], "blink")
            elif index == 15:
                frame = library.pose_frame(picture["id"], "sleep")
            else:
                frame = 0
            pixmap = library.pixmap(picture["id"], frame, 6, False)
            painter.drawPixmap(column * 160 + (160 - pixmap.width()) // 2, 115 - pixmap.height(), pixmap)
            painter.drawText(column * 160 + 12, 138, picture["name"])
        painter.end()
        frames.append(Image.frombytes("RGBA", (canvas.width(), canvas.height()),
                                      canvas.bits().tobytes()))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, disposal=2)


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])  # noqa: F841
    import art
    import park
    import sprites
    import ui_style
    import weather_window

    ui_style.install(app)
    lib = sprites.Library([])

    def frames(a):
        items = [("%s %d" % (a["id"], i + 1), sprites.frame_image(a, fr)) for i, fr in enumerate(a["frames"])]
        return items + [(a["id"] + " " + pose, sprites.frame_image(a, frame))
                        for pose, frame in a.get("poses", {}).items()]

    allart = list(lib.builtin.values())
    sheet([x for a in allart if a["kind"] == "pet" for x in frames(a)], out / "1_pets.png", scale=5)
    sheet([x for a in allart if a["kind"] != "pet" for x in frames(a)], out / "2_decor.png", scale=4)
    animation(lib, out / "animation.gif")
    pic = lambda pal, rows: sprites.frame_image({"palette": pal, "frames": [rows]}, rows)   # noqa: E731
    items = [(k, park._outlined(pic(pal, rows))) for k, (pal, rows) in art.PARTICLES.items()]
    items += [("w:" + k, pic(art.WEATHER_ICON_PALETTE, v)) for k, v in art.WEATHER_ICONS.items()]
    items += [("ui:" + k, pic(art.WEATHER_ICON_PALETTE, v)) for k, v in art.UI_ICONS.items()]
    sheet(items, out / "3_particles_icons.png", scale=6, bg="#2c3449")
    bodies = [("sun", weather_window._sun_image(scale=1)), ("moon", weather_window._moon_image(n=16, scale=1))]
    sheet(bodies, out / "4_sun_moon.png", scale=8, cols=2, bg="#4a5d80")
    ww = weather_window.WeatherWindow()
    clouds = []
    for seed in (0.11, 0.52, 0.93):
        for gloom, night, label in ((0, 0, "day"), (1, 0, "rain"), (1, 1, "night")):
            pm = ww._cloud_pixmap(seed, 40, gloom, night)
            img = pm.toImage()
            clouds.append((label, img.scaled(img.width() // 4, img.height() // 4)))
    sheet(clouds, out / "5_clouds.png", scale=4, cols=3, bg="#4a5d80")
    print("wrote contact sheets to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "review/latest")
