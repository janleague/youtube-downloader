<div align="center">

# ▶ YouTube Downloader

**Modern, karanlık temalı YouTube MP3 & MP4 indirici**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.x-1F6FEB?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/by-janleague-6E40C9?style=for-the-badge&logo=github)](https://github.com/janleague)

</div>

---

## ✨ Özellikler

- **MP3 & MP4** — tek uygulamadan iki format
- **MP3**: En yüksek kalite ses, otomatik **320 kbps** dönüşümü + ID3 metadata
- **MP4**: 144p'den 2160p (4K)'ya seçilebilir çözünürlük
- **Gerçek zamanlı progress bar** — yüzde, hız (MB/s) ve kalan süre
- **Kapsamlı hata yönetimi** — 20+ hata türü kullanıcı dostu mesajlara çevrilir
- **ffmpeg kontrolü** — MP3 dönüşümünden önce otomatik kontrol
- **İndirmeler klasörü** — script ile aynı dizinde `Downloads/` altında toplanır
- **GitHub butonu** — footer'dan direkt profile git
- **Tek dosya** — kurulum dışında ek bir şey yok

---

## 🖥️ Ekran Görüntüsü

```
╔══════════════════════════════════════════════════╗
║  ▶  YouTube Downloader          by janleague  ║
║     MP3 & MP4  ·  Yüksek Kalite  ·  Ücretsiz  v1.0  ║
╠══════════════════════════════════════════════════╣
║  YOUTUBE URL                                     ║
║  ┌──────────────────────────────────────────┐    ║
║  │  https://www.youtube.com/watch?v=...     │    ║
║  └──────────────────────────────────────────┘    ║
║                                      [✕ Temizle] ║
║  FORMAT                                          ║
║  ┌──────────────────────────────────────────┐    ║
║  │  ● MP3        ○ MP4                      │    ║
║  └──────────────────────────────────────────┘    ║
║  🎵  En yüksek kalite ses  ·  320 kbps MP3       ║
║                                                  ║
║  ┌────────────────[⬇  İndir]─────────────────┐   ║
║  └──────────────────────────────────────────┘    ║
║  %73.4            1.8 MB/s           12s kaldı  ║
║  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░    ║
║  🔄  Video bilgileri alınıyor...                ║
╠══════════════════════════════════════════════════╣
║  📁 ./Downloads        [Klasörü Aç] [github] ║
╚══════════════════════════════════════════════════╝
```

---

## 📦 Kurulum

### 1. Depoyu klonla

```bash
git clone https://github.com/janleague/youtube-downloader.git
cd youtube-downloader
```

### 2. Python bağımlılıklarını kur

```bash
pip install customtkinter yt-dlp
```

> **Not:** Python 3.10 veya üzeri gereklidir.

### 3. ffmpeg'i kur (zorunlu)

MP3 dönüşümü ve yüksek kaliteli MP4 birleştirme için ffmpeg şarttır.

| Platform | Komut |
|----------|-------|
| **Windows** | `winget install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Ubuntu/Debian** | `sudo apt install ffmpeg` |
| **Fedora** | `sudo dnf install ffmpeg` |
| **Manuel** | [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) → PATH'e ekle |

Kurulumu doğrula:
```bash
ffmpeg -version
```

---

## 🚀 Kullanım

```bash
python youtube_downloader.py
```

1. YouTube video URL'sini giriş kutusuna yapıştır
2. **MP3** veya **MP4** seç
3. MP4 seçildiyse çözünürlük belirle (720p, 1080p, vb.)
4. **⬇ İndir** butonuna bas veya `Enter`'a bas
5. İndirilen dosya `Downloads/` klasörüne kaydedilir

---

## 📁 Proje Yapısı

```
youtube-downloader/
│
├── youtube_downloader.py   # Ana uygulama (tek dosya)
├── Downloads/              # İndirilen dosyalar burada toplanır
│   ├── video_adi.mp3
│   └── video_adi.mp4
├── README.md
└── LICENSE
```

---

## ⚙️ Teknik Detaylar

### Mimari

Uygulama iki katmana ayrılmıştır:

**`DownloadManager` (Logic Katmanı)**
- GUI'den tamamen bağımsız
- `yt-dlp` ile indirme ve dönüştürme
- 20+ hata senaryosu için kullanıcı dostu mesajlar
- `callback` sistemi ile GUI'ye ilerleme bilgisi gönderir

**`App` (GUI Katmanı)**
- `CustomTkinter` tabanlı, karanlık tema
- Thread-safe `after()` callback sistemi
- Tüm ağ işlemleri ayrı `daemon thread`'de — GUI her zaman duyarlı

### Desteklenen URL Formatları

| Format | Örnek |
|--------|-------|
| Standart | `https://www.youtube.com/watch?v=VIDEO_ID` |
| Kısa | `https://youtu.be/VIDEO_ID` |
| Shorts | `https://www.youtube.com/shorts/VIDEO_ID` |

### Hata Yönetimi

| Hata Türü | Açıklama |
|-----------|----------|
| Private Video | Özel video uyarısı |
| Geo-kısıtlı | Bölge yasağı uyarısı |
| Üye videosu | Üyelik gerekliliği uyarısı |
| ffmpeg yok | Kurulum talimatıyla birlikte uyarı |
| İnternet yok | Ağ bağlantı hatası |
| HTTP 403/404/429/500 | Sunucu hata kodları |
| Disk alanı yok | Yetersiz alan uyarısı |
| İzin hatası | Klasör yazma izni uyarısı |
| Telif hakkı | Copyright kısıtlaması uyarısı |
| DRM korumalı | Koruma uyarısı |

---

## 🔧 Gereksinimler

| Bağımlılık | Versiyon | Açıklama |
|------------|----------|----------|
| Python | ≥ 3.10 | `str \| None` söz dizimi |
| customtkinter | ≥ 5.0 | Modern GUI framework |
| yt-dlp | latest | YouTube indirme motoru |
| ffmpeg | herhangi | Ses/video dönüştürme |

---

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

<div align="center">

**Geliştirici: [janleague](https://github.com/janleague)**

*Beğendiysen ⭐ vermeyi unutma!*

</div>
