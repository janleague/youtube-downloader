# YouTube İndirici

Tauri + React arayüzlü, `yt-dlp` tabanlı Windows video ve ses indirici.

## Özellikler

- MP3: 128, 192, 256 ve 320 kbps
- MP4: 360p ile 2160p arası kalite seçimi
- Canlı ilerleme, hız ve kalan süre
- Gerçek indirme kütüphanesi, küçük resimler ve dosya açma
- Kalıcı klasör, format, kalite, dil, bildirim ve tema ayarları
- Türkçe ve İngilizce arayüz
- Tauri masaüstü bildirimleri

## Kaynaktan çalıştırma

Gerekenler:

- Windows 10/11
- Python 3.10+
- Node.js
- Rust
- MP3 ve yüksek kaliteli MP4 birleştirme için FFmpeg

```powershell
python -m pip install -r requirements.txt
cd .\NEWGUI\react-src
npm install
npm run tauri dev
```

FFmpeg gerekirse:

```powershell
winget install --id Gyan.FFmpeg --exact
```

## Test ve derleme

```powershell
python -m unittest discover -s tests -v
cd .\NEWGUI\react-src
npm run build
cargo check --manifest-path .\src-tauri\Cargo.toml
```

Windows installer oluşturmak için:

```powershell
cd .\NEWGUI\react-src
npm run release:build
```

## Yapı

```text
backend.py                 Tauri ile Python arasındaki JSON köprüsü
core/                      yt-dlp, ayarlar ve kütüphane mantığı
NEWGUI/react-src/src/      React arayüzü
NEWGUI/react-src/src-tauri Tauri/Rust masaüstü katmanı
tests/                     Python çekirdek testleri
```

Ayarlar `%LOCALAPPDATA%\janleague\YouTubeDownloader\settings.ini` altında,
varsayılan indirmeler aynı dizindeki `Downloads` klasöründe tutulur.

Yalnızca indirme yetkinizin bulunduğu içerikleri indirin. Bu proje YouTube veya
Google ile bağlantılı değildir.
