"""Uygulama verilerini AppData altında tutan kalıcı tercih deposu."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings, QStandardPaths


ORGANIZATION = "janleague"
APPLICATION = "YouTubeDownloader"


def default_data_root() -> Path:
    """Ayarlar, metadata ve varsayılan indirmeler için yazılabilir ana klasör."""
    local_data = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericDataLocation
    )
    if local_data:
        return Path(local_data) / ORGANIZATION / APPLICATION
    return Path.home() / "AppData" / "Local" / ORGANIZATION / APPLICATION


class SettingsStore:
    def __init__(
        self,
        app_dir: Path | None = None,
        data_root: Path | None = None,
        migrate_legacy: bool = True,
    ):
        self.app_dir = Path(app_dir) if app_dir else Path.cwd()
        self.data_root = Path(data_root) if data_root else default_data_root()
        self.data_root.mkdir(parents=True, exist_ok=True)

        self.settings_path = self.data_root / "settings.ini"
        self.default_downloads = self.data_root / "Downloads"
        self.default_downloads.mkdir(parents=True, exist_ok=True)

        self._settings = QSettings(
            str(self.settings_path),
            QSettings.Format.IniFormat,
        )
        if migrate_legacy:
            self._migrate_native_settings()

    def _migrate_native_settings(self):
        """Eski Registry ayarlarını ilk açılışta yeni INI dosyasına taşır."""
        if self._settings.value("_storage_version"):
            return

        legacy = QSettings(ORGANIZATION, APPLICATION)
        if not self._settings.allKeys():
            for key in legacy.allKeys():
                value = legacy.value(key)
                if key == "downloads_dir" and self._is_legacy_default(value):
                    continue
                self._settings.setValue(key, value)
        self._settings.setValue("_storage_version", 2)
        self._settings.sync()

    @staticmethod
    def _is_legacy_default(value) -> bool:
        if not value:
            return False
        downloads_root = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not downloads_root:
            downloads_root = str(Path.home() / "Downloads")
        try:
            return Path(str(value)).resolve() == (
                Path(downloads_root) / "YouTube Downloader"
            ).resolve()
        except OSError:
            return False

    def value(self, key: str, default=None):
        return self._settings.value(key, default)

    def set(self, key: str, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    @property
    def downloads_dir(self) -> Path:
        stored = str(self.value("downloads_dir", "") or "").strip()
        return Path(stored) if stored else self.default_downloads

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
