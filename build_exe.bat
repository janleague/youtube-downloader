@echo off
setlocal
cd /d "%~dp0"

echo.
echo  ================================================
echo   YouTube Downloader - EXE Builder
echo  ================================================
echo.

python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] PyInstaller kuruluyor...
    python -m pip install pyinstaller
    if errorlevel 1 goto :error
)

echo [*] Bagimliliklar kontrol ediliyor...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [*] EXE olusturuluyor...
python -m PyInstaller --noconfirm --clean YouTubeDownloader.spec
if errorlevel 1 goto :error

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"

if exist "%ISCC%" (
    echo [*] Windows kurulum dosyasi olusturuluyor...
    "%ISCC%" installer.iss
    if errorlevel 1 goto :error
) else (
    echo [!] Inno Setup bulunamadi. Yalnizca portable EXE olusturuldu.
    echo     Kurulum: winget install --id JRSoftware.InnoSetup --exact
)

echo.
echo [+] Hazir: dist\YouTubeDownloader.exe
if exist "dist\YouTubeDownloader-Setup-v2.0.0.exe" (
    echo [+] Hazir: dist\YouTubeDownloader-Setup-v2.0.0.exe
)
exit /b 0

:error
echo.
echo [HATA] Build tamamlanamadi.
exit /b 1
