import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store
import updates


class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(updates.parse_version("v0.2.0"), (0, 2, 0))
        self.assertIsNone(updates.parse_version("latest"))
        self.assertTrue(updates.is_newer("v0.10.0", "0.9.9"))
        self.assertFalse(updates.is_newer("0.2.0", "0.2.0"))
        self.assertFalse(updates.is_newer("junk", "0.2.0"))

    def fake(self, payload):
        resp = mock.MagicMock()
        resp.__enter__.return_value.read.return_value = payload.encode()
        return mock.patch("urllib.request.urlopen", return_value=resp)

    def test_latest_release(self):
        page = "https://github.com/sirawitbm/desktop-park/releases/tag/v0.3.0"
        with self.fake('{"tag_name": "v0.3.0", "html_url": "%s"}' % page):
            self.assertEqual(updates.latest_release(), ("0.3.0", page))

    def test_only_opens_our_own_page(self):
        with self.fake('{"tag_name": "v0.3.0", "html_url": "https://evil.example/x"}'):
            self.assertEqual(updates.latest_release()[1], updates.RELEASES_PAGE)

    def test_skips_prereleases_and_errors(self):
        with self.fake('{"tag_name": "v0.3.0", "prerelease": true}'):
            self.assertIsNone(updates.latest_release())
        with self.fake("not json"):
            self.assertIsNone(updates.latest_release())
        with mock.patch("urllib.request.urlopen", side_effect=OSError):
            self.assertIsNone(updates.latest_release())

    def test_skip_is_saved(self):
        self.assertEqual(store.clean({"skip_update": "0.3.0"})["skip_update"], "0.3.0")
        self.assertEqual(store.clean({"skip_update": 5})["skip_update"], "")


if __name__ == "__main__":
    unittest.main()
