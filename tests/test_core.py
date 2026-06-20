from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.download_manager import DownloadManager
from core.library_service import scan_library
from core.settings_store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def test_default_downloads_share_the_app_data_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = SettingsStore(
                data_root=root,
                migrate_legacy=False,
            )
            self.assertEqual(store.settings_path, root / "settings.ini")
            self.assertEqual(store.downloads_dir, root / "Downloads")
            self.assertTrue(store.downloads_dir.is_dir())

    def test_manual_download_folder_override_is_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            custom = root / "Custom"
            store = SettingsStore(data_root=root, migrate_legacy=False)
            store.set("downloads_dir", str(custom))
            reopened = SettingsStore(data_root=root, migrate_legacy=False)
            self.assertEqual(reopened.downloads_dir, custom)


class LibraryTests(unittest.TestCase):
    def test_scan_reads_title_quality_and_thumbnail_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "downloaded-video.mp4"
            media.write_bytes(b"video")
            (root / "downloaded-video.info.json").write_text(
                json.dumps(
                    {
                        "title": "Gerçek YouTube Başlığı",
                        "height": 1080,
                        "webpage_url": "https://youtu.be/example",
                    }
                ),
                encoding="utf-8",
            )
            thumbnail = root / "downloaded-video.webp"
            thumbnail.write_bytes(b"thumbnail")

            items = scan_library(root)

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["title"], "Gerçek YouTube Başlığı")
            self.assertEqual(items[0]["quality"], "1080p")
            self.assertEqual(items[0]["thumbnail"], str(thumbnail))

    def test_download_options_persist_metadata_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(Path(directory))
            options = manager._common_options()
            self.assertTrue(options["writeinfojson"])
            self.assertTrue(options["writethumbnail"])


if __name__ == "__main__":
    unittest.main()
