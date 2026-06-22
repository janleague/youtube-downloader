$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$binaryDir = Join-Path $root "NEWGUI\react-src\src-tauri\binaries"
$workDir = Join-Path $root ".backend-build"
$specDir = Join-Path $root ".backend-spec"
$assetDir = Join-Path $root ".backend-assets"
$output = Join-Path $binaryDir "youtube-downloader-backend"
$sidecar = Join-Path $binaryDir "backend"
$bundledFfmpeg = Join-Path $assetDir "ffmpeg.exe"

New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null
New-Item -ItemType Directory -Force -Path $assetDir | Out-Null
Remove-Item -LiteralPath $output -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $sidecar -Recurse -Force -ErrorAction SilentlyContinue

$ffmpegSource = python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
$ffmpegSource = $ffmpegSource.Trim()
if (-not (Test-Path -LiteralPath $ffmpegSource)) {
    throw "Bundled ffmpeg source not found: $ffmpegSource"
}
Copy-Item -LiteralPath $ffmpegSource -Destination $bundledFfmpeg -Force

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --console `
    --name youtube-downloader-backend `
    --distpath $binaryDir `
    --workpath $workDir `
    --specpath $specDir `
    --collect-all yt_dlp `
    --add-binary "$bundledFfmpeg;." `
    (Join-Path $root "backend.py")

Move-Item -LiteralPath $output -Destination $sidecar
Write-Host "Backend sidecar hazır: $sidecar"
