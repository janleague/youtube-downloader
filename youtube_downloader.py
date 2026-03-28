"""
╔══════════════════════════════════════════════════════════╗
║          YouTube Downloader — by janleague               ║
║          github.com/janleague                            ║
╚══════════════════════════════════════════════════════════╝

Modern, karanlık temalı YouTube MP3 / MP4 indirici.
CustomTkinter + yt-dlp ile geliştirilmiştir.

Kurulum:
    pip install customtkinter yt-dlp

ffmpeg Kurulumu (gerekli):
    Windows  → winget install ffmpeg
               veya: https://www.gyan.dev/ffmpeg/builds/
    macOS    → brew install ffmpeg
    Linux    → sudo apt install ffmpeg   (Debian/Ubuntu)
               sudo dnf install ffmpeg   (Fedora)

Kullanım:
    python youtube_downloader.py

Author : janleague
GitHub : https://github.com/janleague
License: MIT
"""

import os
import sys
import threading
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Bağımlılık kontrolleri — eksik paketleri otomatik kur
# ─────────────────────────────────────────────────────────────
try:
    import customtkinter as ctk
except ImportError:
    print("[janleague/yt-dl] CustomTkinter bulunamadı, kuruluyor...")
    os.system(f'"{sys.executable}" -m pip install customtkinter --quiet')
    import customtkinter as ctk

try:
    import yt_dlp
except ImportError:
    print("[janleague/yt-dl] yt-dlp bulunamadı, kuruluyor...")
    os.system(f'"{sys.executable}" -m pip install yt-dlp --quiet')
    import yt_dlp


# ════════════════════════════════════════════════════════════════
# LOGIC KATMANI
# GUI'den tamamen bağımsız. Tüm indirme mantığı burada.
# ════════════════════════════════════════════════════════════════

class DownloadManager:
    """
    İndirme işlemlerini yöneten sınıf.

    GUI'ye tamamen kör çalışır; iletişim yalnızca
    4 adet callback fonksiyonu üzerinden kurulur:
        on_progress(percent, speed, eta)
        on_status(message, level)
        on_complete(filepath, title)
        on_error(message)
    """

    RESOLUTIONS = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p", "En İyi"]

    # Hata mesajlarını kullanıcı dostu Türkçeye çeviren anahtar eşlemesi
    _ERROR_MAP = [
        ("Private video",                         "Bu video özel (private). Erişim izniniz yok."),
        ("Video unavailable",                     "Video mevcut değil veya kaldırılmış."),
        ("This video is not available",           "Bu video bölgenizde mevcut değil (geo-kısıtlı)."),
        ("members-only",                          "Bu video yalnızca kanal üyeleri için. Üyelik gerekli."),
        ("This live event will begin",            "Canlı yayın henüz başlamadı. Daha sonra tekrar deneyin."),
        ("is not a valid URL",                    "Geçersiz URL. Lütfen doğru bir YouTube bağlantısı girin."),
        ("Unsupported URL",                       "Bu URL desteklenmiyor. Yalnızca YouTube bağlantıları kabul edilir."),
        ("Sign in",                               "Bu içerik için YouTube hesabınıza giriş yapılması gerekiyor."),
        ("age",                                   "Bu video yaş kısıtlamalı; YouTube oturumu açılmalı."),
        ("copyright",                             "Bu video telif hakkı nedeniyle indirilemez."),
        ("DRM",                                   "Bu video DRM korumalı, indirilemez."),
        ("ffmpeg",                                "ffmpeg bulunamadı!\n→ Windows: winget install ffmpeg\n→ macOS: brew install ffmpeg\n→ Linux: sudo apt install ffmpeg"),
        ("No space left",                         "Disk alanı yetersiz! Lütfen yer açın."),
        ("Permission denied",                     "İzin hatası: İndirmeler klasörüne yazma izniniz yok."),
        ("Unable to download webpage",            "Ağ bağlantısı kurulamadı. İnternet bağlantınızı kontrol edin."),
        ("Failed to establish a new connection",  "İnternet bağlantısı yok veya YouTube'a erişilemiyor."),
        ("HTTP Error 429",                        "Çok fazla istek gönderildi (429). Birkaç dakika bekleyip tekrar deneyin."),
        ("HTTP Error 403",                        "Erişim reddedildi (403). Video yalnızca yetkili kullanıcılara açık olabilir."),
        ("HTTP Error 404",                        "Video bulunamadı (404). URL'yi kontrol edin."),
        ("HTTP Error 500",                        "YouTube sunucu hatası (500). Daha sonra tekrar deneyin."),
        ("This video has been removed",           "Video kaldırılmış. YouTube'da artık mevcut değil."),
        ("Requested format is not available",     "İstenen çözünürlük bu video için mevcut değil. Farklı bir çözünürlük deneyin."),
    ]

    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

        # Klasörü oluştur; hata olursa kullanıcıya bildir
        try:
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise RuntimeError(
                f"İndirmeler klasörü oluşturulamadı: {self.downloads_dir}\n"
                "Lütfen yazma izninizi kontrol edin."
            )

        # Callback'ler — GUI tarafından atanır
        self.on_progress: Optional[callable] = None
        self.on_status:   Optional[callable] = None
        self.on_complete: Optional[callable] = None
        self.on_error:    Optional[callable] = None

    # ── ffmpeg Varlık Kontrolü ────────────────────────────────
    @staticmethod
    def check_ffmpeg() -> bool:
        """ffmpeg'in PATH'te bulunup bulunmadığını kontrol eder."""
        return shutil.which("ffmpeg") is not None

    # ── URL Doğrulama ─────────────────────────────────────────
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        YouTube URL formatını doğrular.
        Desteklenen formatlar: watch, shorts, youtu.be, playlist
        """
        url = url.strip()
        if not url:
            return False
        pattern = re.compile(
            r"(https?://)?(www\.)?"
            r"(youtube\.com/(watch\?.*v=|shorts/|playlist\?.*list=)|youtu\.be/)"
            r"[\w\-]+"
        )
        return bool(pattern.search(url))

    # ── İlerleme Hook'u ───────────────────────────────────────
    def _progress_hook(self, d: dict):
        """
        yt-dlp'nin her chunk indirmesinde çağırdığı hook.
        İlerleme verisini hesaplar ve on_progress callback'ine iletir.
        """
        status = d.get("status", "")

        if status == "downloading":
            try:
                downloaded = d.get("downloaded_bytes") or 0
                total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                percent    = (downloaded / total * 100) if total > 0 else 0

                # Hız (bytes/s → okunabilir format)
                raw_speed = d.get("speed") or 0
                if raw_speed >= 1_048_576:
                    speed = f"{raw_speed / 1_048_576:.1f} MB/s"
                elif raw_speed >= 1_024:
                    speed = f"{raw_speed / 1_024:.0f} KB/s"
                else:
                    speed = "— KB/s"

                # Kalan süre (saniye → okunabilir format)
                raw_eta = d.get("eta") or 0
                if raw_eta >= 3600:
                    eta = f"{raw_eta // 3600}s {(raw_eta % 3600) // 60}d kaldı"
                elif raw_eta >= 60:
                    eta = f"{raw_eta // 60}d {raw_eta % 60}s kaldı"
                elif raw_eta > 0:
                    eta = f"{raw_eta}s kaldı"
                else:
                    eta = "hesaplanıyor..."

                if self.on_progress:
                    self.on_progress(percent, speed, eta)

            except (ZeroDivisionError, TypeError):
                pass  # İlerleme verisi eksik/bozuk — sessizce atla

        elif status == "finished":
            # Dosya indirildi; şimdi ffmpeg dönüşümü var (varsa)
            if self.on_progress:
                self.on_progress(99.0, "", "dönüştürülüyor...")
            if self.on_status:
                self.on_status("🔄  Dönüştürme yapılıyor (ffmpeg)...", "info")

        elif status == "error":
            # yt-dlp iç hatası — _execute_download zaten yakalayacak
            pass

    # ── Hata Mesajı Çözümleyici ───────────────────────────────
    def _resolve_error(self, raw: str) -> str:
        """
        Ham yt-dlp hata metnini kullanıcı dostu Türkçeye çevirir.
        Hiçbir kalıpla eşleşmezse ham mesajı kısal.
        """
        for keyword, friendly in self._ERROR_MAP:
            if keyword.lower() in raw.lower():
                return friendly
        # Bilinmeyen hata: temizle ve kısal
        clean = re.sub(r"ERROR: \[.*?\]", "İndirme hatası:", raw)
        return clean[:280]

    # ── MP3 İndirme ───────────────────────────────────────────
    def download_mp3(self, url: str):
        """
        En yüksek kalitede ses indirir, ffmpeg ile 320 kbps MP3'e dönüştürür.
        ID3 metadata (başlık, sanatçı) otomatik eklenir.
        """
        if not self.check_ffmpeg():
            if self.on_error:
                self.on_error(
                    "ffmpeg bulunamadı — MP3 dönüşümü için ffmpeg gereklidir.\n"
                    "→ Windows: winget install ffmpeg\n"
                    "→ macOS: brew install ffmpeg\n"
                    "→ Linux: sudo apt install ffmpeg"
                )
            return

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(self.downloads_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "postprocessors": [
                {
                    # Sesi MP3'e çevir — en yüksek kalite: 320kbps
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {
                    # Başlık / sanatçı / albüm bilgisini ekle
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
        }
        self._execute_download(url, ydl_opts, output_ext="mp3")

    # ── MP4 İndirme ───────────────────────────────────────────
    def download_mp4(self, url: str, resolution: str):
        """
        Belirtilen çözünürlükte video indirir; ses ve video ayrı stream'lerse
        ffmpeg ile birleştirir.
        'En İyi' seçilirse en yüksek mevcut kalite kullanılır.
        """
        if resolution == "En İyi":
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            h = resolution.replace("p", "")
            fmt = (
                f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={h}]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={h}]+bestaudio"
                f"/best[height<={h}][ext=mp4]"
                f"/best[height<={h}]"
                f"/best"
            )

        ydl_opts = {
            "format": fmt,
            "outtmpl": str(self.downloads_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "merge_output_format": "mp4",
            "socket_timeout": 30,
            "retries": 5,
            "fragment_retries": 5,
            "postprocessors": [
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
        }
        self._execute_download(url, ydl_opts, output_ext="mp4")

    # ── Ortak İndirme Çalıştırıcı ─────────────────────────────
    def _execute_download(self, url: str, ydl_opts: dict, output_ext: str):
        """
        yt-dlp'yi çalıştırır; tüm hata türlerini yakalar,
        kullanıcı dostu mesajlara dönüştürür ve callback'e iletir.
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Önce video meta verisini çek (indirmeden)
                info = ydl.extract_info(url, download=False)

                if info is None:
                    if self.on_error:
                        self.on_error("Video bilgisi alınamadı. URL'yi kontrol edin.")
                    return

                title = info.get("title", "video")

                # Asıl indirme
                ydl.download([url])

            # Başarı: callback'e dosya yolu ve başlığı ilet
            if self.on_complete:
                self.on_complete(
                    str(self.downloads_dir / f"{title}.{output_ext}"),
                    title,
                )

        except yt_dlp.utils.DownloadError as exc:
            if self.on_error:
                self.on_error(self._resolve_error(str(exc)))

        except yt_dlp.utils.ExtractorError as exc:
            if self.on_error:
                self.on_error(f"Video verisi okunamadı: {self._resolve_error(str(exc))}")

        except yt_dlp.utils.PostProcessingError as exc:
            if self.on_error:
                self.on_error(
                    "Post-işlem hatası (ffmpeg):\n"
                    + self._resolve_error(str(exc))
                )

        except PermissionError:
            if self.on_error:
                self.on_error(
                    f"Yazma izni yok: {self.downloads_dir}\n"
                    "Lütfen klasör izinlerini kontrol edin."
                )

        except OSError as exc:
            msg = str(exc)
            if "No space left" in msg or "28" in msg:
                friendly = "Disk alanı yetersiz! Lütfen yer açın."
            else:
                friendly = f"Dosya sistemi hatası: {msg[:200]}"
            if self.on_error:
                self.on_error(friendly)

        except KeyboardInterrupt:
            if self.on_error:
                self.on_error("İndirme iptal edildi.")

        except Exception as exc:
            # Beklenmeyen her hatayı yakala — uygulamanın çökmesini engelle
            if self.on_error:
                self.on_error(f"Beklenmeyen hata: {type(exc).__name__}: {str(exc)[:200]}")


# ════════════════════════════════════════════════════════════════
# GUI KATMANI
# ════════════════════════════════════════════════════════════════

# ── Renk Paleti (janleague dark theme) ───────────────────────
COLORS = {
    "bg_dark":        "#0D0D0D",   # Ana arka plan
    "bg_card":        "#161616",   # Kart / header arka planı
    "bg_input":       "#1E1E1E",   # Giriş kutusu arka planı
    "accent":         "#FF0000",   # YouTube kırmızısı
    "accent_hover":   "#CC0000",   # Hover durumu
    "accent_dim":     "#350000",   # Devre dışı / baskı rengi
    "text_primary":   "#F5F5F5",   # Ana metin
    "text_secondary": "#999999",   # İkincil metin
    "text_dim":       "#444444",   # Soluk / placeholder metin
    "success":        "#22C55E",   # Başarı yeşili
    "warning":        "#F59E0B",   # Uyarı sarısı
    "error":          "#EF4444",   # Hata kırmızısı
    "progress_bg":    "#222222",   # Progress bar arka planı
    "border":         "#272727",   # Kenarlık rengi
    "github":         "#6E40C9",   # GitHub mor
}

# ── Sabitler ─────────────────────────────────────────────────
AUTHOR      = "janleague"
GITHUB_URL  = "https://github.com/janleague"
APP_VERSION = "1.0.0"


class App(ctk.CTk):
    """
    Ana uygulama penceresi.

    CustomTkinter tabanlı, sabit boyutlu, karanlık tema.
    Tüm ağ/işlem yükü ayrı bir thread'de çalışır; GUI her zaman duyarlıdır.

    Author : janleague (https://github.com/janleague)
    """

    TITLE  = f"YouTube Downloader  ·  by {AUTHOR}"
    W      = 580
    H      = 670

    def __init__(self):
        super().__init__()

        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Pencere
        self.title(self.TITLE)
        self.geometry(f"{self.W}x{self.H}")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        self._center_window()

        # İndirme mantığı — script dosyasıyla aynı klasörde "Downloads" alt klasörü
        script_dir    = Path(__file__).resolve().parent
        downloads_dir = script_dir / "Downloads"
        self.manager  = DownloadManager(downloads_dir)
        self.manager.on_progress = self._cb_progress
        self.manager.on_status   = self._cb_status
        self.manager.on_complete = self._cb_complete
        self.manager.on_error    = self._cb_error

        # Durum değişkenleri
        self._downloading = False
        self._fmt_var     = ctk.StringVar(value="MP3")

        # UI
        self._build_ui()

    # ── Pencereyi Ortala ──────────────────────────────────────
    def _center_window(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{self.W}x{self.H}+{(sw - self.W) // 2}+{(sh - self.H) // 2}")

    # ══════════════════════════════════════════════════════════
    # UI İNŞASI
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_url_section()
        self._build_format_section()
        self._build_resolution_section()
        self._build_download_button()
        self._build_progress_section()
        self._build_status_section()
        self._build_footer()

    # ── Header ────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=100)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Sol: ▶ ikonu
        ctk.CTkLabel(
            hdr, text="▶",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=(26, 10), pady=26)

        # Orta: başlık + altyazı
        mid = ctk.CTkFrame(hdr, fg_color="transparent")
        mid.pack(side="left", pady=20)

        ctk.CTkLabel(
            mid, text="YouTube Downloader",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            mid, text="MP3 & MP4  ·  Yüksek Kalite  ·  Ücretsiz",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Sağ: yazar imzası
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right", padx=22, pady=20)

        ctk.CTkLabel(
            right, text=f"by {AUTHOR}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(anchor="e")

        ctk.CTkLabel(
            right, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"]
        ).pack(anchor="e")

    # ── URL Girişi ────────────────────────────────────────────
    def _build_url_section(self):
        sec = self._section("YouTube URL")

        self.url_entry = ctk.CTkEntry(
            sec,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=52,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_dim"],
        )
        self.url_entry.pack(fill="x")
        # Enter tuşuyla da indirme başlatılabilir
        self.url_entry.bind("<Return>", lambda _: self._start_download())

        ctk.CTkButton(
            sec, text="✕  Temizle",
            width=90, height=28,
            corner_radius=7,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=COLORS["bg_input"],
            text_color=COLORS["text_dim"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._clear_url
        ).pack(anchor="e", pady=(5, 0))

    # ── Format Seçimi ─────────────────────────────────────────
    def _build_format_section(self):
        sec = self._section("Format")

        toggle = ctk.CTkFrame(sec, fg_color=COLORS["bg_input"], corner_radius=10)
        toggle.pack(fill="x")

        for fmt in ("MP3", "MP4"):
            ctk.CTkRadioButton(
                toggle,
                text=fmt,
                variable=self._fmt_var,
                value=fmt,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["text_primary"],
                command=self._on_format_change,
            ).pack(side="left", padx=24, pady=13)

        self.fmt_desc = ctk.CTkLabel(
            sec,
            text="🎵  En yüksek kalite ses  ·  320 kbps MP3",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.fmt_desc.pack(anchor="w", pady=(6, 0))

    # ── Çözünürlük (yalnızca MP4) ─────────────────────────────
    def _build_resolution_section(self):
        self.res_sec = self._section("Çözünürlük")

        self.res_var = ctk.StringVar(value="1080p")
        ctk.CTkOptionMenu(
            self.res_sec,
            values=DownloadManager.RESOLUTIONS,
            variable=self.res_var,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_primary"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_input"],
            dropdown_text_color=COLORS["text_primary"],
        ).pack(fill="x")

        # MP3 varsayılan → gizle
        self.res_sec.pack_forget()

    # ── İndir Butonu ──────────────────────────────────────────
    def _build_download_button(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="x", padx=28, pady=(16, 0))

        self.dl_btn = ctk.CTkButton(
            wrap,
            text="⬇  İndir",
            height=52,
            corner_radius=12,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            command=self._start_download,
        )
        self.dl_btn.pack(fill="x")

    # ── Progress Bar ──────────────────────────────────────────
    def _build_progress_section(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="x", padx=28, pady=(16, 0))

        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))

        self.pct_lbl = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.pct_lbl.pack(side="left")

        self.eta_lbl = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.eta_lbl.pack(side="right")

        self.spd_lbl = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"]
        )
        self.spd_lbl.pack(side="right", padx=(0, 10))

        self.prog = ctk.CTkProgressBar(
            wrap,
            height=10,
            corner_radius=5,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["accent"],
            mode="determinate",
        )
        self.prog.set(0)
        self.prog.pack(fill="x")

    # ── Durum Etiketi ─────────────────────────────────────────
    def _build_status_section(self):
        self.status_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            wraplength=524,
        )
        self.status_lbl.pack(pady=(12, 0), padx=28)

    # ── Alt Bar (footer) ──────────────────────────────────────
    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=40)
        ftr.pack(side="bottom", fill="x")
        ftr.pack_propagate(False)

        # Sol: klasör yolu
        ctk.CTkLabel(
            ftr,
            text=f"📁  {self.manager.downloads_dir}",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=14, pady=10)

        # Sağ: GitHub linki
        gh_btn = ctk.CTkButton(
            ftr,
            text="⌥  github/janleague",
            width=150, height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=COLORS["bg_input"],
            text_color=COLORS["text_dim"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._open_github,
        )
        gh_btn.pack(side="right", padx=(0, 8))

        # Klasörü aç
        ctk.CTkButton(
            ftr,
            text="Klasörü Aç",
            width=90, height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=COLORS["bg_input"],
            text_color=COLORS["text_dim"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._open_folder,
        ).pack(side="right", padx=(0, 4))

    # ══════════════════════════════════════════════════════════
    # YARDIMCI METOD
    # ══════════════════════════════════════════════════════════

    def _section(self, label: str) -> ctk.CTkFrame:
        """Etiketli bir bölüm çerçevesi oluşturup döndürür."""
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="x", padx=28, pady=(14, 0))

        ctk.CTkLabel(
            outer,
            text=label.upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["text_dim"]
        ).pack(anchor="w", pady=(0, 5))

        return outer

    # ══════════════════════════════════════════════════════════
    # OLAY YÖNETİCİLERİ
    # ══════════════════════════════════════════════════════════

    def _on_format_change(self):
        """MP3 ↔ MP4 değiştiğinde çözünürlük bölümünü göster/gizle."""
        if self._fmt_var.get() == "MP4":
            self.res_sec.pack(fill="x", padx=28, pady=(14, 0),
                              before=self.dl_btn.master)
            self.fmt_desc.configure(text="🎬  Video + Ses  ·  Seçilen çözünürlük")
        else:
            self.res_sec.pack_forget()
            self.fmt_desc.configure(text="🎵  En yüksek kalite ses  ·  320 kbps MP3")

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self.url_entry.focus()

    def _open_folder(self):
        """İndirmeler klasörünü dosya yöneticisinde açar."""
        folder = str(self.manager.downloads_dir)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except Exception:
            pass  # Klasör açılamazsa sessizce geç

    def _open_github(self):
        """GitHub profilini varsayılan tarayıcıda açar."""
        import webbrowser
        webbrowser.open(GITHUB_URL)

    # ── İndirme Akışı ─────────────────────────────────────────
    def _start_download(self):
        """İndir butonuna basıldığında veya Enter'a basıldığında çalışır."""
        if self._downloading:
            return

        url = self.url_entry.get().strip()

        if not url:
            self._status("⚠  Lütfen bir YouTube URL'si girin.", "warning")
            self.url_entry.focus()
            return

        if not DownloadManager.is_valid_url(url):
            self._status("⚠  Geçersiz URL formatı. Lütfen geçerli bir YouTube bağlantısı girin.", "warning")
            return

        # Başlat
        self._downloading = True
        self._set_ui_busy(True)
        self._reset_progress()
        self._status("🔍  Video bilgileri alınıyor...", "info")

        fmt = self._fmt_var.get()
        res = self.res_var.get() if fmt == "MP4" else None

        # İndirmeyi arka planda çalıştır — GUI'yi bloke etmez
        threading.Thread(
            target=self._worker,
            args=(url, fmt, res),
            daemon=True
        ).start()

    def _worker(self, url: str, fmt: str, res: Optional[str]):
        """Thread içinde çalışan iş parçacığı."""
        try:
            if fmt == "MP3":
                self.manager.download_mp3(url)
            else:
                self.manager.download_mp4(url, res)
        except Exception as exc:
            # _execute_download normalde her şeyi yakalar;
            # bu satır yalnızca beklenmedik sızıntılar için güvenlik ağıdır.
            self._cb_error(f"Kritik hata: {type(exc).__name__}: {str(exc)[:200]}")

    # ── UI Durum Kontrolü ─────────────────────────────────────
    def _set_ui_busy(self, busy: bool):
        if busy:
            self.dl_btn.configure(text="⏳  İndiriliyor...",
                                   fg_color=COLORS["accent_dim"], state="disabled")
            self.url_entry.configure(state="disabled")
        else:
            self.dl_btn.configure(text="⬇  İndir",
                                   fg_color=COLORS["accent"], state="normal")
            self.url_entry.configure(state="normal")

    def _reset_progress(self):
        self.prog.set(0)
        self.pct_lbl.configure(text="")
        self.spd_lbl.configure(text="")
        self.eta_lbl.configure(text="")

    def _status(self, msg: str, level: str = "info"):
        colors = {
            "info":    COLORS["text_secondary"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error":   COLORS["error"],
        }
        self.status_lbl.configure(text=msg,
                                   text_color=colors.get(level, COLORS["text_secondary"]))

    # ══════════════════════════════════════════════════════════
    # CALLBACK'LER  (DownloadManager → GUI)
    # after(0, ...) sayesinde thread-safe çalışır
    # ══════════════════════════════════════════════════════════

    def _cb_progress(self, pct: float, speed: str, eta: str):
        def _u():
            self.prog.set(pct / 100)
            self.pct_lbl.configure(text=f"%{pct:.1f}")
            self.spd_lbl.configure(text=speed)
            self.eta_lbl.configure(text=eta)
        self.after(0, _u)

    def _cb_status(self, msg: str, level: str):
        self.after(0, lambda: self._status(msg, level))

    def _cb_complete(self, filepath: str, title: str):
        def _u():
            self.prog.set(1.0)
            self.pct_lbl.configure(text="%100")
            self.spd_lbl.configure(text="")
            self.eta_lbl.configure(text="")
            self._status(f"✅  İndirildi: {title}", "success")
            self._set_ui_busy(False)
            self._downloading = False
            self.url_entry.delete(0, "end")
            self.url_entry.focus()
        self.after(0, _u)

    def _cb_error(self, msg: str):
        def _u():
            self._reset_progress()
            self._status(f"❌  {msg}", "error")
            self._set_ui_busy(False)
            self._downloading = False
            self.url_entry.focus()
        self.after(0, _u)


# ════════════════════════════════════════════════════════════════
# GİRİŞ NOKTASI
# ════════════════════════════════════════════════════════════════

def main():
    """Uygulamayı başlatır."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
