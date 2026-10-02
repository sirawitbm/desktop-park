import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 not installed")
class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def editor(self):
        from editor import Editor
        editor = Editor()
        editor._pv.stop()
        self.addCleanup(editor.deleteLater)
        return editor

    def owner(self):
        from board import Board
        from desktop_park import App
        from park import ParkWindow
        from sprites import Library
        import store
        owner = App.__new__(App)
        owner.data = store.empty()
        owner.library = Library([])
        owner.park = ParkWindow(owner.library)
        owner.park.timer.stop()
        owner.park.world.resize(800, 600)
        owner.board = Board(owner.library)
        owner.editor = None
        owner._last_save_error = None
        owner._save_timer = QTimer()
        owner.tray = Mock()
        from weather_window import WeatherWindow
        owner.weather = WeatherWindow()
        owner.weather.timer.stop()
        owner.weather_actions = {kind: Mock() for kind in ("clear", "sun", "rain", "snow", "wind")}
        owner.time_actions = {mode: Mock() for mode in ("clock", "day", "night")}
        owner.weather_auto_action = Mock()
        owner.sky_action = Mock()
        owner.hide_action = Mock()
        owner.power_action = Mock()
        owner.park.scene_restored.connect(owner._apply_scene_settings)
        self.addCleanup(owner.park.deleteLater)
        self.addCleanup(owner.board.deleteLater)
        self.addCleanup(owner.weather.deleteLater)
        return owner

    def test_cancel_keeps_modified_editor_open_and_discard_closes(self):
        editor = self.editor()
        editor.show()
        editor.pixels()[0][0] = "#ffffff"
        with patch("editor.QMessageBox.question", return_value=QMessageBox.Cancel):
            editor.close()
        self.assertTrue(editor.isVisible())
        with patch("editor.QMessageBox.question", return_value=QMessageBox.Discard):
            editor.close()
        self.assertFalse(editor.isVisible())

    def test_undo_returns_to_clean_state_and_metadata_is_dirty(self):
        editor = self.editor()
        editor.push_undo()
        editor.pixels()[0][0] = "#ffffff"
        self.assertTrue(editor.is_dirty())
        editor.undo()
        self.assertFalse(editor.is_dirty())
        editor.name.setText("New name")
        self.assertTrue(editor.is_dirty())

    def test_rejected_save_keeps_drawing_open(self):
        editor = self.editor()
        editor.pixels()[0][0] = "#ffffff"
        editor.saved.connect(lambda picture: setattr(editor, "save_error", "disk full"))
        editor.show()
        with patch("editor.QMessageBox.warning"):
            self.assertFalse(editor._save())
        self.assertTrue(editor.isVisible())
        self.assertTrue(editor.is_dirty())

    def test_save_failure_stays_visible_until_successful_retry(self):
        owner = self.owner()
        with patch("desktop_park.store.save", side_effect=OSError("disk full")):
            self.assertFalse(owner.save())
            self.assertFalse(owner.save())
        self.assertEqual(owner._last_save_error, "disk full")
        self.assertFalse(owner.board.save_bar.isHidden())
        self.assertEqual(owner.tray.showMessage.call_count, 1)
        owner.board.set_collapsed(True)
        self.assertFalse(owner.board.quick_save.isHidden())
        with patch("desktop_park.store.save"):
            self.assertTrue(owner.save())
        self.assertTrue(owner.board.quick_save.isHidden())

    def test_new_drawing_save_is_immediate_and_failure_rolls_back(self):
        owner = self.owner()
        owner.editor = self.editor()
        owner.editor.pixels()[0][0] = "#ffffff"
        picture = owner.editor.to_picture()
        with patch("desktop_park.store.save", side_effect=OSError("disk full")):
            owner._drawing_saved(picture)
        self.assertNotIn(picture["id"], owner.library.custom)
        self.assertEqual(owner.park.snapshot(), [])
        self.assertEqual(owner.editor.save_error, "disk full")
        with patch("desktop_park.store.save") as save:
            owner._drawing_saved(picture)
        save.assert_called_once()
        self.assertIn(picture["id"], owner.library.custom)
        self.assertEqual(len(owner.park.snapshot()), 1)

    def test_save_from_close_confirmation_emits_once(self):
        editor = self.editor()
        editor.pixels()[0][0] = "#ffffff"
        saved = []
        finished = []
        editor.saved.connect(saved.append)
        editor.finished.connect(finished.append)
        editor.show()
        with patch("editor.QMessageBox.question", return_value=QMessageBox.Save):
            editor.close()
        self.assertEqual(len(saved), 1)
        self.assertEqual(len(finished), 1)
        self.assertFalse(editor.isVisible())

    def test_remove_and_resize_invalidate_entire_shadow(self):
        from PySide6.QtGui import QRegion
        owner = self.owner()
        park = owner.park
        thing = park.add_art("tree", scale=3)
        thing.x = 200
        shadow = park._shadow_rect(thing)
        with patch.object(park, "update") as update:
            park._remove(thing)
        self.assertTrue(QRegion(shadow).subtracted(QRegion(update.call_args.args[0])).isEmpty())
        park.undo()
        thing = park.world.things[0]
        shadow = park._shadow_rect(thing)
        with patch.object(park, "update") as update:
            park.set_scale(thing, 5)
        self.assertTrue(QRegion(shadow).subtracted(update.call_args.args[0]).isEmpty())

    def test_light_radius_changes_invalidate_static_objects(self):
        owner = self.owner()
        park = owner.park
        park.add_art("tree", scale=3)
        park.world.night = 1.0
        park.world.lights = [(100, 100, 50)]
        with patch.object(park, "isVisible", return_value=True):
            park._tick()
            park.world.lights = [(100, 100, 500)]
            with patch.object(park, "update") as update:
                park._tick()
        self.assertIn((), [call.args for call in update.call_args_list])

    def test_undo_restores_remove_clear_scale_and_behavior(self):
        owner = self.owner()
        park = owner.park
        for action in (lambda thing: park._remove(thing), lambda thing: park.clear(),
                       lambda thing: park.set_scale(thing, 5),
                       lambda thing: park._set_behavior(thing, "fly")):
            park.load_things([])
            thing = park.add_art("tree", scale=3)
            before = park.snapshot()
            action(thing)
            park.undo()
            self.assertEqual(park.snapshot(), before)
            park.undo()
            self.assertEqual(park.snapshot(), [])

    def test_cache_evicts_cold_entries_and_accounts_for_memory(self):
        from PySide6.QtGui import QPixmap
        from sprites import Library
        library = Library([])
        library.cache_entries = 3
        for index in range(3):
            library._store(("probe", index), QPixmap(8, 8))
        library._cached(("probe", 0))
        library._store(("probe", 3), QPixmap(8, 8))
        self.assertIn(("probe", 0), library._pixmaps)
        self.assertNotIn(("probe", 1), library._pixmaps)
        self.assertEqual(len(library._pixmaps), 3)
        library.forget("probe")
        self.assertEqual(library._pixmap_bytes, 0)
        library.cache_bytes = 256
        library._store(("probe", 0), QPixmap(8, 8))
        library._store(("probe", 1), QPixmap(8, 8))
        self.assertEqual(len(library._pixmaps), 1)
        self.assertLessEqual(library._pixmap_bytes, library.cache_bytes)

    def test_preset_load_restores_environment_and_can_be_undone(self):
        owner = self.owner()
        owner.park.add_art("tree", scale=3)
        before = owner.park.snapshot()
        owner.set_weather("snow")
        with patch("desktop_park.store.save"):
            self.assertTrue(owner.save_preset("Winter"))
        owner.park.clear()
        owner.set_weather("clear")
        self.assertTrue(owner.load_preset("Winter"))
        self.assertEqual(owner.park.snapshot(), before)
        self.assertEqual(owner.data["weather"], "snow")
        owner.park.undo()
        self.assertEqual(owner.park.snapshot(), [])
        self.assertEqual(owner.data["weather"], "clear")

    def test_preset_load_adapts_grounded_objects_to_screen_size(self):
        owner = self.owner()
        owner.park.add_art("tree", scale=3)
        with patch("desktop_park.store.save"):
            owner.save_preset("Garden")
        owner.park.clear()
        owner.park.world.resize(1200, 800)
        owner.load_preset("Garden")
        thing = owner.park.world.things[0]
        self.assertEqual(thing.y + thing.h, 800)
        self.assertTrue(0 <= thing.x <= 1200 - thing.w)

    def test_failed_preset_save_keeps_previous_presets(self):
        owner = self.owner()
        with patch("desktop_park.store.save", side_effect=OSError("disk full")):
            self.assertFalse(owner.save_preset("Garden"))
        self.assertEqual(owner.data["presets"], [])

    def test_importing_same_drawing_twice_creates_independent_ids(self):
        import store
        owner = self.owner()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "cat.parkart")
            store.export_drawing(owner.library.get("cat"), path)
            with patch("desktop_park.store.save"):
                self.assertTrue(owner.import_art(path))
                self.assertTrue(owner.import_art(path))
        self.assertEqual(len(owner.library.custom), 2)
        self.assertEqual(len(owner.park.world.things), 2)
        self.assertNotIn("cat", owner.library.custom)

    def test_low_power_changes_update_rates_not_simulation_time(self):
        owner = self.owner()
        owner.set_low_power(True)
        owner.park.timer.stop()
        owner.weather.timer.stop()
        self.assertEqual(owner.park.timer.interval(), 67)
        self.assertEqual(owner.weather.timer.interval(), 100)
        owner.weather.weather.set_kind("rain")
        with patch.object(owner.weather, "isVisible", return_value=True):
            for _ in range(10):
                owner.weather._tick()
        self.assertAlmostEqual(owner.weather.weather.t, 1.0)
        self.assertTrue(owner.data["low_power"])
        owner.set_low_power(False)
        owner.park.timer.stop()
        owner.weather.timer.stop()
        self.assertEqual(owner.weather.timer.interval(), 50)

    def test_preset_menu_actions_emit_the_preset_name(self):
        owner = self.owner()
        owner.board.set_presets([{"name": "Garden"}])
        names = []
        owner.board.preset_load.connect(names.append)
        owner.board.presets_btn.menu().actions()[-1].menu().actions()[0].trigger()
        self.assertEqual(names, ["Garden"])

    def test_pose_images_are_separate_from_walk_frames(self):
        owner = self.owner()
        thing = owner.park.add_art("cat", scale=3)
        self.assertEqual(owner.library.frame_count("cat"), 4)
        thing.reaction = "sleep"
        sleep = owner.park._frame(thing)
        self.assertGreaterEqual(sleep, 4)
        self.assertFalse(owner.library.pixmap("cat", sleep, 3, False).isNull())
        self.assertEqual(len(owner.library.images("cat")), 6)

    def test_rename_delete_and_overwrite_preset_confirmations(self):
        owner = self.owner()
        with patch("desktop_park.store.save"):
            owner.save_preset("Garden")
            self.assertTrue(owner.rename_preset("Garden", "Evening"))
        with patch("desktop_park.QMessageBox.question", return_value=QMessageBox.No):
            self.assertFalse(owner.save_preset("Evening"))
            self.assertFalse(owner.delete_preset("Evening"))
        with patch("desktop_park.QMessageBox.question", return_value=QMessageBox.Yes), \
                patch("desktop_park.store.save"):
            self.assertTrue(owner.delete_preset("Evening"))
        self.assertEqual(owner.data["presets"], [])

    def test_export_failure_is_reported_without_changing_the_park(self):
        owner = self.owner()
        before = owner.park.snapshot()
        with patch("desktop_park.store.export_drawing", side_effect=OSError("disk full")), \
                patch("desktop_park.QMessageBox.warning") as warning:
            self.assertFalse(owner.export_art("cat", "ignored.parkart"))
        warning.assert_called_once()
        self.assertEqual(owner.park.snapshot(), before)

    def test_corrupt_import_keeps_existing_drawings_and_objects(self):
        owner = self.owner()
        owner.park.add_art("cat")
        before = owner.park.snapshot()
        with patch("desktop_park.store.import_drawing", side_effect=ValueError("bad format")), \
                patch("desktop_park.QMessageBox.warning") as warning:
            self.assertFalse(owner.import_art("ignored.parkart"))
        warning.assert_called_once()
        self.assertEqual(owner.park.snapshot(), before)
        self.assertEqual(owner.library.custom, {})

    def test_quit_refuses_to_exit_when_saving_fails(self):
        owner = self.owner()
        owner.qapp = Mock()
        owner.quitting = False
        with patch("desktop_park.store.save", side_effect=OSError("disk full")), \
                patch.object(owner, "show_board"):
            owner.quit()
        owner.qapp.exit.assert_not_called()
        self.assertFalse(owner.quitting)

    def test_small_light_movements_invalidate_static_objects(self):
        owner = self.owner()
        park = owner.park
        park.world.night = 1.0
        park.world.lights = [(100, 100, 50)]
        with patch.object(park, "isVisible", return_value=True):
            park._tick()
            park.world.lights = [(101, 100, 50)]
            with patch.object(park, "update") as update:
                park._tick()
        self.assertIn((), [call.args for call in update.call_args_list])

    def test_undo_after_screen_change_preserves_ground_contact(self):
        owner = self.owner()
        park = owner.park
        thing = park.add_art("tree", scale=3)
        park._remove(thing)
        park.world.relocate(1200, 800)
        park.undo()
        restored = park.world.things[0]
        self.assertEqual(restored.y + restored.h, 800)
        self.assertLessEqual(restored.x + restored.w, 1200)

    def test_escape_cancel_keeps_dirty_editor_open(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        editor = self.editor()
        editor.pixels()[0][0] = "#ffffff"
        editor.show()
        with patch("editor.QMessageBox.question", return_value=QMessageBox.Cancel):
            QTest.keyClick(editor, Qt.Key_Escape)
        self.assertTrue(editor.isVisible())
        with patch("editor.QMessageBox.question", return_value=QMessageBox.Discard):
            editor.reject()

    def test_drag_start_invalidates_ground_shadow_and_undo_restores_position(self):
        from PySide6.QtCore import QPoint, QPointF
        from PySide6.QtGui import QRegion
        owner = self.owner()
        park = owner.park
        thing = park.add_art("tree", scale=3)
        before = park.snapshot()
        shadow = park._shadow_rect(thing)
        point = QPoint(int(thing.x + 10), int(thing.y + 10))
        park._press = (thing, point, QPoint(10, 10))
        event = Mock()
        event.position.return_value = QPointF(point + QPoint(20, -30))
        with patch.object(park, "update") as update:
            park.mouseMoveEvent(event)
        self.assertTrue(QRegion(shadow).subtracted(QRegion(update.call_args_list[0].args[0])).isEmpty())
        park.undo()
        self.assertEqual(park.snapshot(), before)
        self.assertIsNone(park._press)

    def test_hover_preview_has_sprite_pixels_and_name(self):
        from board import PictureButton
        from PySide6.QtWidgets import QLabel
        owner = self.owner()
        button = next(button for button in owner.board.findChildren(PictureButton)
                      if button.picture["id"] == "snail")
        labels = button.preview().findChildren(QLabel)
        image = next(label for label in labels if not label.pixmap().isNull()).pixmap().toImage()
        self.assertTrue(any(image.pixelColor(x, y).alpha() > 0 for y in range(image.height())
                            for x in range(image.width())))
        self.assertIn("Snail", [label.text() for label in labels])