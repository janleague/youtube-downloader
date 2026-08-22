from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from core.download_manager import DownloadManager
from core.engine_updater import EngineUpdater
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
            self.assertNotIn("extractor_args", options)
            self.assertTrue(options["cachedir"].endswith("engine\\cache"))
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

        class StaticEngineUpdater:
            def __init__(self, cache_dir):
                self.cache_dir = cache_dir
                self.load_calls = []

            def load(self, force_update=False):
                self.load_calls.append(force_update)
                return yt_dlp

            @staticmethod
            def ensure_js_runtime():
                return None

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
            updater = StaticEngineUpdater(Path(directory) / "engine-cache")
            manager = DownloadManager(
                Path(directory),
                on_status=lambda message, level: statuses.append((message, level)),
                on_complete=lambda filepath, title: completions.append((filepath, title)),
                on_error=errors.append,
                engine_updater=updater,
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
        self.assertEqual(updater.load_calls, [False, True])
        self.assertEqual(errors, [])
        self.assertEqual(completions[0][1], "Recovered title")
        self.assertTrue(
            any("yeniden deneniyor" in message for message, _level in statuses)
        )


class EngineUpdaterTests(unittest.TestCase):
    @staticmethod
    def _fake_engine_bytes(version: str = "2099.01.01") -> bytes:
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("yt_dlp/__init__.py", "")
            archive.writestr(
                "yt_dlp/version.py",
                f"__version__ = '{version}'\n",
            )
        output.seek(0)
        return output.read()

    @classmethod
    def _write_fake_engine(cls, folder: Path) -> tuple[Path, str]:
        engine = folder / "yt-dlp"
        engine.write_bytes(cls._fake_engine_bytes())
        digest = hashlib.sha256(engine.read_bytes()).hexdigest()
        (folder / "yt-dlp.sha256").write_text(digest, encoding="ascii")
        return engine, digest

    def test_verified_bundled_engine_is_copied_to_private_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            _source, digest = self._write_fake_engine(bundle)
            updater = EngineUpdater(
                data_root=root / "data",
                bundled_root=bundle,
                clock=lambda: 0,
            )

            engine = updater.ensure_engine()

            self.assertIsNotNone(engine)
            self.assertEqual(hashlib.sha256(engine.read_bytes()).hexdigest(), digest)
            self.assertEqual(updater._state["engine_version"], "2099.01.01")

    def test_tampered_bundled_engine_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            self._write_fake_engine(bundle)
            (bundle / "yt-dlp").write_bytes(b"tampered")
            updater = EngineUpdater(
                data_root=root / "data",
                bundled_root=bundle,
                clock=lambda: 0,
            )
            with patch.object(updater, "_download", side_effect=OSError("offline")):
                engine = updater.ensure_engine()

            self.assertIsNone(engine)

    def test_bundled_deno_is_copied_without_system_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            deno = bundle / "deno.exe"
            deno.write_bytes(b"deno-binary")
            digest = hashlib.sha256(deno.read_bytes()).hexdigest()
            (bundle / "deno.exe.sha256").write_text(digest, encoding="ascii")
            updater = EngineUpdater(
                data_root=root / "data",
                bundled_root=bundle,
                clock=lambda: 0,
            )

            with patch.object(
                updater,
                "_deno_works",
                side_effect=lambda path: path.is_file(),
            ):
                runtime = updater.ensure_js_runtime()

            self.assertEqual(runtime, ("deno", updater.deno_path))
            self.assertEqual(updater.deno_path.read_bytes(), b"deno-binary")

    def test_verified_remote_update_keeps_previous_engine_for_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            _source, old_digest = self._write_fake_engine(bundle)
            updater = EngineUpdater(
                data_root=root / "data",
                bundled_root=bundle,
                clock=lambda: 0,
            )
            old_engine = updater.ensure_engine()
            new_data = self._fake_engine_bytes("2099.02.02")
            new_digest = hashlib.sha256(new_data).hexdigest()

            def fake_download(url, _maximum_size):
                if url == updater.CHECKSUMS_URL:
                    return f"{new_digest}  yt-dlp\n".encode()
                return new_data

            with patch.object(updater, "_download", side_effect=fake_download):
                new_engine = updater.ensure_engine(force_update=True)

            self.assertNotEqual(new_engine, old_engine)
            self.assertEqual(updater._state["engine_version"], "2099.02.02")
            self.assertEqual(
                updater._state["previous_engine_file"], old_engine.name
            )
            self.assertEqual(
                hashlib.sha256(old_engine.read_bytes()).hexdigest(),
                old_digest,
            )

    def test_bad_remote_update_keeps_current_verified_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            self._write_fake_engine(bundle)
            updater = EngineUpdater(
                data_root=root / "data",
                bundled_root=bundle,
                clock=lambda: 0,
            )
            current = updater.ensure_engine()
            claimed_digest = "a" * 64

            def fake_download(url, _maximum_size):
                if url == updater.CHECKSUMS_URL:
                    return f"{claimed_digest}  yt-dlp\n".encode()
                return b"tampered"

            with patch.object(updater, "_download", side_effect=fake_download):
                after_update = updater.ensure_engine(force_update=True)

            self.assertEqual(after_update, current)
            self.assertIn(
                "doğrulaması başarısız",
                updater._state["last_engine_error"],
            )


if __name__ == "__main__":
    unittest.main()
