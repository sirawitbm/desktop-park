import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store

NESTED = "[" * 200000 + "]" * 200000          # ~400 KB: under the import size cap


class StoreSafetyTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_deeply_nested_save_file_falls_back_to_the_backup(self):
        good = store.empty()
        good["weather"] = "snow"
        path = self.path("park.json")
        with open(path + ".bak", "w", encoding="utf-8") as f:
            json.dump(good, f)
        with open(path, "w", encoding="utf-8") as f:
            f.write(NESTED)
        self.assertEqual(store.load(path)["weather"], "snow")     # starts, from the .bak

    def test_deeply_nested_drawing_file_is_a_clear_error(self):
        path = self.path("bad.parkart")
        with open(path, "w", encoding="utf-8") as f:
            f.write(NESTED)
        with self.assertRaises(ValueError):
            store.import_drawing(path)

    def test_export_leaves_no_backup_or_temp_files(self):
        picture = {"id": "my-1", "name": "Frog", "kind": "pet", "behavior": "hop",
                   "palette": {"a": "#00ff00"}, "frames": [["a.", ".a"]]}
        path = self.path("frog.parkart")
        store.export_drawing(picture, path)
        store.export_drawing(picture, path)                      # overwrite it
        self.assertEqual(sorted(os.listdir(self.dir)), ["frog.parkart"])
        self.assertEqual(store.import_drawing(path)["name"], "Frog")

    def test_failed_save_leaves_no_temp_file(self):
        path = self.path("park.json")
        os.mkdir(path + ".tmp")                                  # makes the temp write fail
        try:
            with self.assertRaises(OSError):
                store.save(store.empty(), path)
        finally:
            os.rmdir(path + ".tmp")
        self.assertFalse(os.path.exists(path))

    def test_park_save_still_keeps_a_backup(self):
        path = self.path("park.json")
        store.save(store.empty(), path)
        store.save(store.empty(), path)
        self.assertTrue(os.path.exists(path + ".bak"))


if __name__ == "__main__":
    unittest.main()
