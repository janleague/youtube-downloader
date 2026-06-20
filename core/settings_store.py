"""QSettings tabanlı kalıcı uygulama tercihleri."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings, QStandardPaths


class SettingsStore:
    def __init__(self, app_dir: Path):
        self._settings = QSettings("janleague", "YouTubeDownloader")
        downloads_root = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not downloads_root:
            downloads_root = str(Path.home() / "Downloads")
        self.default_downloads = Path(downloads_root) / "YouTube Downloader"

    def value(self, key: str, default=None):
        return self._settings.value(key, default)

    def set(self, key: str, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    @property
    def downloads_dir(self) -> Path:
        return Path(self.value("downloads_dir", str(self.default_downloads)))

    @property
    def default_format(self) -> str:
        return str(self.value("default_format", "MP3"))

    @property
    def resolution(self) -> str:
        return str(self.value("resolution", "1080p"))

    @property
    def audio_quality(self) -> str:
        return str(self.value("audio_quality", "320"))

    @property
    def language(self) -> str:
        return str(self.value("language", "tr"))

    @property
    def notifications(self) -> bool:
        return self._bool("notifications", True)

    @property
    def dark_theme(self) -> bool:
        return self._bool("dark_theme", True)

    def _bool(self, key: str, default: bool) -> bool:
        value = self.value(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}
