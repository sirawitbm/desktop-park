"""The picture library: built-in art plus the user's drawings, turned into
images the windows can paint."""

from collections import OrderedDict

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap, QTransform

import art as artmod
import daycycle


def frame_image(picture, frame_rows):
    w, h = artmod.size_of(picture)
    img = QImage(max(1, w), max(1, h), QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    pal = picture["palette"]
    for y, row in enumerate(frame_rows):
        for x, ch in enumerate(row):
            colour = pal.get(ch)
            if colour:
                img.setPixelColor(x, y, QColor(colour))
    return img


class Library:
    def __init__(self, custom_art):
        self.builtin = artmod.builtin_by_id()
        self.custom = {a["id"]: a for a in custom_art}
        self._images = {}       # art id -> [QImage per frame]
        self._pixmaps = OrderedDict()
        self._pixmap_bytes = 0
        self.cache_bytes = 48 * 1024 * 1024
        self.cache_entries = 2000
        self._paint_gen = 0              # bumped once per paint (begin_paint)
        self._used = {}                  # cache key -> paint it was last used in

    def begin_paint(self):
        """Called at the start of each paint. Pictures used in the current
        paint are never evicted, so a scene bigger than the budget goes a bit
        over it instead of rebuilding its pictures every frame (thrashing)."""
        self._paint_gen += 1

    # -- lookups -------------------------------------------------------------
    def get(self, art_id):
        return self.custom.get(art_id) or self.builtin.get(art_id)

    def all(self):
        return list(self.builtin.values()) + list(self.custom.values())

    def custom_list(self):
        return list(self.custom.values())

    def set_custom(self, picture):
        self.custom[picture["id"]] = picture
        self.forget(picture["id"])

    def set_clock(self, text, body):
        """The clock decoration shows a new time (called when the minute changes)."""
        picture = self.builtin.get("clock")
        if picture is not None:
            picture["frames"] = [artmod.clock_rows(text, body)]
            self.forget("clock")

    def remove_custom(self, art_id):
        self.custom.pop(art_id, None)
        self.forget(art_id)

    def forget(self, art_id):
        self._images.pop(art_id, None)
        for key in [k for k in self._pixmaps if k[0] == art_id]:
            self._pixmap_bytes -= self._cost(self._pixmaps.pop(key))
            self._used.pop(key, None)

    # -- images --------------------------------------------------------------
    def images(self, art_id):
        if art_id not in self._images:
            picture = self.get(art_id)
            frames = (picture["frames"] + list(picture.get("poses", {}).values())) if picture else []
            self._images[art_id] = [frame_image(picture, frame) for frame in frames]
        return self._images[art_id]

    def frame_count(self, art_id):
        picture = self.get(art_id)
        return max(1, len(picture["frames"])) if picture else 1

    def pose_frame(self, art_id, pose):
        picture = self.get(art_id)
        poses = list(picture.get("poses", {})) if picture else []
        return len(picture["frames"]) + poses.index(pose) if pose in poses else None

    def pixmap(self, art_id, frame, scale, flip, shade=(0.0, 0.0)):
        """The picture at this size and facing. shade = (night, light) gives it
        the time-of-day tint (rounded with daycycle.bucket)."""
        if shade[0] > 0:
            key = (art_id, frame, scale, flip, shade)
            pm = self._cached(key)
            if pm is None:
                # at night only the tinted copy is drawn: don't keep the plain one too
                base = self._cached((art_id, frame, scale, flip)) or self._plain(art_id, frame, scale, flip)
                if base is None:
                    return None
                r, g, b, a = daycycle.tint(*shade)
                pm = QPixmap(base)
                p = QPainter(pm)
                p.setCompositionMode(QPainter.CompositionMode_SourceAtop)   # only on the picture
                p.fillRect(pm.rect(), QColor(r, g, b, int(a * 255)))
                p.end()
                self._store(key, pm)
            return pm
        key = (art_id, frame, scale, flip)
        pm = self._cached(key)
        if pm is None:
            pm = self._plain(art_id, frame, scale, flip)
            if pm is not None:
                self._store(key, pm)
        return pm

    def _plain(self, art_id, frame, scale, flip):
        imgs = self.images(art_id)
        if not imgs:
            return None
        img = imgs[frame % len(imgs)]
        if flip:
            img = img.transformed(QTransform().scale(-1, 1))
        img = img.scaled(img.width() * scale, img.height() * scale,
                         Qt.IgnoreAspectRatio, Qt.FastTransformation)
        return QPixmap.fromImage(img)

    @staticmethod
    def _cost(pm):
        return pm.width() * pm.height() * max(1, pm.depth() // 8)

    def _cached(self, key):
        pm = self._pixmaps.get(key)
        if pm is not None:
            self._pixmaps.move_to_end(key)
            self._used[key] = self._paint_gen
        return pm

    def _store(self, key, pm):
        previous = self._pixmaps.pop(key, None)
        if previous is not None:
            self._pixmap_bytes -= self._cost(previous)
        cost = self._cost(pm)
        if cost > self.cache_bytes:
            return
        while self._pixmaps and (len(self._pixmaps) >= self.cache_entries
                                 or self._pixmap_bytes + cost > self.cache_bytes):
            oldest = next(iter(self._pixmaps))
            if self._used.get(oldest) == self._paint_gen:
                break                  # everything left is on screen right now: go over a little
            old = self._pixmaps.pop(oldest)
            self._used.pop(oldest, None)
            self._pixmap_bytes -= self._cost(old)
        self._pixmaps[key] = pm
        self._used[key] = self._paint_gen
        self._pixmap_bytes += cost

    def opaque(self, art_id, frame, ax, ay):
        imgs = self.images(art_id)
        if not imgs:
            return False
        img = imgs[frame % len(imgs)]
        if 0 <= ax < img.width() and 0 <= ay < img.height():
            return img.pixelColor(ax, ay).alpha() > 0
        return False

    def thumbnail(self, art_id, box=40, max_scale=None, bottom=False):
        """The first frame, as big as fits in a box x box square (whole pixels
        only). max_scale keeps small pictures from being blown up, so a snail
        stays snail-sized next to a tree; bottom lines it up on the box's floor."""
        imgs = self.images(art_id)
        if not imgs:
            return QPixmap()
        img = imgs[0]
        scale = max(1, min(box // max(1, img.width()), box // max(1, img.height())))
        if max_scale:
            scale = min(scale, max_scale)
        img = img.scaled(img.width() * scale, img.height() * scale,
                         Qt.IgnoreAspectRatio, Qt.FastTransformation)
        if not bottom:
            return QPixmap.fromImage(img)
        canvas = QImage(box, box, QImage.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.transparent)
        p = QPainter(canvas)
        p.drawImage((box - img.width()) // 2, box - img.height() - 2, img)
        p.end()
        return QPixmap.fromImage(canvas)


def app_icon_pixmap(scale=1):
    """The park-tile app icon (art.APP_ICON), scaled by whole pixels."""
    from art_pack import PAL
    rows = artmod.APP_ICON
    img = frame_image({"palette": PAL, "frames": [rows]}, rows)
    return QPixmap.fromImage(img.scaled(16 * scale, 16 * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation))


def app_icon():
    """The app icon at the sizes Windows asks for, each pixel-crisp."""
    icon = QIcon()
    for scale in (1, 2, 3, 4, 8, 16):
        icon.addPixmap(app_icon_pixmap(scale))
    return icon
