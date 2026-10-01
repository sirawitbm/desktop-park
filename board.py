"""The floating control board: pick things to add, draw your own, lock or
hide the park. Drag it by the title bar; "-" folds it down to just the bar."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QActionGroup, QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout, QMenu,
                               QPushButton, QScrollArea, QToolButton,
                               QVBoxLayout, QWidget)

import art as artmod
import weather as weathermod
from sprites import frame_image

COLS = 5
FULL_WIDTH = COLS * 50 + 34
STYLE = """
#board { background: #1d2230; border: 1px solid #3a4258; border-radius: 10px; }
QLabel { color: #c9d1e6; font: 9pt 'Segoe UI'; }
QLabel#title { color: #ffffff; font: bold 10pt 'Segoe UI'; }
QLabel#section { color: #8d97b3; font: bold 8pt 'Segoe UI'; padding-top: 4px; }
QLabel#hint { color: #6f7893; font: 8pt 'Segoe UI'; }
QToolButton#thumb { background: #262c3d; border: 1px solid #2f364a; border-radius: 6px; }
QToolButton#thumb:hover { background: #33405c; border-color: #5b7bd5; }
QToolButton#head { color: #c9d1e6; background: transparent; border: none;
                   font: bold 11pt 'Segoe UI'; padding: 0 6px; }
QToolButton#head:hover { color: #ffffff; background: #33405c; border-radius: 4px; }
QToolButton#quick { background: #262c3d; border: 1px solid #2f364a; border-radius: 6px;
                    padding: 2px 4px; min-width: 22px; min-height: 22px; }
QToolButton#quick:hover { background: #33405c; border-color: #5b7bd5; }
QToolButton#quick:checked { background: #5b7bd5; border-color: #7d98e6; }
QToolButton#quick::menu-indicator { image: none; width: 0; }
QToolButton#newver { color: #ffffff; background: #3f7d5a; border: 1px solid #58a078;
                     border-radius: 6px; padding: 2px 6px; font: bold 8pt 'Segoe UI'; }
QPushButton { color: #e6ebf7; background: #2c3449; border: 1px solid #3a4258;
              border-radius: 6px; padding: 5px 8px; font: 9pt 'Segoe UI'; }
QPushButton:hover { background: #3a4767; }
QPushButton:checked { background: #5b7bd5; border-color: #7d98e6; }
QPushButton#draw { background: #3f7d5a; border-color: #58a078; }
QPushButton#draw:hover { background: #4b9a6d; }
QFrame#update { background: #24352d; border: 1px solid #3f7d5a; border-radius: 6px; }
QLabel#updatetext { color: #c8f0d4; font: 9pt 'Segoe UI'; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #3a4258; border-radius: 4px; min-height: 20px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QMenu { background: #262c3d; color: #e6ebf7; border: 1px solid #3a4258; }
QMenu::item:selected { background: #5b7bd5; }
"""


class Board(QWidget):
    add_art = Signal(str)
    draw_new = Signal()
    edit_art = Signal(str)
    delete_art = Signal(str)
    lock_toggled = Signal(bool)
    hide_toggled = Signal(bool)
    clear_park = Signal()
    weather_changed = Signal(str)
    weather_auto = Signal(bool)
    update_open = Signal()
    update_later = Signal()
    moved = Signal()
    closed = Signal()

    def __init__(self, library):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Desktop Park")
        self.library = library
        self._drag = None
        self.collapsed = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # the window always shrinks or grows to fit what is showing (folding,
        # the update bar); a plain adjustSize() measured before the hide landed
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.frame = QFrame(objectName="board")
        outer.addWidget(self.frame)
        self.frame.setStyleSheet(STYLE)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(6)
        self._lay = lay

        head = QHBoxLayout()
        head.setSpacing(4)
        self.logo = QLabel()
        self.logo.setPixmap(library.thumbnail("fish", 20))
        self.logo.setToolTip("Desktop Park - drag me anywhere, even into the taskbar")
        self.title = QLabel("Desktop Park", objectName="title")
        head.addWidget(self.logo)
        head.addWidget(self.title)

        # the folded bar's quick controls: weather, hide, lock (and "new version")
        self.quick = QWidget()
        q = QHBoxLayout(self.quick)
        q.setContentsMargins(6, 0, 0, 0)
        q.setSpacing(4)
        self.quick_weather = QToolButton(objectName="quick")
        self.quick_weather.setIconSize(QSize(18, 18))
        self.quick_weather.setPopupMode(QToolButton.InstantPopup)
        self.quick_weather.setToolTip("Weather")
        self.quick_weather.setMenu(self._weather_menu())
        self.quick_hide = QToolButton(objectName="quick", checkable=True)
        self.quick_hide.setIcon(QIcon(_icon(artmod.UI_ICONS["eye"])))
        self.quick_hide.setIconSize(QSize(18, 18))
        self.quick_hide.setToolTip("Hide the park")
        self.quick_hide.toggled.connect(self._hide)
        self.quick_lock = QToolButton(objectName="quick", checkable=True)
        self.quick_lock.setIcon(QIcon(_icon(artmod.UI_ICONS["lock"])))
        self.quick_lock.setIconSize(QSize(18, 18))
        self.quick_lock.setToolTip("Lock: clicks go through everything in the park")
        self.quick_lock.toggled.connect(self._lock)
        self.quick_update = QToolButton(text="New!", objectName="newver")
        self.quick_update.clicked.connect(self.update_open.emit)
        self.quick_update.hide()
        for w in (self.quick_weather, self.quick_hide, self.quick_lock, self.quick_update):
            q.addWidget(w)
        self.quick.hide()
        head.addWidget(self.quick)
        head.addStretch(1)
        self.fold_btn = QToolButton(text="–", objectName="head")
        self.fold_btn.setToolTip("Fold the board")
        self.fold_btn.clicked.connect(self.toggle_collapsed)
        close_btn = QToolButton(text="×", objectName="head")
        close_btn.setToolTip("Hide the board (bring it back from the tray icon)")
        close_btn.clicked.connect(self._close)
        head.addWidget(self.fold_btn)
        head.addWidget(close_btn)
        lay.addLayout(head)

        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(6)
        # shown only when a newer version is on GitHub (visible even when folded)
        self.update_bar = QFrame(objectName="update")
        ub = QHBoxLayout(self.update_bar)
        ub.setContentsMargins(8, 4, 4, 4)
        ub.setSpacing(4)
        self.update_text = QLabel("", objectName="updatetext")
        get = QPushButton("Get it", objectName="draw")
        get.setToolTip("Open the download page on GitHub")
        get.clicked.connect(self.update_open.emit)
        later = QPushButton("Later")
        later.setToolTip("Don't remind me about this version")
        later.clicked.connect(self.update_later.emit)
        ub.addWidget(self.update_text, 1)
        ub.addWidget(get)
        ub.addWidget(later)
        self.update_bar.hide()
        lay.addWidget(self.update_bar)
        lay.addWidget(self.body)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(360)
        self.grid_host = QWidget()
        self.grid = QVBoxLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 4, 0)
        self.grid.setSpacing(2)
        self.scroll.setWidget(self.grid_host)
        body.addWidget(self.scroll)

        draw = QPushButton("✏  Draw your own", objectName="draw")
        draw.clicked.connect(self.draw_new.emit)
        body.addWidget(draw)

        body.addWidget(QLabel("WEATHER", objectName="section"))
        wrow = QHBoxLayout()
        wrow.setSpacing(4)
        self.weather_btns = {}
        for kind in weathermod.KINDS:
            b = QPushButton(checkable=True)
            b.setToolTip(weathermod.LABELS[kind])
            if kind in artmod.WEATHER_ICONS:
                b.setIcon(QIcon(_icon(artmod.WEATHER_ICONS[kind])))
                b.setIconSize(QSize(18, 18))
            else:
                b.setText("Off")
                b.setToolTip("No weather")
            b.setFixedHeight(30)
            b.clicked.connect(lambda _=False, k=kind: self._pick_weather(k))
            wrow.addWidget(b)
            self.weather_btns[kind] = b
        self.auto_btn = QPushButton("Auto", checkable=True)
        self.auto_btn.setFixedHeight(30)
        self.auto_btn.setToolTip("Let the weather change by itself every few minutes")
        self.auto_btn.toggled.connect(self.weather_auto.emit)
        wrow.addWidget(self.auto_btn)
        body.addLayout(wrow)

        row = QHBoxLayout()
        self.lock_btn = QPushButton("Lock", checkable=True)
        self.lock_btn.setToolTip("Lock: clicks go through everything in the park")
        self.lock_btn.toggled.connect(self._lock)
        self.hide_btn = QPushButton("Hide park", checkable=True)
        self.hide_btn.toggled.connect(self._hide)
        clear = QPushButton("Clear")
        clear.setToolTip("Remove everything from the park")
        clear.clicked.connect(self.clear_park.emit)
        row.addWidget(self.lock_btn)
        row.addWidget(self.hide_btn)
        row.addWidget(clear)
        self.screen_btn = QPushButton("Screen")
        self.screen_btn.setToolTip("Move the park to another monitor")
        self.screen_btn.setVisible(False)
        row.addWidget(self.screen_btn)
        body.addLayout(row)

        hint = QLabel("Click a picture to add it. In the park: drag to move,\n"
                      "click to poke, scroll to resize, right-click for options.",
                      objectName="hint")
        body.addWidget(hint)

        self.frame.setFixedWidth(FULL_WIDTH)
        self.rebuild()

    # -- picture grid --------------------------------------------------------
    def rebuild(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        pets = [a for a in self.library.builtin.values() if a["kind"] == "pet"]
        decos = [a for a in self.library.builtin.values() if a["kind"] != "pet"]
        mine = self.library.custom_list()
        self._section("PETS", pets)
        self._section("NATURE & DECOR", decos)
        if mine:
            self._section("MY DRAWINGS  (right-click to edit)", mine, custom=True)
        else:
            self.grid.addWidget(QLabel("MY DRAWINGS", objectName="section"))
            self.grid.addWidget(QLabel("Nothing yet - press “Draw your own”.",
                                       objectName="hint"))
        self.grid.addStretch(1)

    def _section(self, label, pictures, custom=False):
        self.grid.addWidget(QLabel(label, objectName="section"))
        host = QWidget()
        g = QGridLayout(host)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(4)
        for i, picture in enumerate(pictures):
            b = QToolButton(objectName="thumb")
            b.setIcon(QIcon(self.library.thumbnail(picture["id"], 36)))
            b.setIconSize(QSize(36, 36))
            b.setFixedSize(46, 46)
            b.setToolTip(picture["name"])
            b.clicked.connect(lambda _=False, i=picture["id"]: self.add_art.emit(i))
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(
                lambda pos, i=picture["id"], b=b, c=custom: self._thumb_menu(i, b.mapToGlobal(pos), c))
            g.addWidget(b, i // COLS, i % COLS)
        for c in range(COLS):
            g.setColumnStretch(c, 0)
        g.setColumnStretch(COLS, 1)
        self.grid.addWidget(host)

    def _thumb_menu(self, art_id, pos, custom):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE)
        menu.addAction("Add to park", lambda: self.add_art.emit(art_id))
        if custom:
            menu.addAction("Edit drawing", lambda: self.edit_art.emit(art_id))
            menu.addAction("Delete drawing", lambda: self.delete_art.emit(art_id))
        else:
            menu.addAction("Draw my own version", lambda: self.edit_art.emit(art_id))
        menu.exec(pos)

    # -- buttons -------------------------------------------------------------
    # Lock and hide each have two buttons (board + folded bar) kept in step.
    def _lock(self, on):
        self.set_locked(on)
        self.lock_toggled.emit(on)

    def _hide(self, on):
        self.set_hidden(on)
        self.hide_toggled.emit(on)

    def set_locked(self, on):
        for b in (self.lock_btn, self.quick_lock):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)
        self.lock_btn.setText("Locked" if on else "Lock")
        self.quick_lock.setToolTip("Unlock the park" if on else
                                   "Lock: clicks go through everything in the park")

    def _weather_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE)
        group = QActionGroup(menu)
        self._weather_actions = {}
        for kind in weathermod.KINDS:
            a = menu.addAction(QIcon(_icon(artmod.WEATHER_ICONS[kind])), weathermod.LABELS[kind])
            a.setCheckable(True)
            group.addAction(a)
            a.triggered.connect(lambda _=False, k=kind: self._pick_weather(k))
            self._weather_actions[kind] = a
        menu.addSeparator()
        self._auto_action = menu.addAction("Auto (changes by itself)")
        self._auto_action.setCheckable(True)
        self._auto_action.triggered.connect(lambda on: self.auto_btn.setChecked(on))
        return menu

    def _pick_weather(self, kind):
        self.set_weather(kind)
        self.weather_changed.emit(kind)

    def set_weather(self, kind):
        for k, b in self.weather_btns.items():
            b.setChecked(k == kind)
        for k, a in self._weather_actions.items():
            a.setChecked(k == kind)
        self.quick_weather.setIcon(QIcon(_icon(artmod.WEATHER_ICONS.get(kind, artmod.WEATHER_ICONS["clear"]))))
        self.quick_weather.setToolTip("Weather: %s" % weathermod.LABELS.get(kind, kind))

    def set_weather_auto(self, on):
        for b in (self.auto_btn, self._auto_action):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)

    def set_update(self, version):
        self._update_version = version
        if version:
            self.update_text.setText("Version %s is out!" % version)
            self.quick_update.setToolTip("Version %s is out - click to download" % version)
        self._keep_bottom(self._show_update_parts)

    def _show_update_parts(self):
        version = getattr(self, "_update_version", None)
        # big bar on the open board, a small "New!" button on the folded bar
        self.update_bar.setVisible(bool(version) and not self.collapsed)
        self.quick_update.setVisible(bool(version) and self.collapsed)

    def set_screen_menu(self, menu, show):
        """The app hands over the menu listing the monitors."""
        menu.setStyleSheet(STYLE)
        self.screen_btn.setMenu(menu)
        self.screen_btn.setVisible(show)

    def set_hidden(self, on):
        for b in (self.hide_btn, self.quick_hide):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)
        self.hide_btn.setText("Show park" if on else "Hide park")
        self.quick_hide.setToolTip("Show the park" if on else "Hide the park")

    def toggle_collapsed(self):
        self.set_collapsed(not self.collapsed)
        self.moved.emit()

    def set_collapsed(self, on):
        """Folded, the board is a slim bar of quick controls that fits in the
        taskbar. Its bottom edge stays put, so opening grows it upward."""
        def change():
            self.collapsed = on
            self.body.setVisible(not on)
            self.title.setVisible(not on)
            self.quick.setVisible(on)
            if on:
                self._lay.setContentsMargins(6, 4, 4, 4)
                self.frame.setMinimumWidth(0)
                self.frame.setMaximumWidth(16777215)
            else:
                self._lay.setContentsMargins(10, 6, 10, 10)
                self.frame.setFixedWidth(FULL_WIDTH)
            self.fold_btn.setText("\u25b4" if on else "\u2013")
            self.fold_btn.setToolTip("Open the board (it grows upward)" if on else "Fold the board")
            self._show_update_parts()
        self._keep_bottom(change)

    def _keep_bottom(self, change):
        """Make a change that resizes the board, keeping its bottom-left corner
        where it is, and the whole board on its screen."""
        shown = self.isVisible()
        left, bottom = self.x(), self.y() + self.height()
        change()
        self.layout().activate()
        if shown:
            screen = (QGuiApplication.screenAt(QPoint(left + 10, bottom - 5))
                      or self.screen())
            self.place(left, bottom - self.height(), screen.geometry())

    def _close(self):
        self.hide()
        self.closed.emit()

    # -- dragging by the title bar --------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 34:
            self._drag = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            self._drag = None
            self.moved.emit()

    def mouseDoubleClickEvent(self, e):
        if e.position().y() < 34:
            self.toggle_collapsed()

    def place(self, x, y, screen_rect):
        """Move to (x, y), but keep the whole board on that screen. The screen
        rect includes the taskbar, so the folded bar may live inside it."""
        x = min(max(x, screen_rect.left()), screen_rect.right() + 1 - self.width())
        y = min(max(y, screen_rect.top()), screen_rect.bottom() + 1 - self.height())
        self.move(QPoint(int(x), int(y)))


def _icon(rows):
    pic = {"palette": artmod.WEATHER_ICON_PALETTE, "frames": [rows]}
    img = frame_image(pic, rows)
    return QPixmap.fromImage(img.scaled(img.width() * 2, img.height() * 2))
