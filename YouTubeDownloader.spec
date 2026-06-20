# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

yt_datas, yt_binaries, yt_hiddenimports = collect_all("yt_dlp")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=yt_binaries,
    datas=yt_datas + [
        ("fonts", "fonts"),
        ("assets/janleague-avatar-round.png", "assets"),
        ("app_icon.ico", "."),
    ],
    hiddenimports=yt_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="YouTubeDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=["app_icon.ico"],
    version="version_info.txt",
)
