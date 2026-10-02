"""The two looks you can pick in the tray menu (Look > Modern / Pixel).

- modern: the original dark, rounded look, with a pill-shaped folded bar.
- pixel:  a modern pixel-art look - flat colours, soft outlines, rounded
          pixel corners and the Pixelify Sans font.

The pixel frames are drawn here in code and saved as small PNGs that the
stylesheet stretches like a picture frame, so the edges stay crisp.
"""

import os
import sys
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QImage
from PySide6.QtWidgets import QApplication

THEMES = ("modern", "pixel")
LABELS = {"modern": "Modern", "pixel": "Pixel"}
PIXEL_FONT = "Pixelify Sans"
INK = "#161927"                   # darkest outline (pixel look)

_current = "modern"
_fonts_loaded = False
_frames = None


def current():
    return _current


def _base_dir():
    # PyInstaller unpacks bundled files to sys._MEIPASS
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _load_fonts():
    global _fonts_loaded
    if not _fonts_loaded:
        _fonts_loaded = True
        QFontDatabase.addApplicationFont(os.path.join(_base_dir(), "assets", "fonts", "PixelifySans.ttf"))


def pixel_font(px=16):
    """Pixelify Sans is only perfectly sharp at 16 px, drawn without smoothing."""
    f = QFont(PIXEL_FONT)
    f.setPixelSize(px)
    f.setStyleStrategy(QFont.NoAntialias)
    f.setHintingPreference(QFont.PreferNoHinting)
    return f


def install(app=None, theme=None):
    """Apply a look to the whole app. With no theme: keep the current one
    (only the first call does anything then)."""
    global _current
    app = app or QApplication.instance()
    if app is None:
        return
    if theme is None:
        if app.property("dp_theme"):
            return
        theme = _current
    _current = theme if theme in THEMES else "modern"
    app.setProperty("dp_theme", _current)
    if _current == "pixel":
        _load_fonts()
        app.setFont(pixel_font())
        app.setStyleSheet(_pixel_sheet(_write_frames()))
    else:
        f = QFont("Segoe UI")
        f.setPointSize(9)
        app.setFont(f)
        app.setStyleSheet(MODERN)


def folded_sheet():
    """Extra style for the board while it is folded into the taskbar bar."""
    return FOLDED_MODERN if _current == "modern" else FOLDED_PIXEL


# ---------------------------------------------------------------------------
# Modern: the original look
# ---------------------------------------------------------------------------

MODERN = """
QFrame#board { background: #1d2230; border: 1px solid #3a4258; border-radius: 10px; }
QFrame#titlebar { background: transparent; border: none; }
QLabel { color: #c9d1e6; font: 9pt 'Segoe UI'; }
QLabel#title { color: #ffffff; font: bold 10pt 'Segoe UI'; }
QLabel#section { color: #8d97b3; font: bold 8pt 'Segoe UI'; padding-top: 4px; }
QLabel#hint, QLabel#empty { color: #6f7893; font: 8pt 'Segoe UI'; }
QToolTip { color: #e6ebf7; background: #262c3d; border: 1px solid #3a4258; }

QPushButton, QToolButton { color: #e6ebf7; background: #2c3449; border: 1px solid #3a4258;
                           border-radius: 6px; padding: 5px 8px; font: 9pt 'Segoe UI'; }
QPushButton:hover, QToolButton:hover { background: #3a4767; }
QPushButton:checked, QToolButton:checked { background: #5b7bd5; border-color: #7d98e6; }
QPushButton::menu-indicator, QToolButton::menu-indicator { image: none; width: 0; }
QToolButton#wbtn { padding: 0; }
QPushButton#draw, QPushButton#save { background: #3f7d5a; border-color: #58a078; }
QPushButton#draw:hover, QPushButton#save:hover { background: #4b9a6d; }
QPushButton#save { font-weight: bold; }

QToolButton#thumb { background: #262c3d; border: 1px solid #2f364a; border-radius: 6px; padding: 0; }
QToolButton#thumb:hover { background: #33405c; border-color: #5b7bd5; }
QToolButton#head, QToolButton#close { color: #c9d1e6; background: transparent; border: none;
                   font: bold 11pt 'Segoe UI'; padding: 0 6px; }
QToolButton#head:hover, QToolButton#close:hover { color: #ffffff; background: #33405c; border-radius: 4px; }
QToolButton#quick { background: #262c3d; border: 1px solid #2f364a; border-radius: 6px; padding: 2px; }
QToolButton#quick:hover { background: #33405c; border-color: #5b7bd5; }
QToolButton#quick:checked { background: #5b7bd5; border-color: #7d98e6; }
QToolButton#newver { color: #ffffff; background: #3f7d5a; border: 1px solid #58a078;
                     border-radius: 6px; padding: 2px 6px; font: bold 8pt 'Segoe UI'; }
QFrame#qsep { background: #3a4258; border: none; }

QFrame#update { background: #24352d; border: 1px solid #3f7d5a; border-radius: 6px; }
QLabel#updatetext { color: #c8f0d4; font: 9pt 'Segoe UI'; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #3a4258; border-radius: 4px; min-height: 20px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QMenu { background: #262c3d; color: #e6ebf7; border: 1px solid #3a4258; }
QMenu::item { padding: 5px 18px 5px 8px; }
QMenu::item:selected { background: #5b7bd5; }
QMenu::separator { height: 1px; background: #3a4258; margin: 3px 6px; }

QDialog, QMessageBox { background: #1d2230; }
QLineEdit, QComboBox { color: #e6ebf7; background: #262c3d; border: 1px solid #3a4258;
                       border-radius: 5px; padding: 4px 6px; font: 9pt 'Segoe UI'; }
QComboBox QAbstractItemView { color: #e6ebf7; background: #262c3d;
                              selection-background-color: #5b7bd5; }
QToolButton#swatch { padding: 0; border-radius: 4px; }
QLabel#preview { background: #262c3d; border-radius: 6px; }
"""

# Folded: a rounded pill that sits neatly in the taskbar, with flat icon
# buttons that only light up when you point at them or switch them on.
FOLDED_MODERN = """
QFrame#board { background: transparent; border: none; }
QFrame#titlebar { background: #1d2230; border: 1px solid #3a4258; border-radius: 14px; }
QToolButton#quick { background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 2px; }
QToolButton#quick:hover { background: #2c3449; border-color: #3a4258; }
QToolButton#quick:checked { background: #2f3f6e; border-color: #5b7bd5; }
QToolButton#quick:checked:hover { background: #3a4d85; }
QToolButton#head, QToolButton#close { color: #c9d1e6; border-radius: 9px; padding: 0 6px; }
QToolButton#head { font-size: 12pt; }
QToolButton#head:hover { color: #ffffff; background: #2c3449; }
QToolButton#close:hover { color: #ffffff; background: #8c3a4a; }
QToolButton#newver { border-radius: 9px; padding: 1px 8px; }
"""


# ---------------------------------------------------------------------------
# Pixel: modern pixel art
# ---------------------------------------------------------------------------

U = 2                    # one "UI pixel" is 2 screen pixels

# name -> (fill, highlight, shade, outline). Sunken things have the shade on top.
FRAMES = {
    "panel": ("#262b40", "#30364f", "#20243a", INK),
    "titlebar": ("#30385a", "#3c4670", "#2a3150", INK),
    "btn": ("#363e5e", "#454f78", "#2e3552", INK),
    "btn_hover": ("#414b72", "#525d8c", "#373f60", INK),
    "btn_on": ("#5b7cfa", "#7d98ff", "#4a68e0", "#25368a"),
    "btn_on_hover": ("#6a88ff", "#8fa6ff", "#5675ea", "#25368a"),
    "green": ("#3ec27f", "#6be0a2", "#33a86d", "#1b6440"),
    "green_hover": ("#4bd18c", "#7decb0", "#3cb578", "#1b6440"),
    "slot": ("#1d2133", "#181b2b", "#262b42", INK),
    "slot_hover": ("#252a40", "#1f2335", "#2e3450", "#ffcf70"),
    "field": ("#1d2133", "#181b2b", "#262b42", INK),
    "head": ("#30385a", "#30385a", "#30385a", "#30385a"),
    "head_hover": ("#414b72", "#525d8c", "#373f60", INK),
    "close_hover": ("#d0485f", "#e86b80", "#b53a50", "#5e1a28"),
    "update": ("#1d3b2e", "#25503c", "#183226", "#2d7a55"),
    "menu": ("#262b40", "#30364f", "#20243a", INK),
    "tip": (INK, INK, INK, "#454f78"),
}


def _box(fill, hi, lo, outline, n=10):
    """An n x n "UI pixel" frame with rounded (stepped) corners, a soft
    one-pixel highlight along the top and a shade along the bottom."""
    img = QImage(n * U, n * U, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    last = n - 1

    def inside(x, y):
        if not (0 <= x <= last and 0 <= y <= last):
            return False
        return min(x, last - x) + min(y, last - y) >= 2   # stepped round corners

    for y in range(n):
        for x in range(n):
            if not inside(x, y):
                continue
            edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                c = outline
            elif not inside(x, y - 2):
                c = hi
            elif not inside(x, y + 2):
                c = lo
            else:
                c = fill
            col = QColor(c)
            for dy in range(U):
                for dx in range(U):
                    img.setPixelColor(x * U + dx, y * U + dy, col)
    return img


def _write_frames():
    global _frames
    if _frames is None:
        folder = os.path.join(tempfile.gettempdir(), "DesktopPark-ui-3")
        os.makedirs(folder, exist_ok=True)
        _frames = {}
        for name, colours in FRAMES.items():
            path = os.path.join(folder, name + ".png")
            if not os.path.exists(path):
                _box(*colours).save(path)
            _frames[name] = path.replace("\\", "/")
    return _frames


def _frame(path, s=3 * U):
    return 'border-image: url("%s") %d %d %d %d stretch stretch; border-width: %dpx;' % (path, s, s, s, s, s)


def _pixel_sheet(img):
    fr = {name: _frame(path) for name, path in img.items()}
    return """
* {{ font-family: "{font}"; font-size: 16px; color: #e8ecf7; }}
QToolTip {{ {tip} padding: 1px 4px; }}

QFrame#board {{ {panel} }}
QFrame#titlebar {{ {titlebar} }}
QLabel#title {{ color: #ffcf70; }}
QLabel#section {{ color: #8f9bc4; padding: 6px 0 0 2px; }}
QLabel#hint, QLabel#empty {{ font-family: "Segoe UI"; font-size: 11px; color: #6f7aa3; }}

QPushButton, QToolButton {{ {btn} padding: 0 6px; }}
QPushButton {{ min-height: 18px; }}
QPushButton:hover, QToolButton:hover {{ {btn_hover} }}
QPushButton:pressed, QToolButton:pressed {{ {btn_on} }}
QPushButton:checked, QToolButton:checked {{ {btn_on} color: #ffffff; }}
QPushButton:checked:hover, QToolButton:checked:hover {{ {btn_on_hover} }}
QPushButton::menu-indicator, QToolButton::menu-indicator {{ image: none; width: 0; }}
QToolButton#quick, QToolButton#wbtn {{ padding: 0; }}
QPushButton#draw, QPushButton#save {{ {green} color: #ffffff; }}
QPushButton#draw:hover, QPushButton#save:hover {{ {green_hover} }}

QToolButton#thumb {{ {slot} padding: 0; }}
QToolButton#thumb:hover, QToolButton#thumb:pressed {{ {slot_hover} }}
QToolButton#head, QToolButton#close {{ {head} padding: 0; }}
QToolButton#head:hover {{ {head_hover} }}
QToolButton#close:hover {{ {close_hover} }}
QToolButton#newver {{ {green} color: #ffffff; padding: 0 6px; }}
QToolButton#newver:hover {{ {green_hover} }}
QFrame#qsep {{ background: #454f78; border: none; }}

QFrame#update {{ {update} }}
QLabel#updatetext {{ color: #8ef0bd; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: #1d2133; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #454f78; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QMenu {{ {menu} padding: 2px; }}
QMenu::item {{ padding: 3px 18px 3px 8px; background: transparent; }}
QMenu::item:selected {{ background: #5b7cfa; color: #ffffff; }}
QMenu::separator {{ height: 2px; background: #1d2133; margin: 3px 4px; }}

QDialog, QMessageBox {{ background: #262b40; }}
QLineEdit, QComboBox {{ {field} padding: 0 4px; selection-background-color: #5b7cfa; }}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{ background: #262b40; border: 2px solid {ink}; selection-background-color: #5b7cfa; }}
QToolButton#swatch {{ padding: 0; border: 2px solid {ink}; border-image: none; }}
QToolButton#swatch:hover {{ border: 2px solid #ffcf70; }}
QLabel#preview {{ {slot} }}
""".format(font=PIXEL_FONT, ink=INK, **fr)


# Folded: the title bar is the whole window, so drop the outer frame.
FOLDED_PIXEL = "QFrame#board { border-image: none; border-width: 0px; }"
