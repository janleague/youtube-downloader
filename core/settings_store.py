"""AppData altında tutulan, GUI'den bağımsız kalıcı tercih deposu."""

from __future__ import annotations

import configparser
import os
from pathlib import Path


ORGANIZATION = "janleague"
APPLICATION = "YouTubeDownloader"


def default_data_root() -> Path:
    local_data = os.environ.get("LOCALAPPDATA")
    if local_data:
        return Path(local_data) / ORGANIZATION / APPLICATION
    return Path.home() / "AppData" / "Local" / ORGANIZATION / APPLICATION


class SettingsStore:
    DEFAULTS = {
        "default_format": "MP3",
        "resolution": "1080p",
        "audio_quality": "320",
        "language": "tr",
        "notifications": "true",
        "dark_theme": "true",
    }

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
        self._config = configparser.ConfigParser()
        self._config.read(self.settings_path, encoding="utf-8")
        if not self._config.has_section("General"):
            self._config.add_section("General")
        if migrate_legacy:
            self._migrate_legacy_registry()

    def _migrate_legacy_registry(self):
        section = self._config["General"]
        if section.get("_storage_version"):
            return
        if os.name == "nt" and not list(section.keys()):
            try:
                import winreg

                key_path = rf"Software\{ORGANIZATION}\{APPLICATION}"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    index = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, index)
                        except OSError:
                            break
                        if name != "downloads_dir" or not self._is_legacy_default(value):
                            section[name] = str(value)
                        index += 1
            except OSError:
                pass
        section["_storage_version"] = "3"
        self._sync()

    @staticmethod
    def _is_legacy_default(value) -> bool:
        if not value:
            return False
        try:
            return Path(str(value)).resolve() == (
                Path.home() / "Downloads" / "YouTube Downloader"
            ).resolve()
        except OSError:
            return False

    def value(self, key: str, default=None):
        fallback = self.DEFAULTS.get(key, default)
        return self._config["General"].get(key, fallback)

    def set(self, key: str, value):
        if isinstance(value, bool):
            text = "true" if value else "false"
        else:
            text = str(value)
        self._config["General"][key] = text
        self._sync()

    def _sync(self):
        with self.settings_path.open("w", encoding="utf-8") as handle:
            self._config.write(handle)

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
