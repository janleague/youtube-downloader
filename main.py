"""YouTube İndirici — premium PyQt6 arayüzü ve yt-dlp backend."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QAction, QColor, QIcon, QPainter, QPainterPath, QPen,
    QRadialGradient, QRegion, QBrush,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QMenu, QMessageBox,
    QScrollArea, QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from core.download_controller import DownloadController
from core.download_manager import DownloadManager
from core.library_service import scan_library
from core.settings_store import SettingsStore
from pages.about_page import AboutPage
from pages.download_page import DownloadPage
from pages.library_page import LibraryPage
from pages.settings_page import SettingsPage
from theme import COLORS, FONTS, app_qss, load_fonts, set_theme
from widgets.sidebar import Sidebar
from widgets.title_bar import TitleBar
from i18n import set_language, tr


APP_W, APP_H = 1040, 680
RADIUS = 14


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


class ContentArea(QWidget):
    """Ana içeriğin HTML mockup'taki hafif kırmızı ortam ışığı."""

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(COLORS["bg_app"]))
        gradient = QRadialGradient(self.width() * 0.78, -70, 900)
        gradient.setColorAt(0.0, QColor(255, 34, 51, 17))
        gradient.setColorAt(1.0, QColor(255, 34, 51, 0))
        painter.fillRect(self.rect(), QBrush(gradient))


class MainWindow(QWidget):
    PAGE_INDEX = {"download": 0, "library": 1, "settings": 2, "about": 3}

    def __init__(self):
        super().__init__()
        self.app_dir = application_dir()
        self.store = SettingsStore(self.app_dir)
        set_language(self.store.language)
        self.downloads_dir = self.store.downloads_dir
        try:
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.downloads_dir = self.app_dir / "Downloads"
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
            self.store.set("downloads_dir", str(self.downloads_dir))

        self.ffmpeg_ok = DownloadManager.check_ffmpeg()
        self.controller = DownloadController(
            self.downloads_dir, self.store.audio_quality, self,
        )
        self._tray: QSystemTrayIcon | None = None

        self.setWindowTitle(tr("app.name"))
        icon_path = resource_dir() / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(APP_W, APP_H)
        self.setMinimumSize(900, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._build_ui()
        self._wire()
        self._setup_tray(icon_path)
        self.refresh_library()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar()
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_max)
        self.title_bar.close_clicked.connect(self.close)
        root.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar(self.ffmpeg_ok)
        self.sidebar.page_changed.connect(self._goto)
        body.addWidget(self.sidebar)

        self.content = ContentArea()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        self.page_download = DownloadPage()
        self.page_download.set_default_format(self.store.default_format)
        self.page_download.set_default_resolution(self.store.resolution)
        self.page_library = LibraryPage()
        self.page_settings = SettingsPage(
            downloads_path=self._short_path(self.downloads_dir),
            default_format=self.store.default_format,
            audio_quality=self.store.audio_quality,
            language=self.store.language,
            notifications=self.store.notifications,
            dark_theme=self.store.dark_theme,
        )
        self.page_about = AboutPage(self.ffmpeg_ok)
        for page in (
            self.page_download,
            self.page_library,
            self.page_settings,
            self.page_about,
        ):
            self.stack.addWidget(self._scroll(page))
        content_layout.addWidget(self.stack)
        body.addWidget(self.content, 1)
        root.addLayout(body)

    def _wire(self):
        self.page_download.download_requested.connect(self._start_download)
        self.page_download.paste_requested.connect(self._paste)

        self.controller.progress.connect(self.page_download.set_progress)
        self.controller.status.connect(self.page_download.set_status)
        self.controller.complete.connect(self._download_complete)
        self.controller.error.connect(self._download_error)

        self.page_library.file_open_requested.connect(self._open_path)

        self.page_settings.folder_change_requested.connect(self._choose_folder)
        self.page_settings.default_format_changed.connect(self._set_default_format)
        self.page_settings.quality_change_requested.connect(self._choose_quality)
        self.page_settings.language_change_requested.connect(self._choose_language)
        self.page_settings.notifications_toggled.connect(
            lambda enabled: self.store.set("notifications", enabled)
        )
        self.page_settings.dark_theme_toggled.connect(self._dark_theme_toggled)

    def _scroll(self, widget: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.viewport().setAutoFillBackground(False)
        area.viewport().setStyleSheet("background: transparent;")
        area.setWidget(widget)
        return area

    def _goto(self, key: str):
        self.stack.setCurrentIndex(self.PAGE_INDEX[key])
        if key == "library":
            self.refresh_library()

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _start_download(self, url: str, fmt: str, resolution: str | None):
        if not url:
            self.page_download.set_status("Bir YouTube bağlantısı girin.", "warning")
            return
        if not DownloadManager.is_valid_url(url):
            self.page_download.set_status(
                "Geçerli bir YouTube bağlantısı girin.", "warning",
            )
            return
        if fmt == "mp3" and not self.ffmpeg_ok:
            self.page_download.set_error(
                "MP3 dönüşümü için ffmpeg gerekli. "
                "PowerShell: winget install ffmpeg"
            )
            return
        if not self.controller.start(url, fmt, resolution):
            self.page_download.set_status("Bir indirme zaten devam ediyor.", "warning")
            return
        self.page_download.reset_progress()
        self.page_download.set_busy(True)
        self.page_download.set_status("Video bilgileri alınıyor...", "info")

    def _paste(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.page_download.set_url(text)
            self.page_download.set_status("Bağlantı panodan yapıştırıldı.", "info")
        else:
            self.page_download.set_status("Panoda metin bulunamadı.", "warning")

    def _download_complete(self, filepath: str, title: str):
        self.page_download.set_complete(title)
        self.refresh_library()
        if self.store.notifications and self._tray:
            self._tray.showMessage(
                "İndirme tamamlandı",
                title,
                QSystemTrayIcon.MessageIcon.Information,
                4500,
            )

    def _download_error(self, message: str):
        self.page_download.set_error(message)
        if self.store.notifications and self._tray:
            self._tray.showMessage(
                "İndirme başarısız",
                message.splitlines()[0],
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )

    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "İndirme klasörünü seç", str(self.downloads_dir),
        )
        if not path:
            return
        self.downloads_dir = Path(path)
        self.controller.set_downloads_dir(self.downloads_dir)
        self.store.set("downloads_dir", str(self.downloads_dir))
        self.page_settings.set_downloads_path(str(self.downloads_dir))
        self.refresh_library()

    def _set_default_format(self, fmt: str):
        fmt = fmt.upper()
        self.store.set("default_format", fmt)
        self.page_download.set_default_format(fmt)

    def _choose_quality(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_qss())
        for quality in ("320", "256", "192", "128"):
            action = QAction(f"{quality} kbps", menu)
            action.setCheckable(True)
            action.setChecked(self.store.audio_quality == quality)
            action.triggered.connect(
                lambda _checked=False, q=quality: self._set_quality(q)
            )
            menu.addAction(action)
        menu.exec(self.page_settings.quality_btn.mapToGlobal(
            self.page_settings.quality_btn.rect().bottomLeft()
        ))

    def _set_quality(self, quality: str):
        self.store.set("audio_quality", quality)
        self.controller.set_audio_quality(quality)
        self.page_settings.set_audio_quality(quality)

    def _choose_language(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_qss())
        choices = (("tr", "Türkçe"), ("en", "English"))
        for code, label in choices:
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(self.store.language == code)
            action.triggered.connect(
                lambda _checked=False, c=code: self._set_language(c)
            )
            menu.addAction(action)
        menu.exec(self.page_settings.language_btn.mapToGlobal(
            self.page_settings.language_btn.rect().bottomLeft()
        ))

    def _set_language(self, language: str):
        self.store.set("language", language)
        set_language(language)
        self._recreate_window()

    def _recreate_window(self):
        position = self.pos()
        maximized = self.isMaximized()
        replacement = MainWindow()
        replacement.move(position)
        if maximized:
            replacement.showMaximized()
        else:
            replacement.show()
        QApplication.instance()._main_window = replacement
        self._tray = None
        self.close()

    def _dark_theme_toggled(self, enabled: bool):
        self.store.set("dark_theme", enabled)
        set_theme(enabled)
        QApplication.instance().setStyleSheet(app_qss())
        self._recreate_window()

    def refresh_library(self):
        self.page_library.populate(scan_library(self.downloads_dir))

    def _open_path(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except OSError as exc:
            self.page_download.set_status(f"Dosya açılamadı: {exc}", "error")

    def _setup_tray(self, icon_path: Path):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.windowIcon()
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip(tr("app.name"))
        self._tray.show()

    @staticmethod
    def _short_path(path: Path) -> str:
        text = str(path)
        return text if len(text) <= 48 else "…" + text[-47:]

    @staticmethod
    def _menu_qss() -> str:
        return f"""
        QMenu {{
            background: {COLORS['elev']};
            color: {COLORS['text2']};
            border: 1px solid {COLORS['border2']};
            padding: 6px;
        }}
        QMenu::item {{ padding: 8px 24px 8px 10px; border-radius: 6px; }}
        QMenu::item:selected {{ background: rgba(255,34,51,0.16); color: white; }}
        QMenu::indicator {{ width: 12px; height: 12px; }}
        """

    def resizeEvent(self, event):
        path = QPainterPath()
        radius = 0 if self.isMaximized() else RADIUS
        path.addRoundedRect(
            QRectF(0, 0, self.width(), self.height()), radius, radius,
        )
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        super().resizeEvent(event)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 0 if self.isMaximized() else RADIUS
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QColor(COLORS["bg_app"]))
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawPath(path)

    def closeEvent(self, event):
        if self.controller.busy:
            answer = QMessageBox.question(
                self,
                "İndirme devam ediyor",
                "İndirme devam ederken uygulamayı kapatmak istiyor musun?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube İndirici")
    app.setOrganizationName("janleague")
    load_fonts()
    startup_store = SettingsStore(application_dir())
    set_theme(startup_store.dark_theme)
    app.setStyleSheet(app_qss())
    window = MainWindow()
    app._main_window = window
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
