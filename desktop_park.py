"""Desktop Park - little pixel pets and plants that live on top of your screen.

Run:  pythonw desktop_park.py
"""

import random
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

import store
import winutil
from board import STYLE as BOARD_STYLE, Board
from editor import Editor
from park import ParkWindow
from sprites import Library

__version__ = "0.1.0"

# What a brand-new park starts with: (art, x as a fraction of the screen, size)
STARTER_SCENE = [
    ("pine", 0.70, 4), ("tree", 0.78, 5), ("bush", 0.86, 3), ("rock", 0.92, 3),
    ("grass", 0.74, 3), ("flower", 0.83, 4), ("mushroom", 0.95, 3),
    ("cat", 0.80, 3), ("slime", 0.88, 3), ("fish", 0.75, 3),
]


class App:
    def __init__(self, qapp):
        self.qapp = qapp
        qapp.setQuitOnLastWindowClosed(False)   # closing the editor must not quit
        self.quitting = False
        self.data = store.load()
        self.library = Library(self.data["custom_art"])
        self.editor = None
        self._save_timer = QTimer(singleShot=True, interval=1500)
        self._save_timer.timeout.connect(self.save)

        screen = qapp.primaryScreen()
        self.park = ParkWindow(self.library)
        self.park.fit_screen(screen)
        self.park.load_things(self.data["objects"])
        self.park.changed.connect(self.save_soon)
        self.park.edit_art.connect(self.open_editor)
        if not self.data["seeded"]:
            self._seed()

        self.board = Board(self.library)
        self.board.add_art.connect(self.add_art)
        self.board.draw_new.connect(lambda: self.open_editor(None))
        self.board.edit_art.connect(self.open_editor)
        self.board.delete_art.connect(self.delete_art)
        self.board.lock_toggled.connect(self.set_locked)
        self.board.hide_toggled.connect(self.set_hidden)
        self.board.clear_park.connect(self.clear_park)
        self.board.moved.connect(self.save_soon)
        self.board.closed.connect(self._board_closed)
        area = screen.availableGeometry()
        b = self.data["board"]
        self.board.set_collapsed(b.get("collapsed", False))
        self.board.place(b.get("x", area.right() - self.board.width() - 24),
                         b.get("y", area.top() + 80), area)

        self._make_tray()
        self.set_locked(self.data["locked"])
        self.set_hidden(self.data["hidden"])
        self.board.show()
        screen.availableGeometryChanged.connect(lambda r: self.park.fit_screen(screen))

        self._autosave = QTimer(interval=30000)       # pets wander; remember where
        self._autosave.timeout.connect(self.save)
        self._autosave.start()
        self._pin = QTimer(interval=2000)
        self._pin.timeout.connect(self.pin)
        self._pin.start()
        qapp.aboutToQuit.connect(self.save)

    # -- park actions ----------------------------------------------------------
    def _seed(self):
        w = self.park.world.width
        for art_id, fx, scale in STARTER_SCENE:
            t = self.park.make_thing(art_id, scale=scale)
            if t is None:
                continue
            t.x = fx * w - t.w / 2
            t.y = self.park.world.ground - t.h
            if t.behavior == "swim":
                t.y = self.park.world.height * 0.55
            self.park.world.clamp(t)
            self.park.world.things.append(t)
        self.data["seeded"] = True
        self.save_soon()

    def add_art(self, art_id):
        if self.data["hidden"]:
            self.set_hidden(False)
        self.park.add_art(art_id, scale=random.choice((3, 4)))

    def clear_park(self):
        if not self.park.world.things:
            return
        box = QMessageBox(QMessageBox.Question, "Desktop Park",
                          "Remove everything from the park?\n(Your drawings are kept.)",
                          QMessageBox.Yes | QMessageBox.No, self.board)
        box.setStyleSheet(BOARD_STYLE + "QMessageBox{background:#1d2230;} QLabel{color:#e6ebf7;}")
        if box.exec() == QMessageBox.Yes:
            self.park.clear()

    def set_locked(self, on):
        self.data["locked"] = on
        self.park.set_locked(on)
        self.board.set_locked(on)
        self.lock_action.setChecked(on)
        self.save_soon()

    def set_hidden(self, on):
        self.data["hidden"] = on
        self.park.setVisible(not on)
        self.board.set_hidden(on)
        self.hide_action.setChecked(on)
        self.save_soon()

    # -- drawings --------------------------------------------------------------
    def open_editor(self, art_id):
        if self.editor is not None:
            self.editor.raise_()
            self.editor.activateWindow()
            return
        picture = self.library.get(art_id) if art_id else None
        as_copy = bool(picture) and art_id not in self.library.custom
        self.editor = Editor(None, picture, as_copy=as_copy)
        self.editor.saved.connect(self._drawing_saved)
        self.editor.finished.connect(self._editor_closed)
        self.editor.show()
        self.editor.raise_()
        self.editor.activateWindow()

    def _editor_closed(self):
        self.editor.deleteLater()
        self.editor = None

    def _drawing_saved(self, picture):
        is_new = picture["id"] not in self.library.custom
        self.library.set_custom(picture)
        self.park.refresh_art(picture["id"])
        self.board.rebuild()
        if is_new:
            self.add_art(picture["id"])
        self.save_soon()

    def delete_art(self, art_id):
        picture = self.library.custom.get(art_id)
        if not picture:
            return
        box = QMessageBox(QMessageBox.Question, "Desktop Park",
                          "Delete “%s”?\nAny copies in the park go too." % picture["name"],
                          QMessageBox.Yes | QMessageBox.No, self.board)
        box.setStyleSheet(BOARD_STYLE + "QMessageBox{background:#1d2230;} QLabel{color:#e6ebf7;}")
        if box.exec() != QMessageBox.Yes:
            return
        self.park.remove_art(art_id)
        self.library.remove_custom(art_id)
        self.board.rebuild()
        self.save_soon()

    # -- tray ------------------------------------------------------------------
    def _make_tray(self):
        self.tray = QSystemTrayIcon(QIcon(self.library.thumbnail("fish", 32)))
        self.tray.setToolTip("Desktop Park")
        menu = QMenu()
        menu.setStyleSheet(BOARD_STYLE)
        menu.addAction("Show the board", self.show_board)
        self.hide_action = QAction("Hide park", menu, checkable=True)
        self.hide_action.toggled.connect(lambda on: on != self.data["hidden"] and self.set_hidden(on))
        menu.addAction(self.hide_action)
        self.lock_action = QAction("Lock (clicks go through)", menu, checkable=True)
        self.lock_action.toggled.connect(lambda on: on != self.data["locked"] and self.set_locked(on))
        menu.addAction(self.lock_action)
        menu.addSeparator()
        menu.addAction("Quit Desktop Park", self.quit)
        self.tray.setContextMenu(menu)
        self._tray_menu = menu
        self.tray.activated.connect(self._tray_clicked)
        self.tray.show()

    def _tray_clicked(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_board()

    def show_board(self):
        self.board.show()
        self.board.raise_()

    def _board_closed(self):
        if not getattr(self, "_told_tray", False):
            self._told_tray = True
            self.tray.showMessage("Desktop Park", "The board is hiding in the tray icon. "
                                  "Click the fish to bring it back.", QSystemTrayIcon.Information, 4000)

    # -- housekeeping ----------------------------------------------------------
    def pin(self):
        """Stay above other windows. Skipped while a menu is open (it would
        bury the menu) or while a dialog is up."""
        if self.qapp.activePopupWidget() or self.qapp.activeModalWidget():
            return
        if self.park.isVisible():
            winutil.pin_topmost(int(self.park.winId()))
        if self.board.isVisible():
            winutil.pin_topmost(int(self.board.winId()))
        if self.editor is not None:
            winutil.pin_topmost(int(self.editor.winId()))

    def save_soon(self):
        self._save_timer.start()

    def save(self):
        self.data["custom_art"] = self.library.custom_list()
        self.data["objects"] = self.park.snapshot()
        self.data["board"] = {"x": self.board.x(), "y": self.board.y(),
                              "collapsed": self.board.collapsed}
        try:
            store.save(self.data)
        except OSError as e:
            print("save failed:", e, file=sys.stderr)

    def quit(self):
        self.quitting = True
        self.save()
        self.tray.hide()
        self.qapp.exit(0)


def main():
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Desktop Park")
    qapp.setWindowIcon(QIcon(Library([]).thumbnail("fish", 32)))
    if not winutil.acquire_single_instance():
        winutil.message_box("Desktop Park is already running.\n"
                            "Look for the fish in the tray (by the clock).", "Desktop Park")
        return 0
    app = App(qapp)
    qapp._park_app = app
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
