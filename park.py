"""The park: a see-through window over the whole screen where things live.

Only painted pixels catch the mouse. Everywhere else, clicks fall through to
whatever is underneath (Windows does this for see-through windows), so the
park never gets in the way of your work.
"""

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QColor, QImage, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QMenu, QWidget

import art as artmod
import daycycle
import winutil
from sprites import frame_image
from sim import MAX_SCALE, MIN_SCALE, Thing, World, thing_at

SHADOW = QColor(26, 28, 44, 95)     # the soft strip under things on the ground
TICK_MS = 33          # movement updates ~30 times a second; frames flip at 10fps
DRAG_START_PX = 4


class ParkWindow(QWidget):
    changed = Signal()            # something the user did needs saving
    edit_art = Signal(str)        # "Edit picture" chosen for this art id
    undo_changed = Signal(bool)
    scene_restored = Signal(object)

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
        self._undo = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(TICK_MS)
        self._particle_pm = {}
        self._shade_key = None          # time-of-day tint last painted
        self._clock_stamp = None        # what the clock decorations last showed

    # -- setup ---------------------------------------------------------------
    def fit_screen(self, screen):
        area = screen.availableGeometry()   # stop above the taskbar
        self.setGeometry(area)
        self.world.relocate(area.width(), area.height())
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

    def set_low_power(self, on):
        self.timer.setInterval(67 if on else TICK_MS)

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
        kw.setdefault("is_pet", picture.get("kind") == "pet")
        return Thing(kw.pop("uid", None) or self.new_uid(), art_id, w, h, **kw)

    def glows(self):
        """Where the lights are, for the night glow: (x, y, radius, colour, flickers)."""
        out = []
        for t in self.world.things:
            picture = self.library.get(t.art_id)
            glow = picture.get("glow") if picture else None
            if not glow:
                continue
            colour, radius, (fx, fy), flickers = glow
            x, y, w, h = t.rect()
            if t.flip:
                fx = 1 - fx
            out.append((x + fx * w, y + fy * h, radius * t.scale, colour, flickers))
        return out

    def add_art(self, art_id, scale=4):
        t = self.make_thing(art_id, scale=scale)
        if t is None:
            return None
        self.checkpoint()
        t.x, t.y = self.world.drop_spot(t)
        self.world.things.append(t)
        self.world.spawn("sparkle", t.x + t.w / 2, t.y, life=0.8)
        self.update()
        self.changed.emit()
        return t

    def load_things(self, objects, clear_history=True):
        if clear_history:
            self._undo.clear()
            self.undo_changed.emit(False)
        self._press = None
        self._dragged = False
        self.world.particles = []
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
                t.is_pet = picture.get("kind") == "pet"
                self.world.clamp(t)
        self.update()

    def remove_art(self, art_id):
        self.world.things = [t for t in self.world.things if t.art_id != art_id]
        self.update()

    def clear(self):
        self.checkpoint()
        self.world.things = []
        self.world.particles = []
        self.update()
        self.changed.emit()

    def snapshot(self):
        return [t.to_dict() for t in self.world.things]

    def checkpoint(self, settings=None):
        self._undo.append((self.snapshot(), self.world.width, self.world.height, settings))
        self._undo = self._undo[-40:]
        self.undo_changed.emit(True)

    def undo(self):
        if not self._undo:
            return
        objects, width, height, settings = self._undo.pop()
        self.restore_scene(objects, width, height)
        if settings is not None:
            self.scene_restored.emit(settings)
        self.undo_changed.emit(bool(self._undo))
        self.changed.emit()

    def restore_scene(self, objects, width, height):
        target_width, target_height = self.world.width, self.world.height
        self.world.width, self.world.height = width, height
        self.load_things(objects, clear_history=False)
        self.world.relocate(target_width, target_height)
        self.update()

    # -- drawing -------------------------------------------------------------
    def _frame(self, t):
        picture = self.library.get(t.art_id)
        is_pet = bool(picture and picture.get("kind") == "pet")
        pose = self.library.pose_frame(t.art_id, t.pose())
        if pose is not None:
            return pose
        return t.frame_index(self.library.frame_count(t.art_id), is_pet)

    def _rect(self, t):
        x, y, w, h = t.rect()
        return QRect(int(x), int(y), int(w), int(h))

    def _visual_rect(self, t):
        rect = self._rect(t)
        shadow = self._shadow_rect(t)
        if shadow is not None:
            rect = rect.united(shadow)
        return rect.adjusted(-1, -1, 1, 1)

    def _particle(self, kind):
        """Pixmap for a reaction picture, drawn 3x size."""
        pm = self._particle_pm.get(kind)
        if pm is None:
            palette, rows = artmod.PARTICLES[kind]
            img = _outlined(frame_image({"palette": palette, "frames": [rows]}, rows))
            pm = QPixmap.fromImage(img.scaled(img.width() * 3, img.height() * 3))
            self._particle_pm[kind] = pm
        return pm

    def _shadow_rect(self, t):
        """A soft strip on the ground under things that stand or walk there,
        so they sit on the taskbar instead of floating. Jumping pets keep
        their shadow on the ground; it shrinks the higher they go."""
        if t.behavior in ("swim", "fly") or t.dragging:
            return None
        ground = self.world.ground
        above = ground - (t.y + t.h)
        if t.behavior == "stay" and above > 1:
            return None                               # a decoration placed in mid-air
        k = max(0.35, 1.0 - max(0.0, above) / 220.0)
        width = (t.w + 2 * t.scale) * k
        return QRect(int(t.x + t.w / 2 - width / 2), int(ground - t.scale), int(width), int(t.scale))

    def _particle_rect(self, p):
        pm = self._particle(p[0])
        return QRect(int(p[1] - pm.width() / 2), int(p[2] - pm.height()), pm.width(), pm.height())

    def _tick(self):
        if not self.isVisible():
            return
        before = {t.uid: self._rect(t) for t in self.world.things}
        shadows_before = {t.uid: self._shadow_rect(t) for t in self.world.things}
        frames = {t.uid: self._frame(t) for t in self.world.things}
        parts_before = [self._particle_rect(q) for q in self.world.particles]
        self.world.step(self.timer.interval() / 1000.0)
        # the tint changed (dusk, dawn, a lamp added or moved): repaint everything
        key = (daycycle.bucket(self.world.night, 0)[0],
             tuple(self.world.lights))
        if key != self._shade_key:
            self._shade_key = key
            self.update()
        # clock decorations show the real time
        stamp = (daycycle.clock_text(), "moon" if self.world.night >= 0.5 else "sun")
        if stamp != self._clock_stamp:
            self._clock_stamp = stamp
            self.library.set_clock(*stamp)
            for t in self.world.things:
                if t.art_id == "clock":
                    self.update(self._rect(t))
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
                for s in (shadows_before.get(t.uid), self._shadow_rect(t)):
                    if s is not None:
                        dirty += s.adjusted(-1, -1, 1, 1)
        if not dirty.isEmpty():
            self.update(dirty)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode_Source)
        p.fillRect(event.rect(), Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        clip = event.rect()
        for t in self.world.things:
            s = self._shadow_rect(t)
            if s is not None and s.intersects(clip):
                p.fillRect(s, SHADOW)
        for t in self.world.things:
            r = self._rect(t)
            if not r.intersects(clip):
                continue
            shade = (0.0, 0.0)
            if self.world.night > 0.02:
                light = self.world.light_at(r.center().x(), r.center().y())
                shade = daycycle.bucket(self.world.night, light)
            pm = self.library.pixmap(t.art_id, self._frame(t), t.scale, t.flip, shade)
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
        hit = thing_at(self.world.things, pos.x(), pos.y(), opaque)
        if hit is None:
            # the shadow strip is drawn in this window, so it catches the click:
            # treat it as part of the thing rather than swallowing the click
            for t in reversed(self.world.things):
                s = self._shadow_rect(t)
                if s is not None and s.contains(pos):
                    return t
        return hit

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
                self.checkpoint()
                self.update(self._visual_rect(t))
                self._dragged = True
                t.dragging = True
                # bring to front while carrying it
                self.world.things.remove(t)
                self.world.things.append(t)
                self.setCursor(Qt.ClosedHandCursor)
            if self._dragged:
                old = self._visual_rect(t)
                t.x, t.y = pos.x() - offset.x(), pos.y() - offset.y()
                self.world.clamp(t)
                self.update(QRegion(old) + self._visual_rect(t))
            return
        self.setCursor(Qt.OpenHandCursor if self.thing_under(pos) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if not self._press or e.button() != Qt.LeftButton:
            return
        t = self._press[0]
        self._press = None
        if self._dragged:
            self.world.released(t)
            self.update(self._visual_rect(t))
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
        self.checkpoint()
        old = self._visual_rect(t)
        bottom, cx = t.y + t.h, t.x + t.w / 2
        t.scale = scale
        t.x, t.y = cx - t.w / 2, bottom - t.h      # grow from the feet
        self.world.clamp(t)
        self.update(QRegion(old) + self._visual_rect(t))
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
        menu.addSeparator()
        undo = menu.addAction("Undo last park edit", self.undo)
        undo.setEnabled(bool(self._undo))
        menu.exec(global_pos)

    def _set_behavior(self, t, key):
        if key == t.behavior:
            return
        self.checkpoint()
        old = self._visual_rect(t)
        t.behavior = key
        t.state, t.timer, t.target = "idle", 0.3, None
        t.vx = t.vy = 0.0
        self.update(QRegion(old) + self._visual_rect(t))
        self.changed.emit()

    def _flip(self, t):
        self.checkpoint()
        old = self._visual_rect(t)
        t.flip = not t.flip
        self.update(QRegion(old) + self._visual_rect(t))
        self.changed.emit()

    def _order(self, t, front):
        self.checkpoint()
        self.world.things.remove(t)
        if front:
            self.world.things.append(t)
        else:
            self.world.things.insert(0, t)
        self.update(self._visual_rect(t))
        self.changed.emit()

    def _duplicate(self, t):
        self.checkpoint()
        c = self.make_thing(t.art_id, x=min(t.x + 20, self.world.width - t.w), y=t.y,
                            scale=t.scale, behavior=t.behavior, flip=t.flip)
        self.world.things.append(c)
        self.update(self._visual_rect(c))
        self.changed.emit()

    def _remove(self, t):
        if t in self.world.things:
            self.checkpoint()
            old = self._visual_rect(t)
            self.world.things.remove(t)
            self.update(old)
            self.changed.emit()


def _outlined(img, colour=QColor(26, 28, 44)):
    """The picture with a one-pixel dark outline around it, so the little
    reaction pictures read on white windows as well as dark wallpapers."""
    out = QImage(img.width() + 2, img.height() + 2, QImage.Format_ARGB32_Premultiplied)
    out.fill(Qt.transparent)
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixelColor(x, y).alpha() == 0:
                continue
            for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
                if out.pixelColor(x + dx, y + dy).alpha() == 0:
                    out.setPixelColor(x + dx, y + dy, colour)
    p = QPainter(out)
    p.drawImage(1, 1, img)
    p.end()
    return out
