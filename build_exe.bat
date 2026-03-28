@echo off
title YouTube Downloader - EXE Builder
echo.
echo  ================================================
echo   YouTube Downloader - EXE Olusturuluyor
echo  ================================================
echo.

:: PyInstaller kurulu mu kontrol et
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] PyInstaller bulunamadi, kuruluyor...
    python -m pip install pyinstaller --quiet
    echo [+] PyInstaller kuruldu.
    echo.
)

echo [*] EXE olusturuluyor, lutfen bekleyin...
echo     (Bu islem 1-2 dakika surebilir)
echo.

python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --icon "app_icon.ico" ^
    --name "YouTubeDownloader" ^
    youtube_downloader.py

echo.
if exist "dist\YouTubeDownloader.exe" (
    echo  ================================================
    echo   BASARILI! EXE hazir:
    echo   dist\YouTubeDownloader.exe
    echo  ================================================
    echo.
    echo  dist klasoru aciliyor...
    explorer dist
) else (
    echo  [HATA] EXE olusturulamadi. Hata mesajini kontrol edin.
)

echo.
pause
