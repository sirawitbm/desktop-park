"""The cozy pixel-game look shared by every window: pixel fonts, chunky
pixel frames for buttons, slots and panels, and one stylesheet.

The frames are drawn here in code (light edge top-left, shadow bottom-right,
notched corners) and saved as small PNGs that the stylesheet stretches like
a picture frame, so the edges stay crisp at any size.
"""

import os
import sys
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QImage
from PySide6.QtWidgets import QApplication

# Palette: Sweetie 16 by GrafxKid (see THIRD-PARTY-NOTICES.md)
INK = "#1a1c2c"          # outlines, darkest
PLUM = "#5d275d"
RED = "#b13e53"
ORANGE = "#ef7d57"
GOLD = "#ffcd75"
LIME = "#a7f070"
GREEN = "#38b764"
TEAL = "#257179"
NAVY = "#29366f"
BLUE = "#3b5dc9"
SKY = "#41a6f6"
CYAN = "#73eff7"
WHITE = "#f4f4f4"
MIST = "#94b0c2"
SLATE = "#566c86"
STONE = "#333c57"
DEEP = "#262b44"         # a touch darker than STONE, for sunken slots

U = 2                    # one "UI pixel" is 2 screen pixels
TEXT_FONT = "Pixelify Sans"
HEAD_FONT = "Silkscreen"

_FONT_FILES = ("PixelifySans.ttf", "Silkscreen-Regular.ttf", "Silkscreen-Bold.ttf")
_installed = False


def _base_dir():
    # PyInstaller unpacks bundled files to sys._MEIPASS
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _box(fill, light, dark, outline=INK, n=8, notch=True):
    """An n x n "UI pixel" frame: outline ring, bevel ring, flat middle."""
    img = QImage(n * U, n * U, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    cols = {"o": QColor(outline), "l": QColor(light), "d": QColor(dark), "f": QColor(fill)}
    last = n - 1
    for y in range(n):
        for x in range(n):
            corner = x in (0, last) and y in (0, last)
            if notch and corner:
                continue
            if x in (0, last) or y in (0, last):
                c = "o"
            elif x == 1 or y == 1:
                c = "l"
            elif x == last - 1 or y == last - 1:
                c = "d"
            else:
                c = "f"
            for dy in range(U):
                for dx in range(U):
                    img.setPixelColor(x * U + dx, y * U + dy, cols[c])
    return img


# name -> (fill, light, dark, outline). Sunken things swap light and dark.
FRAMES = {
    "panel": (STONE, SLATE, DEEP, INK),
    "titlebar": (NAVY, BLUE, INK, INK),
    "btn": (SLATE, MIST, STONE, INK),
    "btn_hover": ("#6a82a0", "#b8cad6", STONE, INK),
    "btn_down": (BLUE, NAVY, SKY, INK),
    "btn_on": (BLUE, NAVY, SKY, INK),
    "btn_on_hover": ("#4a6ee0", NAVY, CYAN, INK),
    "green": (GREEN, LIME, TEAL, INK),
    "green_hover": ("#4fcf7a", "#d0ffa0", TEAL, INK),
    "green_down": (TEAL, "#1a5157", GREEN, INK),
    "slot": (DEEP, INK, SLATE, INK),
    "slot_hover": (STONE, INK, MIST, GOLD),
    "field": (DEEP, INK, SLATE, INK),
    "head": (STONE, SLATE, DEEP, INK),
    "head_hover": (SLATE, MIST, STONE, INK),
    "close_hover": (RED, ORANGE, PLUM, INK),
    "update": ("#24452f", GREEN, INK, INK),
    "menu": (STONE, SLATE, DEEP, INK),
    "tip": (INK, STONE, INK, SLATE),
}


def _write_frames():
    folder = os.path.join(tempfile.gettempdir(), "DesktopPark-ui-2")
    os.makedirs(folder, exist_ok=True)
    paths = {}
    for name, (fill, light, dark, outline) in FRAMES.items():
        path = os.path.join(folder, name + ".png")
        if not os.path.exists(path):
            _box(fill, light, dark, outline).save(path)
        paths[name] = path.replace("\\", "/")
    return paths


def font(family=TEXT_FONT, px=16):
    """Pixel fonts only look sharp at their own sizes and without smoothing:
    Pixelify Sans at 16 px, Silkscreen at 8 or 16 px."""
    f = QFont(family)
    f.setPixelSize(px)
    f.setStyleStrategy(QFont.NoAntialias)
    f.setHintingPreference(QFont.PreferNoHinting)
    return f


def install(app=None):
    """Load the fonts and apply the stylesheet to the whole app (once)."""
    global _installed
    app = app or QApplication.instance()
    if _installed or app is None:
        return
    _installed = True
    for name in _FONT_FILES:
        QFontDatabase.addApplicationFont(os.path.join(_base_dir(), "assets", "fonts", name))
    app.setFont(font())
    app.setStyleSheet(stylesheet(_write_frames()))


def _frame(path, slice_px=2 * U):
    return 'border-image: url("%s") %d %d %d %d stretch stretch; border-width: %dpx;' % (
        path, slice_px, slice_px, slice_px, slice_px, slice_px)


def stylesheet(img):
    f = lambda name: _frame(img[name])      # noqa: E731
    return """
* {{ font-family: "{text}"; font-size: 16px; color: {white}; }}
QToolTip {{ {tip} padding: 2px 4px; color: {white}; }}

/* the board */
QFrame#board {{ {panel} }}
QFrame#titlebar {{ {titlebar} }}
QLabel#title {{ font-family: "{headfont}"; font-size: 16px; color: {gold}; }}
QLabel#section {{ font-family: "{headfont}"; font-size: 8px; color: {white}; padding: 6px 0 3px 2px;
                  border-bottom: 2px solid {deep}; margin-bottom: 2px; }}
QLabel#hint {{ font-family: "{headfont}"; font-size: 8px; color: {mist}; padding: 2px; }}
QLabel#empty {{ color: {slate}; padding: 2px; }}

/* buttons */
QPushButton, QToolButton {{ {btn} padding: 1px 6px; color: {white}; min-height: 22px; }}
QPushButton:hover, QToolButton:hover {{ {btn_hover} }}
QPushButton:pressed, QToolButton:pressed {{ {btn_down} padding: 2px 5px 0 7px; }}
QPushButton:checked, QToolButton:checked {{ {btn_on} color: #ffffff; }}
QPushButton:checked:hover, QToolButton:checked:hover {{ {btn_on_hover} }}
QPushButton:disabled, QToolButton:disabled {{ color: {slate}; }}
QToolButton::menu-indicator {{ image: none; width: 0; }}
QToolButton#quick, QToolButton#wbtn {{ padding: 0; min-height: 0; }}
QPushButton::menu-indicator {{ image: none; width: 0; }}
QPushButton#draw, QPushButton#save {{ {green} color: #ffffff; }}
QPushButton#draw:hover, QPushButton#save:hover {{ {green_hover} }}
QPushButton#draw:pressed, QPushButton#save:pressed {{ {green_down} }}

/* picture slots, like a game inventory */
QToolButton#thumb {{ {slot} padding: 0; }}
QToolButton#thumb:hover {{ {slot_hover} }}
QToolButton#thumb:pressed {{ {slot_hover} padding: 2px 0 0 2px; }}

/* small square buttons in the title bar */
QToolButton#head {{ {head} padding: 0; min-height: 0; }}
QToolButton#head:hover {{ {head_hover} }}
QToolButton#close {{ {head} padding: 0; min-height: 0; }}
QToolButton#close:hover {{ {close_hover} }}

/* the update notice */
QFrame#update {{ {update} }}
QLabel#updatetext {{ color: {lime}; }}
QToolButton#newver {{ {green} color: #ffffff; font-family: "{headfont}"; font-size: 8px; padding: 0 4px; }}
QToolButton#newver:hover {{ {green_hover} }}

/* scrolling */
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: {deep}; width: 10px; margin: 0; border: 2px solid {ink}; }}
QScrollBar::handle:vertical {{ background: {slate}; border-top: 2px solid {mist};
                              border-bottom: 2px solid {stone}; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

/* menus */
QMenu {{ {menu} padding: 2px; }}
QMenu::item {{ padding: 4px 18px 4px 8px; background: transparent; }}
QMenu::item:selected {{ background: {blue}; color: #ffffff; }}
QMenu::item:disabled {{ color: {mist}; }}
QMenu::separator {{ height: 2px; background: {deep}; margin: 3px 4px; }}
QMenu::indicator {{ width: 10px; height: 10px; margin-left: 4px; }}
QMenu::indicator:checked {{ background: {gold}; border: 2px solid {ink}; }}

/* editor and dialogs */
QDialog, QMessageBox {{ background: {stone}; }}
QLineEdit, QComboBox {{ {field} padding: 1px 4px; color: {white}; selection-background-color: {blue}; }}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{ background: {stone}; border: 2px solid {ink}; selection-background-color: {blue}; }}
QToolButton#swatch {{ padding: 0; min-height: 0; border: 2px solid {ink}; border-image: none; }}
QToolButton#swatch:hover {{ border: 2px solid {gold}; }}
QLabel#preview {{ {slot} }}
""".format(
        text=TEXT_FONT, headfont=HEAD_FONT, white=WHITE, gold=GOLD, mist=MIST, slate=SLATE,
        stone=STONE, deep=DEEP, ink=INK, blue=BLUE, lime=LIME,
        **{name: f(name) for name in FRAMES})
