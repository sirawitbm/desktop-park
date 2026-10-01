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


if __name__ == "__main__":
    unittest.main()
