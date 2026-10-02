"""Desktop Park - little pixel pets and plants that live on top of your screen.

Run:  pythonw desktop_park.py
"""

import random
import sys
import threading

from PySide6.QtCore import QObject, QPoint, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

import daycycle
import store
import updates
import winutil
import ui_style
from board import Board
from editor import Editor
from park import ParkWindow
from weather import KINDS as WEATHER_KINDS, LABELS as WEATHER_LABELS
from weather_window import WeatherWindow
from sprites import Library

__version__ = "0.4.2"

UPDATE_FIRST_MS = 5000                 # first look for a new version
UPDATE_EVERY_MS = 6 * 3600 * 1000      # then every 6 hours


class _Inbox(QObject):
    """Carries results from background threads safely to the main thread."""
    update_result = Signal(object)


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
        ui_style.install(qapp, self.data["theme"])   # Modern or Pixel look
        self.library = Library(self.data["custom_art"])
        self.editor = None
        self._save_timer = QTimer(singleShot=True, interval=1500)
        self._save_timer.timeout.connect(self.save)

        self._screen_menus = []
        screen = self._saved_screen()
        self.screen = screen
        # weather first, so it sits behind the pets
        self.weather = WeatherWindow()
        self.weather.fit_screen(screen)
        self.weather.on_step = self._weather_step
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
        self.board.weather_changed.connect(self.set_weather)
        self.board.weather_auto.connect(self.set_weather_auto)
        self.board.time_mode_changed.connect(self.set_time_mode)
        self.board.show_sky_toggled.connect(self.set_show_sky)
        self.board.update_open.connect(self.open_update)
        self.board.update_later.connect(self.skip_update)
        area = screen.availableGeometry()
        b = self.data["board"]
        self.board.set_collapsed(b.get("collapsed", False))
        bx = b.get("x", area.right() - self.board.width() - 24)
        by = b.get("y", area.top() + 80)
        # the board may sit on a different monitor than the park - keep it there
        home = qapp.screenAt(QPoint(int(bx) + 20, int(by) + 10)) or screen
        self.board.place(bx, by, home.geometry())     # may sit in the taskbar

        self._make_tray()
        self.set_locked(self.data["locked"])
        self.set_weather(self.data["weather"])
        self.set_weather_auto(self.data["weather_auto"])
        self.board.set_time_mode(self.data["time_mode"])
        self.board.set_show_sky(self.data["show_sky"])
        self.set_hidden(self.data["hidden"])
        self.board.show()
        screen.availableGeometryChanged.connect(self._screen_resized)
        self.board.set_screen_menu(self._screen_menu(), len(qapp.screens()) > 1)
        qapp.screenAdded.connect(self._screens_changed)
        qapp.screenRemoved.connect(self._screens_changed)

        self._autosave = QTimer(interval=30000)       # pets wander; remember where
        self._autosave.timeout.connect(self.save)
        self._autosave.start()
        self._pin = QTimer(interval=2000)
        self._pin.timeout.connect(self.pin)
        self._pin.start()
        qapp.aboutToQuit.connect(self.save)

        self.update = None                       # (version, url) of a newer release
        self._inbox = _Inbox()
        self._inbox.update_result.connect(self._update_result)
        QTimer.singleShot(UPDATE_FIRST_MS, self._check_update)
        self._update_timer = QTimer(interval=UPDATE_EVERY_MS)
        self._update_timer.timeout.connect(self._check_update)
        self._update_timer.start()

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
        if box.exec() == QMessageBox.Yes:
            self.park.clear()

    def set_locked(self, on):
        self.data["locked"] = on
        self.park.set_locked(on)
        self.board.set_locked(on)
        self.lock_action.setChecked(on)
        self.save_soon()

    # -- monitors ----------------------------------------------------------------
    @staticmethod
    def _screen_key(s):
        """Model name plus position, so two identical monitors stay apart."""
        g = s.geometry()
        return "%s@%d,%d" % (s.name(), g.x(), g.y())

    def _saved_screen(self):
        saved = self.data.get("screen", "")
        screens = self.qapp.screens()
        for s in screens:                       # same monitor, same place
            if self._screen_key(s) == saved:
                return s
        for s in screens:                       # same monitor, moved around
            if s.name() == saved.rsplit("@", 1)[0]:
                return s
        return self.qapp.primaryScreen()

    def _screen_label(self, i, s):
        size = s.size()
        main = "  (main)" if s is self.qapp.primaryScreen() else ""
        return "Screen %d \u00b7 %d\u00d7%d%s" % (i + 1, size.width(), size.height(), main)

    def _screen_menu(self, parent=None):
        """A menu listing the monitors; it refreshes itself every time it opens."""
        menu = QMenu("Screen", parent)
        menu.aboutToShow.connect(lambda m=menu: self._fill_screen_menu(m))
        self._fill_screen_menu(menu)
        self._screen_menus.append(menu)
        return menu

    def _fill_screen_menu(self, menu):
        menu.clear()
        for i, s in enumerate(self.qapp.screens()):
            a = menu.addAction(self._screen_label(i, s), lambda s=s: self.move_to_screen(s))
            a.setCheckable(True)
            a.setChecked(s is self.screen)

    def _screens_changed(self, *_):
        """A monitor was plugged in or out. Wait a moment: Qt is still
        updating its list of screens when it tells us."""
        QTimer.singleShot(300, self._recheck_screens)

    def _recheck_screens(self):
        screens = self.qapp.screens()
        # our monitor gone -> main screen; it came back -> back there. The
        # saved choice is kept either way.
        wanted = self._saved_screen()
        if wanted is not self.screen:
            self.move_to_screen(wanted, remember=False)
        self.board.set_screen_menu(self.board.screen_btn.menu(), len(screens) > 1)
        self.tray_screen_menu.menuAction().setVisible(len(screens) > 1)

    def move_to_screen(self, screen, remember=True):
        old = self.screen
        if screen is old:
            return
        old_area = None
        try:
            old.availableGeometryChanged.disconnect(self._screen_resized)
            if old in self.qapp.screens():
                old_area = old.availableGeometry()
        except (RuntimeError, TypeError):      # that monitor was unplugged
            pass
        self.screen = screen
        screen.availableGeometryChanged.connect(self._screen_resized)
        self._fit(screen)
        # bring the board along if it was on the screen the park left
        new_area = screen.availableGeometry()
        board_home = self.qapp.screenAt(self.board.geometry().center())
        if old_area is None or board_home is None or board_home is old:
            if old_area is not None:
                x = new_area.left() + (self.board.x() - old_area.left()) / max(1, old_area.width()) * new_area.width()
                y = new_area.top() + (self.board.y() - old_area.top())
            else:
                x, y = new_area.right() - self.board.width() - 24, new_area.top() + 80
            self.board.place(x, y, screen.geometry())
        if remember:
            self.data["screen"] = self._screen_key(screen)
            self.save_soon()

    def _screen_resized(self, *_):
        self._fit(self.screen)

    def _fit(self, screen):
        self.park.fit_screen(screen)
        self.weather.fit_screen(screen)

    def set_hidden(self, on):
        self.data["hidden"] = on
        self.weather.setVisible(not on)
        self.park.setVisible(not on)
        self.board.set_hidden(on)
        self.hide_action.setChecked(on)
        self.save_soon()

    # -- day and night -------------------------------------------------------------
    def set_time_mode(self, mode):
        """Follow the clock, or keep it always day / always night."""
        self.data["time_mode"] = mode if mode in daycycle.MODES else "clock"
        for m, a in self.time_actions.items():
            a.setChecked(m == self.data["time_mode"])
        self.board.set_time_mode(self.data["time_mode"])
        self.save_soon()

    def set_show_sky(self, on):
        self.data["show_sky"] = bool(on)
        self.sky_action.setChecked(self.data["show_sky"])
        self.board.set_show_sky(self.data["show_sky"])
        self.weather.update()
        self.save_soon()

    # -- look --------------------------------------------------------------------
    def set_theme(self, theme):
        """Switch between the Modern and Pixel looks, right away."""
        ui_style.install(self.qapp, theme)
        self.data["theme"] = ui_style.current()
        self.board.apply_theme(ui_style.current())
        for t, a in self.look_actions.items():
            a.setChecked(t == ui_style.current())
        self.save_soon()

    # -- weather ---------------------------------------------------------------
    def set_weather(self, kind):
        if kind not in WEATHER_KINDS:
            kind = "clear"
        self.data["weather"] = kind
        self.weather.weather.set_kind(kind)
        self.board.set_weather(kind)
        for k, a in self.weather_actions.items():
            a.setChecked(k == kind)
        self.save_soon()

    def set_weather_auto(self, on):
        self.data["weather_auto"] = on
        self.weather.weather.set_auto(on)
        self.board.set_weather_auto(on)
        self.weather_auto_action.setChecked(on)
        self.save_soon()

    def _weather_step(self, w):
        self.park.world.wind = w.gust()
        # day and night: glowing lights, fireflies and sleepy pets after dark
        night = daycycle.night_level(mode=self.data["time_mode"])
        w.night = self.park.world.night = night
        w.glows = self.park.glows() if night > 0.02 else []
        self.park.world.lights = [(x, y, r) for x, y, r, _, _ in w.glows]
        w.sky = daycycle.sky(mode=self.data["time_mode"]) if self.data["show_sky"] else None
        if w.kind != self.data["weather"]:          # auto mode changed it
            self.set_weather(w.kind)

    # -- update check -----------------------------------------------------------
    def _check_update(self):
        """Ask GitHub for the newest release, off the main thread. Only reads -
        nothing is ever downloaded; we just offer a link to the page."""
        threading.Thread(target=lambda: self._inbox.update_result.emit(updates.latest_release()),
                         daemon=True).start()

    def _update_result(self, result):
        if not result:
            return                               # offline or GitHub hiccup: try later
        version, url = result
        fresh = self.update is None
        if updates.is_newer(version, __version__) and self.data.get("skip_update") != version:
            self.update = (version, url)
            if fresh:
                self.tray.showMessage("Desktop Park", "Version %s is out. Get it from the "
                                      "board or the tray menu." % version,
                                      QSystemTrayIcon.Information, 6000)
        else:
            self.update = None
        self._show_update()

    def _show_update(self):
        version = self.update[0] if self.update else None
        self.board.set_update(version)
        self.update_action.setVisible(bool(version))
        if version:
            self.update_action.setText("Download update %s" % version)

    def open_update(self):
        if self.update:
            QDesktopServices.openUrl(QUrl(self.update[1]))

    def skip_update(self):
        """Later: stay quiet about this version (a newer one still shows)."""
        if self.update:
            self.data["skip_update"] = self.update[0]
            self.save_soon()
        self.update = None
        self._show_update()

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
        menu.addAction("Show the board", self.show_board)
        self.hide_action = QAction("Hide park", menu, checkable=True)
        self.hide_action.toggled.connect(lambda on: on != self.data["hidden"] and self.set_hidden(on))
        menu.addAction(self.hide_action)
        self.lock_action = QAction("Lock (clicks go through)", menu, checkable=True)
        self.lock_action.toggled.connect(lambda on: on != self.data["locked"] and self.set_locked(on))
        menu.addAction(self.lock_action)
        wmenu = menu.addMenu("Weather")
        self.weather_actions = {}
        for kind in WEATHER_KINDS:
            a = QAction(WEATHER_LABELS[kind], wmenu, checkable=True)
            a.triggered.connect(lambda _=False, k=kind: self.set_weather(k))
            wmenu.addAction(a)
            self.weather_actions[kind] = a
        wmenu.addSeparator()
        self.weather_auto_action = QAction("Changes by itself", wmenu, checkable=True)
        self.weather_auto_action.triggered.connect(self.set_weather_auto)
        wmenu.addAction(self.weather_auto_action)
        tmenu = menu.addMenu("Time of day")
        self.time_actions = {}
        tgroup = QActionGroup(tmenu)
        for mode in daycycle.MODES:
            a = QAction(daycycle.LABELS[mode], tmenu, checkable=True)
            a.setChecked(mode == self.data["time_mode"])
            a.triggered.connect(lambda _=False, m=mode: self.set_time_mode(m))
            tgroup.addAction(a)
            tmenu.addAction(a)
            self.time_actions[mode] = a
        tmenu.addSeparator()
        self.sky_action = QAction("Show sun && moon", tmenu, checkable=True)
        self.sky_action.setChecked(self.data["show_sky"])
        self.sky_action.triggered.connect(self.set_show_sky)
        tmenu.addAction(self.sky_action)
        lmenu = menu.addMenu("Look")
        self.look_actions = {}
        group = QActionGroup(lmenu)
        for theme in ui_style.THEMES:
            a = QAction(ui_style.LABELS[theme], lmenu, checkable=True)
            a.setChecked(theme == ui_style.current())
            a.triggered.connect(lambda _=False, t=theme: self.set_theme(t))
            group.addAction(a)
            lmenu.addAction(a)
            self.look_actions[theme] = a
        self.tray_screen_menu = self._screen_menu(menu)
        menu.addMenu(self.tray_screen_menu)
        self.tray_screen_menu.menuAction().setVisible(len(self.qapp.screens()) > 1)
        menu.addSeparator()
        self.update_action = menu.addAction("Download update", self.open_update)
        self.update_action.setVisible(False)
        menu.addAction("About Desktop Park %s" % __version__,
                       lambda: QDesktopServices.openUrl(QUrl("https://github.com/" + updates.REPO)))
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
        if self.weather.isVisible():
            winutil.pin_topmost(int(self.weather.winId()))
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
