import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import winutil

try:
    os.environ["QT_QPA_PLATFORM"] = "offscreen" if os.name != "nt" else os.environ.get("QT_QPA_PLATFORM", "windows")
    from PySide6.QtWidgets import QApplication, QWidget
except ImportError:
    QApplication = None


@unittest.skipIf(os.name != "nt" or QApplication is None or not winutil.taskbars(),
                 "needs Windows with a taskbar (CI runners have none)")
class TaskbarOwnerTests(unittest.TestCase):
    """The folded bar stays above the taskbar by making the taskbar its owner."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if cls.app.platformName() != "windows":
            # other test files start Qt off-screen first; those windows are not
            # real Windows windows, so window ownership can't be tested there
            raise unittest.SkipTest("Qt is running off-screen, not as real Windows windows")

    def window(self):
        w = QWidget()
        w.setGeometry(-9000, -9000, 200, 40)        # far off-screen: nothing visible
        w.show()
        self.addCleanup(w.close)
        return int(w.winId())

    def test_a_window_off_the_taskbar_has_no_taskbar_under_it(self):
        self.assertIsNone(winutil.taskbar_under(self.window()))

    def test_owner_can_be_set_to_the_taskbar_and_cleared(self):
        hwnd = self.window()
        bar = winutil.taskbars()[0]
        self.assertTrue(winutil.set_owner(hwnd, bar))
        self.assertEqual(winutil.owner_of(hwnd), int(bar))
        self.assertTrue(winutil.set_owner(hwnd, 0))
        self.assertEqual(winutil.owner_of(hwnd), 0)

    def test_taskbar_rect_is_real(self):
        r = winutil.window_rect(winutil.taskbars()[0])
        self.assertIsNotNone(r)
        self.assertGreater(r[2] - r[0], 0)
        self.assertGreater(r[3] - r[1], 0)


if __name__ == "__main__":
    unittest.main()
