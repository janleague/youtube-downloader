"""README ve release sayfası için uygulama ekran görüntülerini üretir."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import QSettings  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from main import MainWindow  # noqa: E402
from theme import app_qss, load_fonts, set_theme  # noqa: E402


OUTPUT = ROOT / "docs" / "images"


def capture(app: QApplication, filename: str, page: str, dark: bool) -> None:
    settings = QSettings("janleague", "YouTubeDownloader")
    settings.setValue("dark_theme", dark)
    settings.sync()

    set_theme(dark)
    app.setStyleSheet(app_qss())
    window = MainWindow()
    window.sidebar.select(page)
    if page == "library":
        thumbnail = str(ROOT / "app_icon.png")
        window.page_library.populate(
            [
                {
                    "title": "Premium UI Design Process",
                    "format": "MP4",
                    "size": "84.2 MB",
                    "quality": "1080p",
                    "path": "",
                    "thumbnail": thumbnail,
                },
                {
                    "title": "Focus Music Mix",
                    "format": "MP3",
                    "size": "12.8 MB",
                    "quality": "320 kbps",
                    "path": "",
                    "thumbnail": thumbnail,
                },
            ]
        )
    window.show()
    app.processEvents()
    app.processEvents()

    target = OUTPUT / filename
    if not window.grab().save(str(target), "PNG"):
        raise RuntimeError(f"Ekran görüntüsü kaydedilemedi: {target}")
    window.close()
    window.deleteLater()
    app.processEvents()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName("janleague")
    app.setApplicationName("YouTubeDownloader")
    load_fonts()

    settings = QSettings("janleague", "YouTubeDownloader")
    original_theme = settings.value("dark_theme", True)
    try:
        capture(app, "dark-download.png", "download", True)
        capture(app, "dark-library.png", "library", True)
        capture(app, "dark-settings.png", "settings", True)
        capture(app, "dark-about.png", "about", True)
        capture(app, "light-download.png", "download", False)
        capture(app, "light-about.png", "about", False)
    finally:
        settings.setValue("dark_theme", original_theme)
        settings.sync()

    print(f"Captured screenshots in {OUTPUT}")


if __name__ == "__main__":
    main()
