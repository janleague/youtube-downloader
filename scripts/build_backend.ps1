$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$binaryDir = Join-Path $root "NEWGUI\react-src\src-tauri\binaries"
$workDir = Join-Path $root ".backend-build"
$specDir = Join-Path $root ".backend-spec"
$output = Join-Path $binaryDir "youtube-downloader-backend.exe"
$sidecar = Join-Path $binaryDir "youtube-downloader-backend-x86_64-pc-windows-msvc.exe"

New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --console `
    --name youtube-downloader-backend `
    --distpath $binaryDir `
    --workpath $workDir `
    --specpath $specDir `
    --collect-all yt_dlp `
    (Join-Path $root "backend.py")

Move-Item -LiteralPath $output -Destination $sidecar -Force
Write-Host "Backend sidecar hazır: $sidecar"
