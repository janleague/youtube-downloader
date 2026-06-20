"""DownloadManager'ı Qt iş parçacığında çalıştıran köprü."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from core.download_manager import DownloadManager


class DownloadWorker(QThread):
    progress = pyqtSignal(float, str, str)
    status = pyqtSignal(str, str)
    complete = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(
        self,
        downloads_dir: Path,
        audio_quality: str,
        url: str,
        fmt: str,
        resolution: str | None,
        parent=None,
    ):
        super().__init__(parent)
        self.downloads_dir = Path(downloads_dir)
        self.audio_quality = audio_quality
        self.url = url
        self.fmt = fmt
        self.resolution = resolution

    def run(self):
        manager = DownloadManager(
            self.downloads_dir,
            self.audio_quality,
            self.progress.emit,
            self.status.emit,
            self.complete.emit,
            self.error.emit,
        )
        manager.download(self.url, self.fmt, self.resolution)


class DownloadController(QObject):
    progress = pyqtSignal(float, str, str)
    status = pyqtSignal(str, str)
    complete = pyqtSignal(str, str)
    error = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)

    def __init__(self, downloads_dir: Path, audio_quality="320", parent=None):
        super().__init__(parent)
        self.downloads_dir = Path(downloads_dir)
        self.audio_quality = str(audio_quality)
        self._worker: DownloadWorker | None = None

    @property
    def busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def set_downloads_dir(self, path: Path):
        self.downloads_dir = Path(path)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def set_audio_quality(self, quality: str):
        self.audio_quality = str(quality)

    def start(self, url: str, fmt: str, resolution: str | None) -> bool:
        if self.busy:
            return False
        self._worker = DownloadWorker(
            self.downloads_dir,
            self.audio_quality,
            url,
            fmt,
            resolution,
            self,
        )
        self._worker.progress.connect(self.progress)
        self._worker.status.connect(self.status)
        self._worker.complete.connect(self.complete)
        self._worker.error.connect(self.error)
        self._worker.finished.connect(self._finished)
        self.busy_changed.emit(True)
        self._worker.start()
        return True

    def _finished(self):
        worker = self._worker
        self._worker = None
        if worker:
            worker.deleteLater()
        self.busy_changed.emit(False)
