import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # no windows on screen
    from PySide6.QtWidgets import QApplication
except ImportError:          # the CI test job runs without PySide6
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 not installed")
class BoardSizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def test_folding_shrinks_the_window(self):
        import board
        import sprites
        b = board.Board(sprites.Library([]))
        b.show()
        self.settle()
        open_h = b.height()
        b.toggle_collapsed()
        self.settle()
        self.assertLess(b.height(), open_h / 4)       # just the title bar left
        b.toggle_collapsed()
        self.settle()
        self.assertEqual(b.height(), open_h)

        b.set_update("9.9.9")
        self.settle()
        self.assertGreater(b.height(), open_h)
        b.set_update(None)
        self.settle()
        self.assertEqual(b.height(), open_h)          # no gap left behind
        b.close()



@unittest.skipIf(QApplication is None, "PySide6 not installed")
class FoldedBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def make(self):
        import board
        import sprites
        b = board.Board(sprites.Library([]))
        # tests must never pull a window onto the real screen: no clamping here
        b.place = lambda x, y, rect: b.move(int(x), int(y))
        b.move(-9000, -8000)
        b.show()
        self.settle()
        return b

    def test_folds_toward_the_bottom(self):
        b = self.make()
        bottom = b.y() + b.height()
        b.toggle_collapsed()
        self.settle()
        self.assertEqual(b.y() + b.height(), bottom)       # bottom edge stayed put
        self.assertLessEqual(b.height(), 48)                 # fits a Windows taskbar
        b.toggle_collapsed()
        self.settle()
        self.assertEqual(b.y() + b.height(), bottom)       # grew upward again
        b.close()

    def test_quick_buttons_stay_in_step(self):
        b = self.make()
        got = []
        b.lock_toggled.connect(lambda on: got.append(("lock", on)))
        b.hide_toggled.connect(lambda on: got.append(("hide", on)))
        b.weather_changed.connect(lambda k: got.append(("weather", k)))
        b.set_collapsed(True)
        b.quick_lock.click()
        b.quick_hide.click()
        b._weather_actions["snow"].trigger()
        self.assertEqual(got, [("lock", True), ("hide", True), ("weather", "snow")])
        self.assertTrue(b.lock_btn.isChecked() and b.hide_btn.isChecked())
        self.assertTrue(b.weather_btns["snow"].isChecked())
        b.lock_btn.click()                                    # the big button unlocks
        self.assertFalse(b.quick_lock.isChecked())
        b.close()

    def test_new_version_shows_small_when_folded(self):
        b = self.make()
        b.set_collapsed(True)
        b.set_update("9.9.9")
        self.settle()
        self.assertFalse(b.quick_update.isHidden())
        self.assertTrue(b.update_bar.isHidden())
        b.set_collapsed(False)
        self.assertTrue(b.quick_update.isHidden())
        self.assertFalse(b.update_bar.isHidden())
        b.close()

    def test_place_keeps_whole_board_on_screen(self):
        import board
        import sprites
        from PySide6.QtCore import QRect
        b = board.Board(sprites.Library([]))      # never shown: moving it is harmless
        b.set_collapsed(True)
        b.layout().activate()
        screen = QRect(0, 0, 1920, 1080)
        b.place(1900, 1070, screen)
        self.assertEqual(b.x() + b.width(), 1920)
        self.assertEqual(b.y() + b.height(), 1080)          # inside the taskbar is fine
        b.place(-50, -50, screen)
        self.assertEqual((b.x(), b.y()), (0, 0))


@unittest.skipIf(QApplication is None, "PySide6 not installed")
class LookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        import ui_style
        ui_style.install(self.app, "modern")

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def test_both_looks_fold_into_the_taskbar(self):
        import board
        import sprites
        import ui_style
        for theme in ui_style.THEMES:
            ui_style.install(self.app, theme)
            b = board.Board(sprites.Library([]))
            b.place = lambda x, y, rect, b=b: b.move(int(x), int(y))
            b.move(-9000, -8000)
            b.show()
            b.set_collapsed(True)
            self.settle()
            self.assertLessEqual(b.height(), 48, theme)
            b.close()

    def test_switching_keeps_state(self):
        import board
        import sprites
        import ui_style
        b = board.Board(sprites.Library([]))
        b.place = lambda x, y, rect: b.move(int(x), int(y))
        b.move(-9000, -8000)
        b.show()
        b.set_locked(True)
        b.set_hidden(True)
        b.set_weather("rain")
        self.assertEqual(b.hide_btn.text(), "Show park")          # the original wording
        ui_style.install(self.app, "pixel")
        b.apply_theme("pixel")
        self.assertTrue(b.lock_btn.isChecked() and b.quick_lock.isChecked())
        self.assertEqual(b.hide_btn.text(), "Show")
        self.assertTrue(b.weather_btns["rain"].isChecked())
        self.assertFalse(b.draw_btn.icon().isNull())              # pixel look has icons
        ui_style.install(self.app, "modern")
        b.apply_theme("modern")
        self.assertTrue(b.draw_btn.icon().isNull())
        self.assertEqual(b.weather_btns["clear"].text(), "Off")
        b.close()

    def test_theme_is_saved(self):
        import store
        self.assertEqual(store.clean({"theme": "pixel"})["theme"], "pixel")
        self.assertEqual(store.clean({"theme": "neon"})["theme"], "modern")


if __name__ == "__main__":
    unittest.main()
