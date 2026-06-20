"""İndirme klasöründeki medya dosyalarını kütüphane modeline çevirir."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


MEDIA_EXTENSIONS = {".mp3", ".m4a", ".mp4", ".mkv", ".webm"}


def scan_library(folder: Path) -> list[dict]:
    folder = Path(folder)
    if not folder.exists():
        return []
    files = [
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [_describe(path) for path in files]


def _describe(path: Path) -> dict:
    fmt = "MP3" if path.suffix.lower() in {".mp3", ".m4a"} else "MP4"
    return {
        "title": path.stem,
        "format": fmt,
        "size": _format_size(path.stat().st_size),
        "quality": _probe_quality(path, fmt),
        "path": str(path),
    }


def _format_size(size: int) -> str:
    if size >= 1_073_741_824:
        return f"{size / 1_073_741_824:.1f} GB"
    if size >= 1_048_576:
        return f"{size / 1_048_576:.1f} MB"
    return f"{max(1, size // 1024)} KB"


def _probe_quality(path: Path, fmt: str) -> str:
    if not shutil.which("ffprobe"):
        return "ses" if fmt == "MP3" else "video"
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", str(path),
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        streams = json.loads(result.stdout or "{}").get("streams", [])
        if fmt == "MP3":
            audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
            rate = int(audio.get("bit_rate") or 0)
            return f"{round(rate / 1000)} kbps" if rate else "ses"
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        height = video.get("height")
        return f"{height}p" if height else "video"
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
        return "ses" if fmt == "MP3" else "video"
