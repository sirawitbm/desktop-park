"""The floating control board: pick things to add, draw your own, change the
weather, lock or hide the park. Drag it by the title bar. Folded, it becomes
a slim bar of quick controls that fits inside the Windows taskbar.

It comes in two looks (ui_style.py), switched with apply_theme()."""

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QActionGroup, QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout, QMenu,
                               QPushButton, QScrollArea, QSizePolicy, QToolButton,
                               QStyle, QVBoxLayout, QWidget)

import art as artmod
import daycycle
import ui_style
import weather as weathermod
from sprites import app_icon_pixmap, frame_image

COLS = 5
SLOT = 46
ICON = QSize(18, 18)
TIME_ICONS = {"clock": "clock", "day": "day", "night": "moon"}
TIME_TEXT = {"clock": " Clock", "day": " Day", "night": " Night"}   # space: gap after the icon

# What the board says and shows in each look.
LOOK = {
    "modern": {
        "width": COLS * 50 + 34, "margins": (10, 6, 10, 10), "head_margins": (0, 0, 0, 0),
        "folded_margins": (8, 4, 4, 4), "scroll": 360, "slot_icon": 36, "icons": False,
        "draw": "✏  Draw your own", "lock": ("Lock", "Locked"), "hide": ("Hide park", "Show park"),
        "clear": "Clear", "screen": "Screen", "logo_open": False,
        "sections": ("PETS", "NATURE & DECOR", "MY DRAWINGS  (right-click to edit)", "MY DRAWINGS"),
        "empty": "Nothing yet - press “Draw your own”.",
        "hint": "Click a picture to add it. In the park: drag to move,\n"
                "click to poke, scroll to resize, right-click for options.",
    },
    "pixel": {
        "width": COLS * SLOT + (COLS - 1) * 4 + 74, "margins": (6, 6, 6, 8), "head_margins": (6, 3, 3, 3),
        "folded_margins": (6, 1, 1, 1), "scroll": 330, "slot_icon": 38, "icons": True,
        "draw": " Draw your own", "lock": (" Lock", " Locked"), "hide": (" Hide", " Show"),
        "clear": " Clear", "screen": "", "logo_open": True,
        "sections": ("Pets", "Nature & decor", "My drawings", "My drawings"),
        "empty": "Nothing yet - draw one below!",
        "hint": "Drag things, click pets, scroll to resize, right-click for more.",
    },
}


def _icon(rows, scale=2):
    pic = {"palette": artmod.WEATHER_ICON_PALETTE, "frames": [rows]}
    img = frame_image(pic, rows)
    return QPixmap.fromImage(img.scaled(img.width() * scale, img.height() * scale))


def _ui_icon(name, scale=2):
    rows = artmod.UI_ICONS.get(name) or artmod.WEATHER_ICONS[name]
    return QIcon(_icon(rows, scale))


def _button(text="", tip="", checkable=False, name=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


def _square(icon, tip, name="head", size=22, checkable=False):
    b = QToolButton(objectName=name)
    if icon:
        b.setIcon(_ui_icon(icon))
        b.setIconSize(ICON)
    b.setFixedSize(size, size)
    b.setToolTip(tip)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


def _sep():
    s = QFrame(objectName="qsep")
    s.setFixedSize(1, 18)
    return s


class PictureButton(QToolButton):
    def __init__(self, library, picture):
        super().__init__(objectName="thumb")
        self.library = library
        self.picture = picture
        self._preview = None

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            self.preview()
            self._preview.adjustSize()
            area = self.screen().availableGeometry()
            point = event.globalPos() + QPoint(14, 14)
            x = min(max(area.left(), point.x()), area.right() + 1 - self._preview.width())
            y = min(max(area.top(), point.y()), area.bottom() + 1 - self._preview.height())
            self._preview.move(x, y)
            self._preview.show()
            return True
        if event.type() == QEvent.Leave and self._preview is not None:
            self._preview.hide()
        return super().event(event)

    def preview(self):
        if self._preview is None:
            self._preview = QFrame(self, Qt.ToolTip)
            self._preview.setObjectName("board")
            layout = QVBoxLayout(self._preview)
            image = QLabel()
            image.setFixedSize(96, 96)
            image.setAlignment(Qt.AlignCenter)
            image.setPixmap(self.library.thumbnail(self.picture["id"], 96, max_scale=6))
            name = QLabel(self.picture["name"])
            name.setTextFormat(Qt.PlainText)
            name.setWordWrap(True)
            name.setFixedWidth(120)
            name.setAlignment(Qt.AlignCenter)
            layout.addWidget(image, 0, Qt.AlignCenter)
            layout.addWidget(name)
        return self._preview


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
    time_mode_changed = Signal(str)
    show_sky_toggled = Signal(bool)
    update_open = Signal()
    update_later = Signal()
    retry_save = Signal()
    undo_park = Signal()
    preset_save = Signal()
    preset_load = Signal(str)
    preset_rename = Signal(str)
    preset_delete = Signal(str)
    import_art = Signal()
    export_art = Signal(str)
    low_power_toggled = Signal(bool)
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
        self._save_error = None
        self._locked = self._hidden = False
        self.look = LOOK[ui_style.current()]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # the window always shrinks or grows to fit what is showing (folding,
        # the update bar); a plain adjustSize() measured before the hide landed
        outer.setSizeConstraint(QLayout.SetFixedSize)
        self.frame = QFrame(objectName="board")
        outer.addWidget(self.frame)
        lay = QVBoxLayout(self.frame)
        lay.setSpacing(6)
        self._lay = lay

        # -- title bar (also the folded bar) -----------------------------------------
        self.titlebar = QFrame(objectName="titlebar")
        head = QHBoxLayout(self.titlebar)
        head.setSpacing(4)
        self._head = head
        self.logo = QLabel()
        self.logo.setPixmap(app_icon_pixmap(2))
        self.logo.setToolTip("Desktop Park - drag me anywhere, even into the taskbar")
        self.title = QLabel("Desktop Park", objectName="title")
        head.addWidget(self.logo)
        head.addWidget(self.title)

        # the folded bar's quick controls: weather, hide, lock (and "new version")
        self.quick = QWidget()
        q = QHBoxLayout(self.quick)
        q.setContentsMargins(2, 0, 0, 0)
        q.setSpacing(3)
        self.quick_weather = _square("clear", "Weather", name="quick", size=30)
        self.quick_weather.setPopupMode(QToolButton.InstantPopup)
        self.quick_weather.setMenu(self._weather_menu())
        self.quick_time = _square("clock", "Time of day", name="quick", size=30)
        self.quick_time.setPopupMode(QToolButton.InstantPopup)
        self.quick_time.setMenu(self._time_menu())
        self.quick_hide = _square("eye", "Hide the park", name="quick", size=30, checkable=True)
        self.quick_hide.toggled.connect(self._hide)
        self.quick_lock = _square("lock", "Lock: clicks go through everything in the park",
                                  name="quick", size=30, checkable=True)
        self.quick_lock.toggled.connect(self._lock)
        self.quick_update = QToolButton(text="New!", objectName="newver")
        self.quick_update.setFixedHeight(24)
        self.quick_update.setCursor(Qt.PointingHandCursor)
        self.quick_update.clicked.connect(self.update_open.emit)
        self.quick_update.hide()
        self.quick_save = QToolButton(text="!", objectName="quick")
        self.quick_save.setFixedSize(30, 30)
        self.quick_save.clicked.connect(self.retry_save.emit)
        self.quick_save.hide()
        q.addWidget(_sep())
        for w in (self.quick_weather, self.quick_time, self.quick_hide, self.quick_lock,
              self.quick_update, self.quick_save):
            q.addWidget(w)
        q.addWidget(_sep())
        self.quick.hide()
        head.addWidget(self.quick)
        head.addStretch(1)
        self.undo_btn = QToolButton(objectName="head")
        self.undo_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.undo_btn.setFixedSize(22, 22)
        self.undo_btn.setToolTip("Undo last park edit")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_park.emit)
        head.addWidget(self.undo_btn)
        self.fold_btn = _square(None, "Fold the board")
        self.fold_btn.clicked.connect(self.toggle_collapsed)
        self.close_btn = _square(None, "Hide the board (bring it back from the tray icon)", name="close")
        self.close_btn.clicked.connect(self._close)
        head.addWidget(self.fold_btn)
        head.addWidget(self.close_btn)
        lay.addWidget(self.titlebar)

        # -- update notice ----------------------------------------------------------
        self.update_bar = QFrame(objectName="update")
        ub = QHBoxLayout(self.update_bar)
        ub.setContentsMargins(8, 4, 4, 4)
        ub.setSpacing(4)
        self.update_text = QLabel("", objectName="updatetext")
        get = _button("Get it", "Open the download page on GitHub", name="draw")
        get.clicked.connect(self.update_open.emit)
        later = _button("Later", "Don't remind me about this version")
        later.clicked.connect(self.update_later.emit)
        ub.addWidget(self.update_text, 1)
        ub.addWidget(get)
        ub.addWidget(later)
        self.update_bar.hide()
        lay.addWidget(self.update_bar)

        self.save_bar = QFrame(objectName="savewarning")
        save_row = QHBoxLayout(self.save_bar)
        save_row.setContentsMargins(8, 4, 4, 4)
        self.save_text = QLabel("Changes not saved", objectName="saveerror")
        self.save_text.setWordWrap(True)
        retry = _button("Retry", "Try saving the park again")
        retry.clicked.connect(self.retry_save.emit)
        save_row.addWidget(self.save_text, 1)
        save_row.addWidget(retry)
        self.save_bar.hide()
        lay.addWidget(self.save_bar)

        # -- body ------------------------------------------------------------------
        self.body = QWidget()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(6)
        lay.addWidget(self.body)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_host = QWidget()
        self.grid = QVBoxLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 4, 0)
        self.grid.setSpacing(2)
        self.scroll.setWidget(self.grid_host)
        body.addWidget(self.scroll)

        self.draw_btn = _button("", "Draw a new pet or decoration", name="draw")
        self.draw_btn.clicked.connect(self.draw_new.emit)
        body.addWidget(self.draw_btn)

        utility = QHBoxLayout()
        utility.setSpacing(4)
        self.presets_btn = QToolButton(text="Parks")
        self.presets_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.presets_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.presets_btn.setToolTip("Saved park arrangements")
        self.presets_btn.setPopupMode(QToolButton.InstantPopup)
        self.presets_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.presets_btn.setMenu(QMenu("Saved parks", self))
        self.set_presets([])
        self.import_btn = QToolButton()
        self.import_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.import_btn.setToolTip("Import a drawing or park pack")
        self.import_btn.setFixedSize(30, 30)
        self.import_btn.clicked.connect(self.import_art.emit)
        self.power_btn = QToolButton()
        self.power_btn.setIcon(_ui_icon("eco"))
        self.power_btn.setToolTip("Low power: fewer animation and weather updates")
        self.power_btn.setCheckable(True)
        self.power_btn.setFixedSize(30, 30)
        self.power_btn.toggled.connect(self.low_power_toggled.emit)
        utility.addWidget(self.presets_btn, 1)
        utility.addWidget(self.import_btn)
        utility.addWidget(self.power_btn)
        body.addLayout(utility)

        self.weather_label = QLabel(objectName="section")
        body.addWidget(self.weather_label)
        wrow = QHBoxLayout()
        wrow.setSpacing(4)
        self.weather_btns = {}
        for kind in weathermod.KINDS:
            tip = "No weather" if kind == "clear" else weathermod.LABELS[kind]
            b = _square(kind, tip, name="wbtn", size=34, checkable=True)
            b.setMinimumWidth(0)
            b.setMaximumWidth(16777215)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)   # share the row evenly
            b.clicked.connect(lambda _=False, k=kind: self._pick_weather(k))
            wrow.addWidget(b, 1)
            self.weather_btns[kind] = b
        self.auto_btn = _button("Auto", "Let the weather change by itself every few minutes",
                                checkable=True)
        self.auto_btn.toggled.connect(self.weather_auto.emit)
        wrow.addWidget(self.auto_btn, 1)
        body.addLayout(wrow)

        self.time_label = QLabel(objectName="section")
        body.addWidget(self.time_label)
        trow = QHBoxLayout()
        trow.setSpacing(4)
        self.time_btns = {}
        for mode in daycycle.MODES:
            b = _button(TIME_TEXT[mode], daycycle.LABELS[mode], checkable=True)
            b.setIcon(_ui_icon(TIME_ICONS[mode]))
            b.setIconSize(ICON)
            b.clicked.connect(lambda _=False, m=mode: self._pick_time(m))
            trow.addWidget(b, 1)
            self.time_btns[mode] = b
        self.sky_btn = _square("sky", "Show the sun and moon crossing the sky", name="wbtn",
                               size=34, checkable=True)
        self.sky_btn.toggled.connect(self._sky)
        trow.addWidget(self.sky_btn)
        body.addLayout(trow)

        self.park_label = QLabel(objectName="section")
        body.addWidget(self.park_label)
        row = QHBoxLayout()
        row.setSpacing(4)
        self.lock_btn = _button("", "Lock: clicks go through everything in the park", checkable=True)
        self.lock_btn.toggled.connect(self._lock)
        self.hide_btn = _button("", "Hide the park", checkable=True)
        self.hide_btn.toggled.connect(self._hide)
        self.clear_btn = _button("", "Remove everything from the park")
        self.clear_btn.clicked.connect(self.clear_park.emit)
        self.screen_btn = _button("", "Move the park to another monitor")
        self.screen_btn.setVisible(False)
        for b in (self.lock_btn, self.hide_btn, self.clear_btn, self.screen_btn):
            row.addWidget(b)
        body.addLayout(row)

        self.hint = QLabel(objectName="hint")
        self.hint.setWordWrap(True)
        body.addWidget(self.hint)

        self.apply_theme(ui_style.current())

    # -- looks -----------------------------------------------------------------
    def apply_theme(self, theme):
        """Switch every label, icon and size to the given look."""
        self._keep_bottom(lambda: self._apply_theme(theme))

    def _apply_theme(self, theme):
        look = self.look = LOOK.get(theme, LOOK["modern"])
        icons = look["icons"]
        self._head.setContentsMargins(*look["head_margins"])
        self.scroll.setFixedHeight(look["scroll"])
        self.title.setText("Desktop Park")
        self.draw_btn.setText(look["draw"])
        self.draw_btn.setIcon(_ui_icon("pencil") if icons else QIcon())
        self.draw_btn.setIconSize(ICON)
        self.weather_label.setText("WEATHER" if not icons else "Weather")
        self.time_label.setText("TIME OF DAY" if not icons else "Time of day")
        self.park_label.setText("PARK" if not icons else "Park")
        self.park_label.setVisible(icons)          # the original look had no "Park" heading
        self.clear_btn.setText(look["clear"])
        self.screen_btn.setText(look["screen"])
        for b, name in ((self.lock_btn, "lock"), (self.hide_btn, "eye"),
                        (self.clear_btn, "trash"), (self.screen_btn, "screen")):
            b.setIcon(_ui_icon(name) if icons else QIcon())
            b.setIconSize(ICON)
            if icons:
                b.setFixedHeight(32)
            else:
                b.setMinimumHeight(0)
                b.setMaximumHeight(16777215)
        off = self.weather_btns["clear"]
        off.setText("" if icons else "Off")
        off.setIcon(_ui_icon("clear") if icons else QIcon())
        off.setIconSize(ICON)
        for b in self.weather_btns.values():
            b.setFixedHeight(34 if icons else 30)
        self.auto_btn.setFixedHeight(34 if icons else 30)
        for b in self.time_btns.values():
            b.setFixedHeight(34 if icons else 30)
        self.sky_btn.setFixedSize(34 if icons else 30, 34 if icons else 30)
        self.draw_btn.setFixedHeight(34 if icons else 30)
        self.hint.setText(look["hint"])
        self.set_locked(self._locked)
        self.set_hidden(self._hidden)
        self._style_fold()
        self.rebuild()

    # -- picture grid --------------------------------------------------------
    def rebuild(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().hide()          # gone at once, not on the next frame
                item.widget().deleteLater()
        pets_label, decor_label, mine_label, empty_label = self.look["sections"]
        everyday = [a for a in self.library.builtin.values() if not a.get("set")]
        spooky = [a for a in self.library.builtin.values() if a.get("set") == "halloween"]
        pets = [a for a in everyday if a["kind"] == "pet"]
        decos = [a for a in everyday if a["kind"] != "pet"]
        mine = self.library.custom_list()
        halloween = "HALLOWEEN" if not self.look["icons"] else "Halloween"
        if daycycle.is_halloween_season():           # October: spooky things first
            self._slots(halloween, spooky)
        self._slots(pets_label, pets)
        self._slots(decor_label, decos)
        if not daycycle.is_halloween_season():
            self._slots(halloween, spooky)
        if mine:
            self._slots(mine_label, mine, custom=True)
        else:
            self.grid.addWidget(QLabel(empty_label, objectName="section"))
            self.grid.addWidget(QLabel(self.look["empty"], objectName="empty"))
        self.grid.addStretch(1)

    def _slots(self, label, pictures, custom=False):
        self.grid.addWidget(QLabel(label, objectName="section"))
        host = QWidget()
        g = QGridLayout(host)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(4)
        size = self.look["slot_icon"]
        for i, picture in enumerate(pictures):
            b = PictureButton(self.library, picture)
            b.setIcon(QIcon(self.library.thumbnail(picture["id"], size, max_scale=2, bottom=True)))
            b.setIconSize(QSize(size, size))
            b.setFixedSize(SLOT, SLOT)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(picture["name"])
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
        menu.addAction("Export drawing...", lambda: self.export_art.emit(art_id))
        menu.exec(pos)

    def set_presets(self, presets):
        menu = self.presets_btn.menu()
        menu.clear()
        menu.addAction("Save current park...", self.preset_save.emit)
        if presets:
            menu.addSeparator()
        for preset in presets:
            name = preset["name"]
            item = menu.addMenu(name.replace("&", "&&"))
            item.addAction("Load", lambda _=False, name=name: self.preset_load.emit(name))
            item.addAction("Rename...", lambda _=False, name=name: self.preset_rename.emit(name))
            item.addAction("Delete...", lambda _=False, name=name: self.preset_delete.emit(name))

    # -- buttons -------------------------------------------------------------
    # Lock and hide each have two buttons (board + folded bar) kept in step.
    def _lock(self, on):
        self.set_locked(on)
        self.lock_toggled.emit(on)

    def _hide(self, on):
        self.set_hidden(on)
        self.hide_toggled.emit(on)

    def set_locked(self, on):
        self._locked = on
        for b in (self.lock_btn, self.quick_lock):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)
        self.lock_btn.setText(self.look["lock"][1 if on else 0])
        self.quick_lock.setToolTip("Unlock the park" if on else
                                   "Lock: clicks go through everything in the park")

    def set_hidden(self, on):
        self._hidden = on
        for b in (self.hide_btn, self.quick_hide):
            b.blockSignals(True)
            b.setChecked(on)
            b.blockSignals(False)
        self.hide_btn.setText(self.look["hide"][1 if on else 0])
        self.quick_hide.setToolTip("Show the park" if on else "Hide the park")

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

    # -- time of day -----------------------------------------------------------
    def _time_menu(self):
        menu = QMenu(self)
        group = QActionGroup(menu)
        self._time_actions = {}
        for mode in daycycle.MODES:
            a = menu.addAction(_ui_icon(TIME_ICONS[mode]), daycycle.LABELS[mode])
            a.setCheckable(True)
            group.addAction(a)
            a.triggered.connect(lambda _=False, m=mode: self._pick_time(m))
            self._time_actions[mode] = a
        menu.addSeparator()
        self._sky_action = menu.addAction(_ui_icon("sky"), "Show sun && moon")
        self._sky_action.setCheckable(True)
        self._sky_action.triggered.connect(self._sky)
        return menu

    def _pick_time(self, mode):
        self.set_time_mode(mode)
        self.time_mode_changed.emit(mode)

    def set_time_mode(self, mode):
        for m, b in self.time_btns.items():
            b.setChecked(m == mode)
        for m, a in self._time_actions.items():
            a.setChecked(m == mode)
        self.quick_time.setIcon(_ui_icon(TIME_ICONS.get(mode, "clock")))
        self.quick_time.setToolTip("Time of day: %s" % daycycle.LABELS.get(mode, mode))

    def _sky(self, on):
        self.set_show_sky(on)
        self.show_sky_toggled.emit(bool(on))

    def set_show_sky(self, on):
        for b in (self.sky_btn, self._sky_action):
            b.blockSignals(True)
            b.setChecked(bool(on))
            b.blockSignals(False)

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
        # big bar on the open board, a small "New!" button on the folded bar
        self.update_bar.setVisible(bool(version) and not self.collapsed)
        self.quick_update.setVisible(bool(version) and self.collapsed)
        self.save_bar.setVisible(bool(self._save_error) and not self.collapsed)
        self.quick_save.setVisible(bool(self._save_error) and self.collapsed)

    def set_save_error(self, error):
        self._save_error = error
        self.save_text.setToolTip(error or "")
        self.quick_save.setToolTip("Changes not saved - click to retry\n" + (error or ""))
        self._keep_bottom(self._show_update_parts)

    def set_undo_available(self, available):
        self.undo_btn.setEnabled(available)

    def set_low_power(self, on):
        self.power_btn.blockSignals(True)
        self.power_btn.setChecked(on)
        self.power_btn.blockSignals(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            self.undo_park.emit()
        else:
            super().keyPressEvent(event)

    def set_screen_menu(self, menu, show):
        """The app hands over the menu listing the monitors."""
        self.screen_btn.setMenu(menu)
        self.screen_btn.setVisible(show)

    # -- folding ----------------------------------------------------------------
    def toggle_collapsed(self):
        self.set_collapsed(not self.collapsed)
        self.moved.emit()

    def set_collapsed(self, on):
        """Folded, the board is a slim bar of quick controls that fits in the
        taskbar. Its bottom edge stays put, so opening grows it upward."""
        def change():
            self.collapsed = on
            self._style_fold()
            self._show_update_parts()
        self._keep_bottom(change)

    def _style_fold(self):
        on, look = self.collapsed, self.look
        self.body.setVisible(not on)
        self.title.setVisible(not on)
        self.quick.setVisible(on)
        self.logo.setVisible(on or look["logo_open"])
        self.frame.setStyleSheet(ui_style.folded_sheet() if on else "")
        if on:
            self._lay.setContentsMargins(0, 0, 0, 0)
            self._head.setContentsMargins(*look["folded_margins"])
            self.frame.setMinimumWidth(0)
            self.frame.setMaximumWidth(16777215)
        else:
            self._lay.setContentsMargins(*look["margins"])
            self._head.setContentsMargins(*look["head_margins"])
            self.frame.setFixedWidth(look["width"])
        if look["icons"]:
            self.fold_btn.setText("")
            self.fold_btn.setIcon(_ui_icon("up" if on else "min"))
            self.close_btn.setText("")
            self.close_btn.setIcon(_ui_icon("close"))
        else:
            self.fold_btn.setIcon(QIcon())
            self.fold_btn.setText("▲" if on else "–")
            self.close_btn.setIcon(QIcon())
            self.close_btn.setText("×")
        size = 26 if (on and not look["icons"]) else 22
        for b in (self.fold_btn, self.close_btn):
            b.setFixedSize(size, size)
        self.fold_btn.setToolTip("Open the board (it grows upward)" if on else "Fold the board")

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
