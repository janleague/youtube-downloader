"""Tauri ile Python indirme motoru arasındaki satır-tabanlı JSON köprüsü."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.download_manager import DownloadManager
from core.library_service import scan_library
from core.settings_store import SettingsStore


APP_DIR = Path(__file__).resolve().parent


def emit(event: str, payload=None):
    print(
        json.dumps({"event": event, "payload": payload}, ensure_ascii=False),
        flush=True,
    )


def output(payload):
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def store() -> SettingsStore:
    return SettingsStore(APP_DIR)


def state_payload(settings: SettingsStore) -> dict:
    downloads_dir = settings.downloads_dir
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return {
        "settings": {
            "downloadsDir": str(downloads_dir),
            "defaultFormat": settings.default_format.lower(),
            "resolution": settings.resolution,
            "audioQuality": settings.audio_quality,
            "language": settings.language,
            "notifications": settings.notifications,
            "darkTheme": settings.dark_theme,
        },
        "ffmpegOk": DownloadManager.check_ffmpeg(),
    }


def command_state(_args):
    output(state_payload(store()))


def command_library(_args):
    settings = store()
    output(scan_library(settings.downloads_dir))


def command_set(args):
    allowed = {
        "downloads_dir",
        "default_format",
        "resolution",
        "audio_quality",
        "language",
        "notifications",
        "dark_theme",
    }
    if args.key not in allowed:
        raise ValueError("Bilinmeyen ayar.")
    value = json.loads(args.value)
    settings = store()
    settings.set(args.key, value)
    if args.key == "downloads_dir":
        settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    output(state_payload(settings))


def command_download(args):
    settings = store()
    manager = DownloadManager(
        settings.downloads_dir,
        settings.audio_quality,
        on_progress=lambda pct, speed, eta: emit(
            "progress", {"pct": pct, "speed": speed, "eta": eta}
        ),
        on_status=lambda message, level: emit(
            "status", {"message": message, "level": level}
        ),
        on_complete=lambda filepath, title: emit(
            "complete", {"filepath": filepath, "title": title}
        ),
        on_error=lambda message: emit("error", {"message": message}),
    )
    manager.download(args.url, args.format, args.resolution)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("state").set_defaults(handler=command_state)
    sub.add_parser("library").set_defaults(handler=command_library)

    set_parser = sub.add_parser("set")
    set_parser.add_argument("key")
    set_parser.add_argument("value")
    set_parser.set_defaults(handler=command_set)

    download = sub.add_parser("download")
    download.add_argument("url")
    download.add_argument("format", choices=("mp3", "mp4"))
    download.add_argument("--resolution")
    download.set_defaults(handler=command_download)
    return parser


def main():
    try:
        args = build_parser().parse_args()
        args.handler(args)
    except Exception as exc:
        emit("error", {"message": str(exc)})
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
