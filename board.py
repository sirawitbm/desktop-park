"""The floating control board: pick things to add, draw your own, lock or
hide the park. Drag it by the title bar; "-" folds it down to just the bar."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu,
                               QPushButton, QScrollArea, QToolButton,
                               QVBoxLayout, QWidget)

COLS = 5
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
QPushButton { color: #e6ebf7; background: #2c3449; border: 1px solid #3a4258;
              border-radius: 6px; padding: 5px 8px; font: 9pt 'Segoe UI'; }
QPushButton:hover { background: #3a4767; }
QPushButton:checked { background: #5b7bd5; border-color: #7d98e6; }
QPushButton#draw { background: #3f7d5a; border-color: #58a078; }
QPushButton#draw:hover { background: #4b9a6d; }
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
        self.frame = QFrame(objectName="board")
        outer.addWidget(self.frame)
        self.frame.setStyleSheet(STYLE)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(6)

        head = QHBoxLayout()
        title = QLabel("Desktop Park", objectName="title")
        head.addWidget(title)
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
        body.addLayout(row)

        hint = QLabel("Click a picture to add it. In the park: drag to move,\n"
                      "click to poke, scroll to resize, right-click for options.",
                      objectName="hint")
        body.addWidget(hint)

        self.setFixedWidth(COLS * 50 + 34)
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
    def _lock(self, on):
        self.lock_btn.setText("Locked" if on else "Lock")
        self.lock_toggled.emit(on)

    def _hide(self, on):
        self.hide_btn.setText("Show park" if on else "Hide park")
        self.hide_toggled.emit(on)

    def set_locked(self, on):
        self.lock_btn.blockSignals(True)
        self.lock_btn.setChecked(on)
        self.lock_btn.setText("Locked" if on else "Lock")
        self.lock_btn.blockSignals(False)

    def set_hidden(self, on):
        self.hide_btn.blockSignals(True)
        self.hide_btn.setChecked(on)
        self.hide_btn.setText("Show park" if on else "Hide park")
        self.hide_btn.blockSignals(False)

    def toggle_collapsed(self):
        self.set_collapsed(not self.collapsed)
        self.moved.emit()

    def set_collapsed(self, on):
        self.collapsed = on
        self.body.setVisible(not on)
        self.fold_btn.setText("+" if on else "–")
        self.fold_btn.setToolTip("Open the board" if on else "Fold the board")
        self.adjustSize()

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
        x = min(max(x, screen_rect.left()), screen_rect.right() - self.width())
        y = min(max(y, screen_rect.top()), screen_rect.bottom() - 40)
        self.move(QPoint(int(x), int(y)))
