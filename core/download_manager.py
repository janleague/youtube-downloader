"""yt-dlp tabanlı, GUI'den bağımsız indirme motoru."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Callable

import yt_dlp


ProgressCallback = Callable[[float, str, str], None]
StatusCallback = Callable[[str, str], None]
CompleteCallback = Callable[[str, str], None]
ErrorCallback = Callable[[str], None]


class DownloadManager:
    RESOLUTIONS = [
        "2160p", "1440p", "1080p", "720p", "480p", "360p", "En İyi",
    ]

    _ERROR_MAP = [
        ("Private video", "Bu video özel. Erişim izniniz yok."),
        ("Video unavailable", "Video mevcut değil veya kaldırılmış."),
        ("This video is not available", "Video bölgenizde kullanılamıyor."),
        ("members-only", "Bu video yalnızca kanal üyeleri için."),
        ("This live event will begin", "Canlı yayın henüz başlamadı."),
        ("is not a valid URL", "Geçersiz YouTube bağlantısı."),
        ("Unsupported URL", "Bu bağlantı desteklenmiyor."),
        ("Sign in", "Bu içerik için YouTube hesabına giriş gerekiyor."),
        ("age", "Bu video yaş kısıtlamalı."),
        ("copyright", "Video telif kısıtlaması nedeniyle indirilemiyor."),
        ("DRM", "Video DRM korumalı ve indirilemiyor."),
        ("ffmpeg", "ffmpeg bulunamadı veya çalıştırılamadı."),
        ("No space left", "Disk alanı yetersiz."),
        ("Permission denied", "İndirme klasörüne yazma izni yok."),
        ("Unable to download webpage", "YouTube'a bağlanılamadı."),
        ("Failed to establish a new connection", "İnternet bağlantısı kurulamadı."),
        ("HTTP Error 429", "Çok fazla istek gönderildi. Birkaç dakika bekleyin."),
        ("HTTP Error 403", "YouTube erişimi reddetti (403)."),
        ("HTTP Error 404", "Video bulunamadı (404)."),
        ("HTTP Error 500", "YouTube sunucu hatası verdi (500)."),
        ("This video has been removed", "Video YouTube'dan kaldırılmış."),
        ("Requested format is not available", "Seçilen kalite bu videoda bulunmuyor."),
    ]

    def __init__(
        self,
        downloads_dir: Path,
        audio_quality: str = "320",
        on_progress: ProgressCallback | None = None,
        on_status: StatusCallback | None = None,
        on_complete: CompleteCallback | None = None,
        on_error: ErrorCallback | None = None,
    ):
        self.downloads_dir = Path(downloads_dir)
        self.audio_quality = str(audio_quality)
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_complete = on_complete
        self.on_error = on_error
        self.set_downloads_dir(self.downloads_dir)

    def set_downloads_dir(self, path: Path):
        path = Path(path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = path

    @staticmethod
    def check_ffmpeg() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def is_valid_url(url: str) -> bool:
        pattern = re.compile(
            r"^https?://(?:www\.)?"
            r"(?:youtube\.com/(?:watch\?.*v=|shorts/|playlist\?.*list=)|youtu\.be/)"
            r"[\w-]+",
            re.IGNORECASE,
        )
        return bool(pattern.search(url.strip()))

    def _progress_hook(self, data: dict):
        status = data.get("status")
        if status == "downloading":
            downloaded = data.get("downloaded_bytes") or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            percent = downloaded / total * 100 if total else 0.0
            raw_speed = data.get("speed") or 0
            if raw_speed >= 1_048_576:
                speed = f"{raw_speed / 1_048_576:.1f} MB/s"
            elif raw_speed >= 1024:
                speed = f"{raw_speed / 1024:.0f} KB/s"
            else:
                speed = "— KB/s"

            raw_eta = int(data.get("eta") or 0)
            if raw_eta >= 3600:
                eta = f"{raw_eta // 3600} sa {(raw_eta % 3600) // 60} dk"
            elif raw_eta >= 60:
                eta = f"{raw_eta // 60} dk {raw_eta % 60} sn"
            elif raw_eta:
                eta = f"{raw_eta} sn kaldı"
            else:
                eta = "hesaplanıyor..."
            if self.on_progress:
                self.on_progress(percent, speed, eta)
        elif status == "finished":
            if self.on_progress:
                self.on_progress(99.0, "", "dönüştürülüyor...")
            if self.on_status:
                self.on_status("Dönüştürme ve metadata işlemleri yapılıyor...", "info")

    def _resolve_error(self, raw: str) -> str:
        for keyword, friendly in self._ERROR_MAP:
            if keyword.lower() in raw.lower():
                return friendly
        clean = re.sub(r"ERROR:\s*(?:\[.*?\])?", "", raw).strip()
        return clean[:300] or "Bilinmeyen bir indirme hatası oluştu."

    def download(self, url: str, fmt: str, resolution: str | None = None):
        if not self.is_valid_url(url):
            if self.on_error:
                self.on_error("Geçerli bir YouTube bağlantısı girin.")
            return
        if fmt.lower() == "mp3":
            self.download_mp3(url)
        else:
            self.download_mp4(url, resolution or "1080p")

    def download_mp3(self, url: str):
        if not self.check_ffmpeg():
            if self.on_error:
                self.on_error(
                    "MP3 dönüşümü için ffmpeg gerekli.\n"
                    "Windows: winget install ffmpeg"
                )
            return
        options = self._common_options()
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.audio_quality,
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
            ],
        })
        self._execute(url, options, "mp3")

    def download_mp4(self, url: str, resolution: str):
        if resolution == "En İyi":
            selector = "bestvideo+bestaudio/best"
        else:
            height = re.sub(r"\D", "", resolution) or "1080"
            selector = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}][ext=mp4]"
                f"/best[height<={height}]/best"
            )
        options = self._common_options()
        options.update({
            "format": selector,
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata", "add_metadata": True}],
        })
        self._execute(url, options, "mp4")

    def _common_options(self) -> dict:
        return {
            "outtmpl": str(self.downloads_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "writeinfojson": True,
            "writethumbnail": True,
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "windowsfilenames": True,
        }

    def _execute(self, url: str, options: dict, output_ext: str):
        try:
            if self.on_status:
                self.on_status("Video bilgileri alınıyor...", "info")
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise RuntimeError("Video bilgisi alınamadı.")
                title = info.get("title") or "video"

            matches = sorted(
                self.downloads_dir.glob(f"*.{output_ext}"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            filepath = str(matches[0]) if matches else str(
                self.downloads_dir / f"{title}.{output_ext}"
            )
            if self.on_complete:
                self.on_complete(filepath, title)
        except yt_dlp.utils.DownloadError as exc:
            self._emit_error(self._resolve_error(str(exc)))
        except yt_dlp.utils.PostProcessingError as exc:
            self._emit_error("ffmpeg işlemi başarısız: " + self._resolve_error(str(exc)))
        except PermissionError:
            self._emit_error("İndirme klasörüne yazma izni yok.")
        except OSError as exc:
            self._emit_error(self._resolve_error(str(exc)))
        except Exception as exc:  # Son güvenlik ağı: GUI çökmemeli.
            self._emit_error(self._resolve_error(str(exc)))

    def _emit_error(self, message: str):
        if self.on_error:
            self.on_error(message)
