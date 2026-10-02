"""The picture library: built-in art plus the user's drawings, turned into
images the windows can paint."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform

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
        self._pixmaps = {}      # (art id, frame, scale, flip) -> QPixmap

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
            del self._pixmaps[key]

    # -- images --------------------------------------------------------------
    def images(self, art_id):
        if art_id not in self._images:
            picture = self.get(art_id)
            self._images[art_id] = [frame_image(picture, f) for f in picture["frames"]] if picture else []
        return self._images[art_id]

    def frame_count(self, art_id):
        return max(1, len(self.images(art_id)))

    def pixmap(self, art_id, frame, scale, flip, shade=(0.0, 0.0)):
        """The picture at this size and facing. shade = (night, light) gives it
        the time-of-day tint (rounded with daycycle.bucket)."""
        if shade[0] > 0:
            key = (art_id, frame, scale, flip, shade)
            pm = self._pixmaps.get(key)
            if pm is None:
                base = self.pixmap(art_id, frame, scale, flip)
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
        pm = self._pixmaps.get(key)
        if pm is None:
            imgs = self.images(art_id)
            if not imgs:
                return None
            img = imgs[frame % len(imgs)]
            if flip:
                img = img.transformed(QTransform().scale(-1, 1))
            img = img.scaled(img.width() * scale, img.height() * scale,
                             Qt.IgnoreAspectRatio, Qt.FastTransformation)
            pm = QPixmap.fromImage(img)
            self._store(key, pm)
        return pm

    def _store(self, key, pm):
        if len(self._pixmaps) > 2000:
            self._pixmaps.clear()
        self._pixmaps[key] = pm

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
