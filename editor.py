"""The pixel editor: draw a decoration or a pet, optionally with a few
animation frames, and save it to "My drawings"."""

import time

from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QColorDialog, QComboBox, QDialog,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QToolButton,
                               QVBoxLayout, QWidget)

import art as artmod
import ui_style

SIZES = (8, 12, 16, 24, 32)
MAX_FRAMES = 6
def blank(w, h):
    return [[None] * w for _ in range(h)]


class Canvas(QWidget):
    """The grid you paint on. Left button paints, right button erases."""
    edited = Signal()
    picked = Signal(str)

    def __init__(self, editor):
        super().__init__()
        self.ed = editor
        self.setMinimumSize(384, 384)
        self.setMouseTracking(True)
        self._stroke = False
        self._hover = None

    def cell(self):
        w, h = self.ed.w, self.ed.h
        return max(4, min(self.width() // w, self.height() // h))

    def origin(self):
        c = self.cell()
        return ((self.width() - c * self.ed.w) // 2, (self.height() - c * self.ed.h) // 2)

    def to_pixel(self, pos):
        c = self.cell()
        ox, oy = self.origin()
        x, y = int((pos.x() - ox) // c), int((pos.y() - oy) // c)
        if 0 <= x < self.ed.w and 0 <= y < self.ed.h:
            return x, y
        return None

    def paintEvent(self, _):
        p = QPainter(self)
        c = self.cell()
        ox, oy = self.origin()
        w, h = self.ed.w, self.ed.h
        # a mid-grey checkerboard: see-through squares never look like black paint
        light, dark = QColor("#8d93a0"), QColor("#7a808e")
        for y in range(h):
            for x in range(w):
                p.fillRect(ox + x * c, oy + y * c, c, c, light if (x + y) % 2 else dark)
        # faint previous frame, to help line up animation ("onion skin")
        prev = self.ed.onion()
        if prev is not None:
            p.setOpacity(0.25)
            for y, row in enumerate(prev):
                for x, col in enumerate(row):
                    if col:
                        p.fillRect(ox + x * c, oy + y * c, c, c, QColor(col))
            p.setOpacity(1.0)
        for y, row in enumerate(self.ed.pixels()):
            for x, col in enumerate(row):
                if col:
                    p.fillRect(ox + x * c, oy + y * c, c, c, QColor(col))
        if c >= 8:
            p.setPen(QColor(0, 0, 0, 28))
            for x in range(w + 1):
                p.drawLine(ox + x * c, oy, ox + x * c, oy + h * c)
            for y in range(h + 1):
                p.drawLine(ox, oy + y * c, ox + w * c, oy + y * c)
        if self._hover:
            p.setPen(QColor(255, 255, 255, 140))
            p.drawRect(QRect(ox + self._hover[0] * c, oy + self._hover[1] * c, c - 1, c - 1))
        p.end()

    def _apply(self, e):
        px = self.to_pixel(e.position())
        if px is None:
            return
        tool = self.ed.tool
        erase = bool(e.buttons() & Qt.RightButton)
        if tool == "pick":
            col = self.ed.pixels()[px[1]][px[0]]
            if col:
                self.picked.emit(col)
            return
        if tool == "fill":
            self.ed.flood(px[0], px[1], None if erase else self.ed.colour)
            return
        colour = None if erase or tool == "erase" else self.ed.colour
        if self.ed.pixels()[px[1]][px[0]] != colour:
            self.ed.pixels()[px[1]][px[0]] = colour
            self.update()
            self.edited.emit()

    def mousePressEvent(self, e):
        self.ed.push_undo()
        self._stroke = True
        self._apply(e)

    def mouseMoveEvent(self, e):
        px = self.to_pixel(e.position())
        if px != self._hover:
            self._hover = px
            self.update()
        if self._stroke and self.ed.tool not in ("fill", "pick"):
            self._apply(e)

    def mouseReleaseEvent(self, _):
        self._stroke = False

    def leaveEvent(self, _):
        self._hover = None
        self.update()


class Editor(QDialog):
    saved = Signal(dict)

    def __init__(self, parent=None, picture=None, as_copy=False):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Draw - Desktop Park")
        ui_style.install()
        self.tool = "pen"
        self.colour = "#ff77a8"
        self._undo = []
        self.cur = 0
        self.save_error = None
        self._closing = False

        if picture:
            self.w, self.h = artmod.size_of(picture)
            pal = picture["palette"]
            self.frames = [[[pal.get(row[x]) if x < len(row) else None for x in range(self.w)]
                            for row in fr] for fr in picture["frames"]]
            self.art_id = None if as_copy else picture["id"]
            name = picture["name"] + (" (mine)" if as_copy else "")
            kind, behavior = picture.get("kind", "deco"), picture.get("behavior", "stay")
        else:
            self.w = self.h = 16
            self.frames = [blank(16, 16)]
            self.art_id = None
            name, kind, behavior = "", "pet", "walk"

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        self.canvas = Canvas(self)
        self.canvas.edited.connect(self._edited)
        self.canvas.picked.connect(self.set_colour)
        root.addWidget(self.canvas, 1)

        side = QVBoxLayout()
        side.setSpacing(6)
        root.addLayout(side)

        side.addWidget(QLabel("NAME", objectName="section"))
        self.name = QLineEdit(name)
        self.name.setPlaceholderText("e.g. Frog")
        side.addWidget(self.name)

        row = QHBoxLayout()
        self.kind = QComboBox()
        self.kind.addItem("Pet", "pet")
        self.kind.addItem("Decoration", "deco")
        self.kind.setCurrentIndex(0 if kind == "pet" else 1)
        self.behavior = QComboBox()
        for key in artmod.BEHAVIORS:
            self.behavior.addItem(artmod.BEHAVIOR_LABELS[key], key)
        self.behavior.setCurrentIndex(artmod.BEHAVIORS.index(behavior))
        self.kind.currentIndexChanged.connect(self._kind_changed)
        side.addWidget(QLabel("TYPE  /  HOW IT MOVES", objectName="section"))
        row.addWidget(self.kind)
        row.addWidget(self.behavior, 1)
        side.addLayout(row)

        side.addWidget(QLabel("TOOLS", objectName="section"))
        tools = QHBoxLayout()
        self.tool_group = QButtonGroup(self)
        for key, label, tip in (("pen", "Pen", "Paint (right button erases)"),
                                ("erase", "Eraser", "Erase pixels"),
                                ("fill", "Fill", "Fill an area"),
                                ("pick", "Pick", "Pick a colour from the drawing")):
            b = QToolButton(text=label, checkable=True)
            b.setToolTip(tip)
            b.setChecked(key == "pen")
            b.clicked.connect(lambda _=False, k=key: setattr(self, "tool", k))
            self.tool_group.addButton(b)
            tools.addWidget(b)
        side.addLayout(tools)

        side.addWidget(QLabel("COLOURS", objectName="section"))
        pal = QGridLayout()
        pal.setSpacing(3)
        for i, col in enumerate(artmod.EDITOR_COLORS):
            b = QToolButton(objectName="swatch")
            b.setFixedSize(QSize(24, 24))
            b.setStyleSheet("background: %s;" % col)
            b.clicked.connect(lambda _=False, c=col: self.set_colour(c))
            pal.addWidget(b, i // 8, i % 8)
        side.addLayout(pal)
        crow = QHBoxLayout()
        self.current = QLabel()
        self.current.setFixedSize(40, 24)
        more = QPushButton("More colours…")
        more.clicked.connect(self._pick_colour)
        crow.addWidget(QLabel("Now:"))
        crow.addWidget(self.current)
        crow.addWidget(more, 1)
        side.addLayout(crow)
        self.set_colour(self.colour)

        side.addWidget(QLabel("CANVAS", objectName="section"))
        crow = QHBoxLayout()
        self.size_box = QComboBox()
        for s in SIZES:
            self.size_box.addItem("%d x %d" % (s, s), s)
        if self.w == self.h and self.w in SIZES:
            self.size_box.setCurrentIndex(SIZES.index(self.w))
        else:
            self.size_box.addItem("%d x %d" % (self.w, self.h), None)
            self.size_box.setCurrentIndex(self.size_box.count() - 1)
        self.size_box.currentIndexChanged.connect(self._resize)
        crow.addWidget(self.size_box, 1)
        for label, fn, tip in (("Mirror", self._mirror, "Flip left-right"),
                               ("Clear", self._clear, "Clear this frame"),
                               ("Undo", self.undo, "Undo (Ctrl+Z)")):
            b = QPushButton(label)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            crow.addWidget(b)
        side.addLayout(crow)

        side.addWidget(QLabel("ANIMATION FRAMES  (pets move at 10 fps)", objectName="section"))
        self.frame_row = QHBoxLayout()
        self.frame_row.setSpacing(4)
        side.addLayout(self.frame_row)
        frow = QHBoxLayout()
        add = QPushButton("+ Copy frame")
        add.setToolTip("Add a new frame that starts as a copy of this one")
        add.clicked.connect(self._add_frame)
        rem = QPushButton("Delete frame")
        rem.clicked.connect(self._del_frame)
        frow.addWidget(add)
        frow.addWidget(rem)
        side.addLayout(frow)

        prow = QHBoxLayout()
        self.preview = QLabel()
        self.preview.setFixedSize(96, 96)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setObjectName("preview")
        prow.addWidget(self.preview)
        prow.addWidget(QLabel("Preview\n\nDraw it facing RIGHT -\nit turns around by itself."), 1)
        side.addLayout(prow)
        self._pv_frame = 0
        self._pv = QTimer(self)
        self._pv.timeout.connect(self._tick_preview)
        self._pv.start(100)

        side.addStretch(1)
        brow = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save", objectName="save")
        save.clicked.connect(self._save)
        brow.addWidget(cancel)
        brow.addWidget(save, 1)
        side.addLayout(brow)

        self._rebuild_frames()
        self.resize(900, 600)
        self._saved_state = self._state()

    # -- state ---------------------------------------------------------------
    def _state(self):
        return (self.w, self.h, tuple(tuple(tuple(row) for row in frame) for frame in self.frames),
                self.name.text(), self.kind.currentData(), self.behavior.currentData())

    def is_dirty(self):
        return self._state() != self._saved_state

    def _confirm_close(self):
        if self._closing or not self.is_dirty():
            return True
        choice = QMessageBox.question(self, "Desktop Park", "Save changes to this drawing?",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                     QMessageBox.Cancel)
        if choice == QMessageBox.Save:
            return self._save()
        return choice == QMessageBox.Discard

    def reject(self):
        if self._confirm_close() and self.result() != QDialog.Accepted:
            super().reject()

    def closeEvent(self, event):
        if not self._confirm_close():
            event.ignore()
            return
        if self.result() == QDialog.Accepted:
            event.accept()
            return
        self._closing = True
        super().closeEvent(event)
        self._closing = False

    def pixels(self):
        return self.frames[self.cur]

    def onion(self):
        return self.frames[self.cur - 1] if self.cur > 0 else None

    def push_undo(self):
        self._undo.append(([[[c for c in r] for r in f] for f in self.frames], self.cur, self.w, self.h))
        self._undo = self._undo[-60:]

    def undo(self):
        if self._undo:
            self.frames, self.cur, self.w, self.h = self._undo.pop()
            self.cur = min(self.cur, len(self.frames) - 1)
            self._rebuild_frames()
            self.canvas.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Z and e.modifiers() & Qt.ControlModifier:
            self.undo()
        else:
            super().keyPressEvent(e)

    def set_colour(self, col):
        self.colour = col
        self.current.setStyleSheet("background: %s; border: 2px solid %s;" % (col, ui_style.INK))
        if self.tool in ("erase", "pick"):
            self.tool = "pen"
            self.tool_group.buttons()[0].setChecked(True)

    def _pick_colour(self):
        col = QColorDialog.getColor(QColor(self.colour), self, "Pick a colour")
        if col.isValid():
            self.set_colour(col.name())

    def _kind_changed(self):
        if self.kind.currentData() == "deco":
            self.behavior.setCurrentIndex(artmod.BEHAVIORS.index("stay"))
        elif self.behavior.currentData() == "stay":
            self.behavior.setCurrentIndex(artmod.BEHAVIORS.index("walk"))

    def flood(self, x, y, colour):
        grid = self.pixels()
        target = grid[y][x]
        if target == colour:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if 0 <= cx < self.w and 0 <= cy < self.h and grid[cy][cx] == target:
                grid[cy][cx] = colour
                stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
        self._edited()

    def _edited(self):
        self.canvas.update()
        self._refresh_frame_thumbs()

    def _mirror(self):
        self.push_undo()
        self.frames[self.cur] = [list(reversed(r)) for r in self.pixels()]
        self._edited()

    def _clear(self):
        self.push_undo()
        self.frames[self.cur] = blank(self.w, self.h)
        self._edited()

    def _resize(self):
        s = self.size_box.currentData()
        if s is None or (s == self.w and s == self.h):
            return
        self.push_undo()
        # keep the drawing anchored to the bottom-centre (where feet are)
        dx, dy = (s - self.w) // 2, s - self.h
        new = []
        for f in self.frames:
            g = blank(s, s)
            for y, row in enumerate(f):
                for x, col in enumerate(row):
                    nx, ny = x + dx, y + dy
                    if col and 0 <= nx < s and 0 <= ny < s:
                        g[ny][nx] = col
            new.append(g)
        self.frames, self.w, self.h = new, s, s
        self._rebuild_frames()
        self.canvas.update()

    # -- frames --------------------------------------------------------------
    def _frame_pixmap(self, f, box):
        scale = max(1, min(box // self.w, box // self.h))
        pm = QPixmap(self.w * scale, self.h * scale)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        for y, row in enumerate(f):
            for x, col in enumerate(row):
                if col:
                    p.fillRect(x * scale, y * scale, scale, scale, QColor(col))
        p.end()
        return pm

    def _rebuild_frames(self):
        while self.frame_row.count():
            item = self.frame_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._frame_buttons = []
        for i in range(len(self.frames)):
            b = QToolButton(checkable=True)
            b.setFixedSize(44, 44)
            b.setIconSize(QSize(36, 36))
            b.setChecked(i == self.cur)
            b.setToolTip("Frame %d" % (i + 1))
            b.clicked.connect(lambda _=False, i=i: self._select(i))
            self.frame_row.addWidget(b)
            self._frame_buttons.append(b)
        self.frame_row.addStretch(1)
        self._refresh_frame_thumbs()

    def _refresh_frame_thumbs(self):
        for i, b in enumerate(self._frame_buttons):
            b.setIcon(QIcon(self._frame_pixmap(self.frames[i], 36)))

    def _select(self, i):
        self.cur = i
        for j, b in enumerate(self._frame_buttons):
            b.setChecked(j == i)
        self.canvas.update()

    def _add_frame(self):
        if len(self.frames) >= MAX_FRAMES:
            return
        self.push_undo()
        self.frames.insert(self.cur + 1, [r[:] for r in self.pixels()])
        self.cur += 1
        self._rebuild_frames()
        self.canvas.update()

    def _del_frame(self):
        if len(self.frames) <= 1:
            return
        self.push_undo()
        del self.frames[self.cur]
        self.cur = min(self.cur, len(self.frames) - 1)
        self._rebuild_frames()
        self.canvas.update()

    def _tick_preview(self):
        self._pv_frame = (self._pv_frame + 1) % len(self.frames)
        self.preview.setPixmap(self._frame_pixmap(self.frames[self._pv_frame], 88))

    # -- saving --------------------------------------------------------------
    def to_picture(self):
        """Turn the colour grid into the compact saved format."""
        palette, lookup = {}, {}
        frames = []
        for f in self.frames:
            rows = []
            for row in f:
                chars = []
                for col in row:
                    if not col:
                        chars.append(".")
                        continue
                    if col not in lookup:
                        if len(lookup) >= len(artmod.PIXEL_CHARS):
                            col = min(lookup, key=lambda c: _dist(c, col))
                        else:
                            ch = artmod.PIXEL_CHARS[len(lookup)]
                            lookup[col] = ch
                            palette[ch] = col
                    chars.append(lookup[col])
                rows.append("".join(chars))
            frames.append(rows)
        return {
            "id": self.art_id or "my-%d" % int(time.time() * 1000),
            "name": self.name.text().strip() or "My drawing",
            "kind": self.kind.currentData(),
            "behavior": self.behavior.currentData(),
            "palette": palette,
            "frames": frames,
        }

    def _save(self):
        if not any(c for f in self.frames for r in f for c in r):
            QMessageBox.information(self, "Desktop Park", "Draw something first!")
            return False
        self.save_error = None
        self.saved.emit(self.to_picture())
        if self.save_error:
            QMessageBox.warning(self, "Desktop Park", "The drawing could not be saved.\n" + self.save_error)
            return False
        self._saved_state = self._state()
        self.accept()
        return True


def _dist(a, b):
    ca, cb = QColor(a), QColor(b)
    return (ca.red() - cb.red()) ** 2 + (ca.green() - cb.green()) ** 2 + (ca.blue() - cb.blue()) ** 2
