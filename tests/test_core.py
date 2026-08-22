from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            self.assertEqual(options["extractor_retries"], 5)
            self.assertEqual(
                options["extractor_args"]["youtube"]["player_client"],
                ["default", "-android_sdkless"],
            )
            self.assertIn("%(title)s", Path(options["outtmpl"]).parent.name)

    def test_download_options_use_available_js_runtime_for_youtube(self):
        node_path = r"C:\Program Files\nodejs\node.exe"

        def fake_which(executable):
            return node_path if executable == "node" else None

        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(Path(directory))
            with patch("shutil.which", side_effect=fake_which):
                options = manager._common_options()

        self.assertEqual(options["js_runtimes"], {"node": {"path": node_path}})

    def test_bundled_ffmpeg_is_used_in_frozen_build(self):
        with tempfile.TemporaryDirectory() as directory:
            ffmpeg = Path(directory) / "ffmpeg.exe"
            ffmpeg.write_bytes(b"bundled")
            with patch.object(sys, "_MEIPASS", directory, create=True):
                manager = DownloadManager(Path(directory) / "Downloads")
                self.assertEqual(manager._find_ffmpeg(), ffmpeg)
                self.assertEqual(manager._common_options()["ffmpeg_location"], str(ffmpeg))

    def test_transient_youtube_login_error_is_retried(self):
        import yt_dlp

        calls = []
        completions = []
        errors = []
        statuses = []

        class FlakyYoutubeDL:
            def __init__(self, options):
                self.options = options

            def __enter__(self):
                return self

            def __exit__(self, _exc_type, _exc, _traceback):
                return False

            def extract_info(self, _url, download=True):
                calls.append(self.options)
                if len(calls) == 1:
                    raise yt_dlp.utils.DownloadError(
                        "ERROR: [youtube] abc: Sign in to confirm you're not a bot"
                    )
                folder = Path(self.options["outtmpl"]).parent
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "Recovered title.mp3").write_bytes(b"audio")
                return {"title": "Recovered title"}

        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadManager(
                Path(directory),
                on_status=lambda message, level: statuses.append((message, level)),
                on_complete=lambda filepath, title: completions.append((filepath, title)),
                on_error=errors.append,
            )
            with (
                patch("time.sleep", return_value=None),
                patch("yt_dlp.YoutubeDL", FlakyYoutubeDL),
            ):
                manager._execute(
                    "https://www.youtube.com/watch?v=abc",
                    manager._common_options(),
                    "mp3",
                )

        self.assertEqual(len(calls), 2)
        self.assertEqual(errors, [])
        self.assertEqual(completions[0][1], "Recovered title")
        self.assertTrue(
            any("yeniden deneniyor" in message for message, _level in statuses)
        )


if __name__ == "__main__":
    unittest.main()
