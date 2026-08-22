"""Self-updating yt-dlp engine and JavaScript runtime management."""

from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import ClassVar

from .settings_store import default_data_root


StatusCallback = Callable[[str, str], None]


class EngineUpdateError(RuntimeError):
    """Raised when no usable yt-dlp engine can be prepared."""


class _YtDlpEngineFinder(importlib.abc.MetaPathFinder):
    """Prefer the downloaded zipapp over PyInstaller's bundled modules."""

    def __init__(self, engine_path: Path):
        self.engine_path = str(engine_path)

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "yt_dlp":
            return importlib.machinery.PathFinder.find_spec(
                fullname, [self.engine_path], target
            )
        if fullname.startswith("yt_dlp."):
            return importlib.machinery.PathFinder.find_spec(
                fullname, path, target
            )
        return None


class EngineUpdater:
    """Keep yt-dlp nightly and Deno current without an application release."""

    ENGINE_CHECK_INTERVAL = 6 * 60 * 60
    DENO_CHECK_INTERVAL = 7 * 24 * 60 * 60
    ENGINE_URL = (
        "https://github.com/yt-dlp/yt-dlp-nightly-builds/"
        "releases/latest/download/yt-dlp"
    )
    CHECKSUMS_URL = (
        "https://github.com/yt-dlp/yt-dlp-nightly-builds/"
        "releases/latest/download/SHA2-256SUMS"
    )
    USER_AGENT = "YouTubeDownloader/2.2.7"
    MAX_ENGINE_SIZE = 20 * 1024 * 1024

    _engine_paths: ClassVar[set[str]] = set()

    def __init__(
        self,
        data_root: Path | None = None,
        bundled_root: Path | None = None,
        on_status: StatusCallback | None = None,
        clock: Callable[[], float] = time.time,
    ):
        self.data_root = Path(data_root) if data_root else default_data_root()
        self.engine_dir = self.data_root / "engine"
        self.cache_dir = self.engine_dir / "cache"
        self.state_path = self.engine_dir / "state.json"
        self.deno_path = self.engine_dir / "deno.exe"
        self._bundled_root = Path(bundled_root) if bundled_root else None
        self.on_status = on_status
        self._clock = clock
        self._state = self._read_state()
        self.engine_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, force_update: bool = False):
        """Load the newest verified engine, falling back to bundled yt-dlp."""
        engine_path = self.ensure_engine(force_update=force_update)
        if engine_path:
            try:
                return self._activate_engine(engine_path)
            except Exception as exc:
                self._state["last_load_error"] = str(exc)[:300]
                previous = self._previous_engine_path()
                if previous and previous != engine_path:
                    try:
                        module = self._activate_engine(previous)
                        self._activate_state_engine(previous)
                        self._write_state()
                        return module
                    except Exception:
                        pass

        try:
            self._remove_engine_paths()
            return importlib.import_module("yt_dlp")
        except ImportError as exc:
            raise EngineUpdateError(
                "İndirme motoru yüklenemedi. İnternet bağlantınızı kontrol edin."
            ) from exc

    def ensure_engine(self, force_update: bool = False) -> Path | None:
        active = self._active_engine_path()
        if active is None:
            active = self._install_bundled_engine()

        last_check = float(self._state.get("last_engine_check", 0) or 0)
        stale = self._clock() - last_check >= self.ENGINE_CHECK_INTERVAL
        if force_update or active is None or stale:
            try:
                active = self._refresh_engine(active)
                self._state.pop("last_engine_error", None)
            except Exception as exc:
                self._state["last_engine_error"] = str(exc)[:300]
            finally:
                self._state["last_engine_check"] = self._clock()
                self._write_state()

        if active:
            self._cleanup_old_engines(active)
        return active

    def ensure_js_runtime(self) -> tuple[str, Path] | None:
        """Return a supported runtime, preferring the private Deno copy."""
        if not self._deno_works(self.deno_path):
            self._install_bundled_deno()

        if self._deno_works(self.deno_path):
            last_check = float(self._state.get("last_deno_check", 0) or 0)
            if self._clock() - last_check >= self.DENO_CHECK_INTERVAL:
                self._upgrade_deno()
                self._state["last_deno_check"] = self._clock()
                self._write_state()
            return "deno", self.deno_path
        return None

    def _refresh_engine(self, active: Path | None) -> Path:
        checksums = self._download(self.CHECKSUMS_URL, 256 * 1024)
        expected = self._checksum_for(checksums.decode("utf-8", "replace"))
        if active and self._sha256(active) == expected:
            return active

        self._status("İndirme motoru otomatik güncelleniyor...", "info")
        engine_data = self._download(self.ENGINE_URL, self.MAX_ENGINE_SIZE)
        actual = hashlib.sha256(engine_data).hexdigest()
        if actual != expected:
            raise EngineUpdateError("İndirme motoru doğrulaması başarısız oldu.")
        return self._store_engine(engine_data, actual, active)

    def _install_bundled_engine(self) -> Path | None:
        root = self._get_bundled_root()
        if root is None:
            return None
        source = root / "yt-dlp"
        if not source.is_file():
            return None

        expected = self._read_hash_file(root / "yt-dlp.sha256")
        actual = self._sha256(source)
        if expected and expected != actual:
            return None
        try:
            return self._store_engine(source.read_bytes(), actual, None)
        except (OSError, EngineUpdateError):
            return None

    def _store_engine(
        self, data: bytes, digest: str, previous: Path | None
    ) -> Path:
        version = self._validate_engine(data)
        destination = self.engine_dir / f"yt-dlp-{digest}.pyz"
        if not destination.is_file():
            temporary = self.engine_dir / (
                f".{destination.name}.{os.getpid()}.tmp"
            )
            try:
                with temporary.open("wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)

        current = self._active_engine_path()
        previous = previous or current
        if previous and previous != destination:
            self._state["previous_engine_file"] = previous.name
        self._state.update({
            "engine_file": destination.name,
            "engine_sha256": digest,
            "engine_version": version,
        })
        self._write_state()
        return destination

    @staticmethod
    def _validate_engine(data: bytes) -> str:
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                version_source = archive.read("yt_dlp/version.py").decode(
                    "utf-8", "strict"
                )
        except (KeyError, OSError, UnicodeError, zipfile.BadZipFile) as exc:
            raise EngineUpdateError("Geçersiz indirme motoru paketi.") from exc
        match = re.search(
            r"^__version__\s*=\s*['\"]([^'\"]+)",
            version_source,
            re.MULTILINE,
        )
        if not match:
            raise EngineUpdateError("İndirme motoru sürümü okunamadı.")
        return match.group(1)

    def _active_engine_path(self) -> Path | None:
        return self._state_engine_path("engine_file", "engine_sha256")

    def _previous_engine_path(self) -> Path | None:
        return self._state_engine_path("previous_engine_file")

    def _state_engine_path(
        self, file_key: str, hash_key: str | None = None
    ) -> Path | None:
        raw_name = str(self._state.get(file_key, "") or "")
        if not raw_name or Path(raw_name).name != raw_name:
            return None
        candidate = self.engine_dir / raw_name
        if not candidate.is_file():
            return None
        expected = str(self._state.get(hash_key, "")) if hash_key else ""
        if expected and self._sha256(candidate) != expected:
            return None
        try:
            with zipfile.ZipFile(candidate) as archive:
                archive.getinfo("yt_dlp/version.py")
        except (KeyError, OSError, zipfile.BadZipFile):
            return None
        return candidate

    def _activate_state_engine(self, engine_path: Path):
        digest = self._sha256(engine_path)
        self._state.update({
            "engine_file": engine_path.name,
            "engine_sha256": digest,
        })

    @classmethod
    def _activate_engine(cls, engine_path: Path):
        engine_text = str(engine_path.resolve())
        cls._unload_engine_modules()
        sys.path[:] = [
            item for item in sys.path if str(item) not in cls._engine_paths
        ]
        cls._engine_paths.add(engine_text)
        sys.path.insert(0, engine_text)
        sys.meta_path.insert(0, _YtDlpEngineFinder(engine_path))
        importlib.invalidate_caches()
        try:
            module = importlib.import_module("yt_dlp")
            importlib.import_module("yt_dlp.version")
            return module
        except Exception:
            cls._unload_engine_modules()
            sys.path[:] = [
                item for item in sys.path if str(item) != engine_text
            ]
            raise

    @classmethod
    def _remove_engine_paths(cls):
        cls._unload_engine_modules()
        sys.path[:] = [
            item for item in sys.path if str(item) not in cls._engine_paths
        ]
        importlib.invalidate_caches()

    @staticmethod
    def _unload_engine_modules():
        sys.meta_path[:] = [
            finder
            for finder in sys.meta_path
            if not isinstance(finder, _YtDlpEngineFinder)
            and not finder.__class__.__module__.startswith("yt_dlp")
        ]
        for name in list(sys.modules):
            if name == "yt_dlp" or name.startswith("yt_dlp."):
                sys.modules.pop(name, None)

    def _install_bundled_deno(self):
        root = self._get_bundled_root()
        if root is None:
            return
        source = root / "deno.exe"
        if not source.is_file():
            return
        expected = self._read_hash_file(root / "deno.exe.sha256")
        if expected and self._sha256(source) != expected:
            return

        temporary = self.engine_dir / f".deno.{os.getpid()}.tmp.exe"
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, self.deno_path)
            if self._deno_works(self.deno_path):
                self._state["last_deno_check"] = self._clock()
                self._write_state()
        except OSError:
            pass
        finally:
            temporary.unlink(missing_ok=True)

    def _upgrade_deno(self):
        self._status("YouTube uyumluluk bileşeni güncelleniyor...", "info")
        environment = os.environ.copy()
        environment["DENO_DIR"] = str(self.cache_dir / "deno")
        creation_flags = 0
        if os.name == "nt":
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            subprocess.run(
                [str(self.deno_path), "upgrade", "--quiet"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=180,
                check=False,
                env=environment,
                creationflags=creation_flags,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    @staticmethod
    def _deno_works(path: Path) -> bool:
        if not path.is_file():
            return False
        creation_flags = 0
        if os.name == "nt":
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                [str(path), "--version"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
                creationflags=creation_flags,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and result.stdout.startswith(b"deno ")

    def _cleanup_old_engines(self, active: Path):
        keep = {active.name}
        previous = self._previous_engine_path()
        if previous:
            keep.add(previous.name)
        for candidate in self.engine_dir.glob("yt-dlp-*.pyz"):
            if candidate.name not in keep:
                candidate.unlink(missing_ok=True)

    def _get_bundled_root(self) -> Path | None:
        if self._bundled_root:
            return self._bundled_root
        bundled = getattr(sys, "_MEIPASS", None)
        return Path(bundled) if bundled else None

    def _download(self, url: str, maximum_size: int) -> bytes:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": self.USER_AGENT,
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            content_length = int(response.headers.get("Content-Length", 0) or 0)
            if content_length > maximum_size:
                raise EngineUpdateError("İndirme motoru paketi beklenenden büyük.")
            data = response.read(maximum_size + 1)
        if len(data) > maximum_size:
            raise EngineUpdateError("İndirme motoru paketi beklenenden büyük.")
        return data

    @staticmethod
    def _checksum_for(contents: str) -> str:
        for line in contents.splitlines():
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            filename = parts[-1].lstrip("*")
            if filename == "yt-dlp" and re.fullmatch(r"[a-fA-F0-9]{64}", parts[0]):
                return parts[0].lower()
        raise EngineUpdateError("Resmi yt-dlp checksum kaydı bulunamadı.")

    @staticmethod
    def _read_hash_file(path: Path) -> str | None:
        try:
            contents = path.read_text(encoding="ascii")
        except OSError:
            return None
        match = re.search(r"[a-fA-F0-9]{64}", contents)
        return match.group(0).lower() if match else None

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _read_state(self) -> dict:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, AttributeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _write_state(self):
        self.engine_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.engine_dir / f".state.{os.getpid()}.tmp"
        try:
            temporary.write_text(
                json.dumps(self._state, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary, self.state_path)
        finally:
            temporary.unlink(missing_ok=True)

    def _status(self, message: str, level: str):
        if self.on_status:
            self.on_status(message, level)
