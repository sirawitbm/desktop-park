"""The floating control board: pick things to add, draw your own, change the
weather, lock or hide the park. Drag it by the title bar. Folded, it becomes
a slim hotbar that fits inside the Windows taskbar."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QActionGroup, QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout, QMenu,
                               QPushButton, QScrollArea, QToolButton,
                               QVBoxLayout, QWidget)

import art as artmod
import ui_style
import weather as weathermod
from sprites import frame_image

COLS = 5
SLOT = 46
FULL_WIDTH = COLS * SLOT + (COLS - 1) * 4 + 50
ICON = QSize(18, 18)


def _icon(rows, scale=2):
    pic = {"palette": artmod.WEATHER_ICON_PALETTE, "frames": [rows]}
    img = frame_image(pic, rows)
    return QPixmap.fromImage(img.scaled(img.width() * scale, img.height() * scale))


def _ui_icon(name, scale=2):
    rows = artmod.UI_ICONS.get(name) or artmod.WEATHER_ICONS[name]
    return QIcon(_icon(rows, scale))


def _button(text="", icon=None, tip="", checkable=False, name=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    if icon:
        b.setIcon(_ui_icon(icon))
        b.setIconSize(ICON)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


def _square(icon, tip, name="head", size=22, scale=2, checkable=False):
    b = QToolButton(objectName=name)
    b.setIcon(_ui_icon(icon, scale))
    b.setIconSize(QSize(size - 8, size - 8))
    b.setFixedSize(size, size)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


def _section(text):
    return QLabel(text, objectName="section")


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
        ui_style.install()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Desktop Park")
        self.library = library
        self._drag = None
        self.collapsed = False
        self._update_version = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # the window always shrinks or grows to fit what is showing (folding,
        # the update bar); a plain adjustSize() measured before the hide landed
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.frame = QFrame(objectName="board")
        outer.addWidget(self.frame)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(6, 6, 6, 8)
        lay.setSpacing(4)
        self._lay = lay

        # -- title bar (also the folded hotbar) ----------------------------------
        self.titlebar = QFrame(objectName="titlebar")
        head = QHBoxLayout(self.titlebar)
        head.setContentsMargins(6, 3, 3, 3)
        head.setSpacing(4)
        self.logo = QLabel()
        self.logo.setPixmap(library.thumbnail("fish", 24))
        self.logo.setToolTip("Desktop Park - drag me anywhere, even into the taskbar")
        self.title = QLabel("DESKTOP PARK", objectName="title")
        head.addWidget(self.logo)
        head.addWidget(self.title)

        # the folded bar's quick controls: weather, hide, lock (and "new version")
        self.quick = QWidget()
        q = QHBoxLayout(self.quick)
        q.setContentsMargins(4, 0, 0, 0)
        q.setSpacing(3)
        self.quick_weather = _square("clear", "Weather", name="quick", size=28)
        self.quick_weather.setPopupMode(QToolButton.InstantPopup)
        self.quick_weather.setMenu(self._weather_menu())
        self.quick_hide = _square("eye", "Hide the park", name="quick", size=28, checkable=True)
        self.quick_hide.toggled.connect(self._hide)
        self.quick_lock = _square("lock", "Lock: clicks go through everything in the park",
                                  name="quick", size=28, checkable=True)
        self.quick_lock.toggled.connect(self._lock)
        self.quick_update = QToolButton(text="NEW!", objectName="newver")
        self.quick_update.setFixedHeight(28)
        self.quick_update.clicked.connect(self.update_open.emit)
        self.quick_update.hide()
        for w in (self.quick_weather, self.quick_hide, self.quick_lock, self.quick_update):
            q.addWidget(w)
        self.quick.hide()
        head.addWidget(self.quick)
        head.addStretch(1)
        self.fold_btn = _square("min", "Fold the board", scale=2)
        self.fold_btn.clicked.connect(self.toggle_collapsed)
        close_btn = _square("close", "Hide the board (bring it back from the tray icon)",
                            name="close", scale=2)
        close_btn.clicked.connect(self._close)
        head.addWidget(self.fold_btn)
        head.addWidget(close_btn)
        lay.addWidget(self.titlebar)

        # -- update notice ----------------------------------------------------------
        self.update_bar = QFrame(objectName="update")
        ub = QHBoxLayout(self.update_bar)
        ub.setContentsMargins(8, 3, 3, 3)
        ub.setSpacing(4)
        self.update_text = QLabel("", objectName="updatetext")
        get = _button("Get it", tip="Open the download page on GitHub", name="draw")
        get.clicked.connect(self.update_open.emit)
        later = _button("Later", tip="Don't remind me about this version")
        later.clicked.connect(self.update_later.emit)
        ub.addWidget(self.update_text, 1)
        ub.addWidget(get)
        ub.addWidget(later)
        self.update_bar.hide()
        lay.addWidget(self.update_bar)

        # -- body ------------------------------------------------------------------
        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(2, 0, 2, 0)
        body.setSpacing(4)
        lay.addWidget(self.body)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(330)
        self.grid_host = QWidget()
        self.grid = QVBoxLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 6, 0)
        self.grid.setSpacing(2)
        self.scroll.setWidget(self.grid_host)
        body.addWidget(self.scroll)

        draw = _button("Draw your own", icon="pencil", name="draw",
                       tip="Draw a new pet or decoration")
        draw.setFixedHeight(34)
        draw.clicked.connect(self.draw_new.emit)
        body.addWidget(draw)

        body.addWidget(_section("WEATHER"))
        wrow = QHBoxLayout()
        wrow.setSpacing(4)
        self.weather_btns = {}
        for kind in weathermod.KINDS:
            tip = "No weather" if kind == "clear" else weathermod.LABELS[kind]
            b = _square(kind, tip, name="wbtn", size=34, checkable=True)
            b.clicked.connect(lambda _=False, k=kind: self._pick_weather(k))
            wrow.addWidget(b)
            self.weather_btns[kind] = b
        self.auto_btn = _button("Auto", checkable=True,
                                tip="Let the weather change by itself every few minutes")
        self.auto_btn.setFixedHeight(34)
        self.auto_btn.toggled.connect(self.weather_auto.emit)
        wrow.addWidget(self.auto_btn, 1)
        body.addLayout(wrow)

        body.addWidget(_section("PARK"))
        row = QHBoxLayout()
        row.setSpacing(4)
        self.lock_btn = _button("Lock", icon="lock", checkable=True,
                                tip="Lock: clicks go through everything in the park")
        self.lock_btn.toggled.connect(self._lock)
        self.hide_btn = _button("Hide", icon="eye", checkable=True, tip="Hide the park")
        self.hide_btn.toggled.connect(self._hide)
        clear = _button("Clear", icon="trash", tip="Remove everything from the park")
        clear.clicked.connect(self.clear_park.emit)
        self.screen_btn = _button("", icon="screen", tip="Move the park to another monitor")
        self.screen_btn.setVisible(False)
        for b in (self.lock_btn, self.hide_btn, clear, self.screen_btn):
            b.setFixedHeight(32)
            row.addWidget(b)
        body.addLayout(row)

        hint = QLabel("CLICK A PICTURE TO ADD IT.\nIN THE PARK: DRAG, CLICK, SCROLL,\n"
                      "RIGHT-CLICK FOR MORE.", objectName="hint")
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
        self._slots("PETS", pets)
        self._slots("NATURE & DECOR", decos)
        if mine:
            self._slots("MY DRAWINGS", mine, custom=True)
        else:
            self.grid.addWidget(_section("MY DRAWINGS"))
            self.grid.addWidget(QLabel("Nothing yet - draw one below!", objectName="empty"))
        self.grid.addStretch(1)

    def _slots(self, label, pictures, custom=False):
        self.grid.addWidget(_section(label))
        host = QWidget()
        g = QGridLayout(host)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(4)
        for i, picture in enumerate(pictures):
            b = QToolButton(objectName="thumb")
            b.setIcon(QIcon(self.library.thumbnail(picture["id"], 38)))
            b.setIconSize(QSize(38, 38))
            b.setFixedSize(SLOT, SLOT)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(picture["name"] + ("  (right-click to edit)" if custom else ""))
            b.clicked.connect(lambda _=False, i=picture["id"]: self.add_art.emit(i))
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(
                lambda pos, i=picture["id"], b=b, c=custom: self._thumb_menu(i, b.mapToGlobal(pos), c))
            g.addWidget(b, i // COLS, i % COLS)
        g.setColumnStretch(COLS, 1)
        self.grid.addWidget(host)

    def _thumb_menu(self, art_id, pos, custom):
        menu = QMenu(self)
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
        group = QActionGroup(menu)
        self._weather_actions = {}
        for kind in weathermod.KINDS:
            a = menu.addAction(_ui_icon(kind), weathermod.LABELS[kind])
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
        self.quick_weather.setIcon(_ui_icon(kind if kind in artmod.WEATHER_ICONS else "clear"))
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
        version = self._update_version
        # big bar on the open board, a small "NEW!" button on the folded bar
        self.update_bar.setVisible(bool(version) and not self.collapsed)
        self.quick_update.setVisible(bool(version) and self.collapsed)

    def set_screen_menu(self, menu, show):
        """The app hands over the menu listing the monitors."""
        self.screen_btn.setMenu(menu)
        self.screen_btn.setVisible(show)

    def set_hidden(self, on):
        for b in (self.hide_btn, self.quick_hide):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)
        self.hide_btn.setText("Show" if on else "Hide")
        self.quick_hide.setToolTip("Show the park" if on else "Hide the park")

    def toggle_collapsed(self):
        self.set_collapsed(not self.collapsed)
        self.moved.emit()

    def set_collapsed(self, on):
        """Folded, the board is a slim hotbar of quick controls that fits in
        the taskbar. Its bottom edge stays put, so opening grows it upward."""
        def change():
            self.collapsed = on
            self.body.setVisible(not on)
            self.title.setVisible(not on)
            self.quick.setVisible(on)
            if on:
                self._lay.setContentsMargins(0, 0, 0, 0)
                self.frame.setMinimumWidth(0)
                self.frame.setMaximumWidth(16777215)
            else:
                self._lay.setContentsMargins(6, 6, 6, 8)
                self.frame.setFixedWidth(FULL_WIDTH)
            # folded, the hotbar is the whole window: drop the outer frame
            self.frame.setStyleSheet(
                "QFrame#board { border-image: none; border-width: 0px; }" if on else "")
            self.fold_btn.setIcon(_ui_icon("up" if on else "min"))
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
    def _on_titlebar(self, pos):
        return self.titlebar.geometry().contains(self.frame.mapFrom(self, pos.toPoint()))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._on_titlebar(e.position()):
            self._drag = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        if self._drag is not None:
            self._drag = None
            self.moved.emit()

    def mouseDoubleClickEvent(self, e):
        if self._on_titlebar(e.position()):
            self.toggle_collapsed()

    def place(self, x, y, screen_rect):
        """Move to (x, y), but keep the whole board on that screen. The screen
        rect includes the taskbar, so the folded bar may live inside it."""
        x = min(max(x, screen_rect.left()), screen_rect.right() + 1 - self.width())
        y = min(max(y, screen_rect.top()), screen_rect.bottom() + 1 - self.height())
        self.move(QPoint(int(x), int(y)))
