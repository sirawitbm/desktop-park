"""The park: a see-through window over the whole screen where things live.

Only painted pixels catch the mouse. Everywhere else, clicks fall through to
whatever is underneath (Windows does this for see-through windows), so the
park never gets in the way of your work.
"""

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QMenu, QWidget

import art as artmod
import winutil
from sprites import frame_image
from sim import MAX_SCALE, MIN_SCALE, Thing, World, thing_at

TICK_MS = 33          # movement updates ~30 times a second; frames flip at 10fps
DRAG_START_PX = 4


class ParkWindow(QWidget):
    changed = Signal()            # something the user did needs saving
    edit_art = Signal(str)        # "Edit picture" chosen for this art id

    def __init__(self, library):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
                         | Qt.WindowDoesNotAcceptFocus | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowTitle("Desktop Park")
        self.setMouseTracking(True)
        self.library = library
        self.world = World(1, 1)
        self.locked = False
        self._drawn = {}          # uid -> QRect painted last time
        self._press = None        # (thing, press pos, offset)
        self._dragged = False
        self._next_uid = 1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(TICK_MS)
        self._particle_pm = {}

    # -- setup ---------------------------------------------------------------
    def fit_screen(self, screen):
        area = screen.availableGeometry()   # stop above the taskbar
        self.setGeometry(area)
        self.world.resize(area.width(), area.height())
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        winutil.no_activate(hwnd)
        winutil.click_through(hwnd, self.locked)

    def set_locked(self, locked):
        self.locked = locked
        winutil.click_through(int(self.winId()), locked)
        self.setCursor(Qt.ArrowCursor)

    # -- things --------------------------------------------------------------
    def new_uid(self):
        uid = "t%d" % self._next_uid
        self._next_uid += 1
        while any(t.uid == uid for t in self.world.things):
            uid = "t%d" % self._next_uid
            self._next_uid += 1
        return uid

    def make_thing(self, art_id, **kw):
        picture = self.library.get(art_id)
        if picture is None:
            return None
        w, h = artmod.size_of(picture)
        kw.setdefault("behavior", picture.get("behavior", "stay"))
        kw.setdefault("speed_mult", picture.get("speed", 1.0))
        return Thing(kw.pop("uid", None) or self.new_uid(), art_id, w, h, **kw)

    def add_art(self, art_id, scale=4):
        t = self.make_thing(art_id, scale=scale)
        if t is None:
            return None
        t.x, t.y = self.world.drop_spot(t)
        self.world.things.append(t)
        self.world.spawn("sparkle", t.x + t.w / 2, t.y, life=0.8)
        self.update()
        self.changed.emit()
        return t

    def load_things(self, objects):
        self.world.things = []
        for o in objects:
            t = self.make_thing(o["art"], uid=o["uid"], x=o["x"], y=o["y"],
                                scale=o["scale"], behavior=o["behavior"], flip=o["flip"])
            if t:
                self.world.clamp(t)
                self.world.things.append(t)
        self.update()

    def refresh_art(self, art_id):
        """A drawing was edited: resize everything that uses it."""
        picture = self.library.get(art_id)
        if picture is None:
            return
        w, h = artmod.size_of(picture)
        for t in self.world.things:
            if t.art_id == art_id:
                t.art_w, t.art_h = w, h
                self.world.clamp(t)
        self.update()

    def remove_art(self, art_id):
        self.world.things = [t for t in self.world.things if t.art_id != art_id]
        self.update()

    def clear(self):
        self.world.things = []
        self.world.particles = []
        self.update()
        self.changed.emit()

    def snapshot(self):
        return [t.to_dict() for t in self.world.things]

    # -- drawing -------------------------------------------------------------
    def _frame(self, t):
        picture = self.library.get(t.art_id)
        is_pet = bool(picture and picture.get("kind") == "pet")
        return t.frame_index(self.library.frame_count(t.art_id), is_pet)

    def _rect(self, t):
        x, y, w, h = t.rect()
        return QRect(int(x), int(y), int(w), int(h))

    def _particle(self, kind):
        """Pixmap for a reaction picture, drawn 3x size."""
        pm = self._particle_pm.get(kind)
        if pm is None:
            palette, rows = artmod.PARTICLES[kind]
            img = frame_image({"palette": palette, "frames": [rows]}, rows)
            pm = QPixmap.fromImage(img.scaled(img.width() * 3, img.height() * 3))
            self._particle_pm[kind] = pm
        return pm

    def _particle_rect(self, p):
        pm = self._particle(p[0])
        return QRect(int(p[1] - pm.width() / 2), int(p[2] - pm.height()), pm.width(), pm.height())

    def _tick(self):
        if not self.isVisible():
            return
        before = {t.uid: self._rect(t) for t in self.world.things}
        frames = {t.uid: self._frame(t) for t in self.world.things}
        parts_before = [self._particle_rect(q) for q in self.world.particles]
        self.world.step(TICK_MS / 1000.0)
        dirty = QRegion()
        for r in parts_before:
            dirty += r
        for q in self.world.particles:
            dirty += self._particle_rect(q)
        for t in self.world.things:
            now = self._rect(t)
            if now != before.get(t.uid) or self._frame(t) != frames.get(t.uid):
                dirty += now.adjusted(-1, -1, 1, 1)
                old = before.get(t.uid)
                if old is not None:
                    dirty += old.adjusted(-1, -1, 1, 1)
        if not dirty.isEmpty():
            self.update(dirty)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(event.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        clip = event.rect()
        for t in self.world.things:
            r = self._rect(t)
            if not r.intersects(clip):
                continue
            pm = self.library.pixmap(t.art_id, self._frame(t), t.scale, t.flip)
            if pm is not None:
                p.drawPixmap(r.topLeft(), pm)
        for q in self.world.particles:
            p.setOpacity(min(1.0, q[3] / 0.4))
            p.drawPixmap(self._particle_rect(q).topLeft(), self._particle(q[0]))
        p.setOpacity(1.0)
        p.end()

    def is_pet(self, t):
        picture = self.library.get(t.art_id)
        return bool(picture and picture.get("kind") == "pet")

    # -- mouse ---------------------------------------------------------------
    def thing_under(self, pos):
        def opaque(t, ax, ay):
            return self.library.opaque(t.art_id, self._frame(t), ax, ay)
        return thing_at(self.world.things, pos.x(), pos.y(), opaque)

    def mousePressEvent(self, e):
        if self.locked:
            return
        t = self.thing_under(e.position().toPoint())
        if t is None:
            return
        if e.button() == Qt.LeftButton:
            pos = e.position().toPoint()
            self._press = (t, pos, QPoint(int(pos.x() - t.x), int(pos.y() - t.y)))
            self._dragged = False
        elif e.button() == Qt.RightButton:
            self.show_menu(t, e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        if self._press:
            t, start, offset = self._press
            if not self._dragged and (pos - start).manhattanLength() >= DRAG_START_PX:
                self._dragged = True
                t.dragging = True
                # bring to front while carrying it
                self.world.things.remove(t)
                self.world.things.append(t)
                self.setCursor(Qt.ClosedHandCursor)
            if self._dragged:
                old = self._rect(t)
                t.x, t.y = pos.x() - offset.x(), pos.y() - offset.y()
                self.world.clamp(t)
                self.update(QRegion(old.adjusted(-1, -1, 1, 1)) + self._rect(t).adjusted(-1, -1, 1, 1))
            return
        self.setCursor(Qt.OpenHandCursor if self.thing_under(pos) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if not self._press or e.button() != Qt.LeftButton:
            return
        t = self._press[0]
        self._press = None
        if self._dragged:
            self.world.released(t)
            self.setCursor(Qt.OpenHandCursor)
            self.changed.emit()
        elif self.is_pet(t):
            self.world.poke(t)               # decorations just sit there
        self._dragged = False

    def wheelEvent(self, e):
        if self.locked:
            return
        t = self.thing_under(e.position().toPoint())
        if t is None:
            return
        step = 1 if e.angleDelta().y() > 0 else -1
        self.set_scale(t, t.scale + step)

    def set_scale(self, t, scale):
        scale = max(MIN_SCALE, min(MAX_SCALE, scale))
        if scale == t.scale:
            return
        old = self._rect(t)
        bottom, cx = t.y + t.h, t.x + t.w / 2
        t.scale = scale
        t.x, t.y = cx - t.w / 2, bottom - t.h      # grow from the feet
        self.world.clamp(t)
        self.update(QRegion(old) + self._rect(t))
        self.changed.emit()

    # -- right-click menu -----------------------------------------------------
    def show_menu(self, t, global_pos):
        picture = self.library.get(t.art_id) or {}
        menu = QMenu(self)
        title = menu.addAction(picture.get("name", "Thing"))
        title.setEnabled(False)
        menu.addSeparator()

        moves = menu.addMenu("How it moves")
        group = QActionGroup(moves)
        for key in artmod.BEHAVIORS:
            a = moves.addAction(artmod.BEHAVIOR_LABELS[key])
            a.setCheckable(True)
            a.setChecked(t.behavior == key)
            group.addAction(a)
            a.triggered.connect(lambda _=False, k=key: self._set_behavior(t, k))

        sizes = menu.addMenu("Size")
        sgroup = QActionGroup(sizes)
        for s in range(MIN_SCALE, MAX_SCALE + 1):
            a = sizes.addAction("%dx" % s)
            a.setCheckable(True)
            a.setChecked(t.scale == s)
            sgroup.addAction(a)
            a.triggered.connect(lambda _=False, s=s: self.set_scale(t, s))

        menu.addAction("Turn around", lambda: self._flip(t))
        menu.addAction("Bring to front", lambda: self._order(t, front=True))
        menu.addAction("Send to back", lambda: self._order(t, front=False))
        menu.addSeparator()
        menu.addAction("Make a copy", lambda: self._duplicate(t))
        edit_label = "Edit drawing" if t.art_id in self.library.custom else "Draw my own version"
        menu.addAction(edit_label, lambda: self.edit_art.emit(t.art_id))
        menu.addSeparator()
        menu.addAction("Remove", lambda: self._remove(t))
        menu.exec(global_pos)

    def _set_behavior(self, t, key):
        t.behavior = key
        t.state, t.timer, t.target = "idle", 0.3, None
        t.vx = t.vy = 0.0
        self.changed.emit()

    def _flip(self, t):
        t.flip = not t.flip
        self.update(self._rect(t))
        self.changed.emit()

    def _order(self, t, front):
        self.world.things.remove(t)
        if front:
            self.world.things.append(t)
        else:
            self.world.things.insert(0, t)
        self.update(self._rect(t))
        self.changed.emit()

    def _duplicate(self, t):
        c = self.make_thing(t.art_id, x=min(t.x + 20, self.world.width - t.w), y=t.y,
                            scale=t.scale, behavior=t.behavior, flip=t.flip)
        self.world.things.append(c)
        self.update(self._rect(c))
        self.changed.emit()

    def _remove(self, t):
        if t in self.world.things:
            self.world.things.remove(t)
        self.update(self._rect(t))
        self.changed.emit()
