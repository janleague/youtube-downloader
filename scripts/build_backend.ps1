$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$binaryDir = Join-Path $root "NEWGUI\react-src\src-tauri\binaries"
$workDir = Join-Path $root ".backend-build"
$specDir = Join-Path $root ".backend-spec"
$assetDir = Join-Path $root ".backend-assets"
$output = Join-Path $binaryDir "youtube-downloader-backend"
$sidecar = Join-Path $binaryDir "backend"
$bundledFfmpeg = Join-Path $assetDir "ffmpeg.exe"
$bundledYtDlp = Join-Path $assetDir "yt-dlp"
$bundledYtDlpHash = Join-Path $assetDir "yt-dlp.sha256"
$bundledDeno = Join-Path $assetDir "deno.exe"
$bundledDenoHash = Join-Path $assetDir "deno.exe.sha256"
$bundledDenoVersion = Join-Path $assetDir "deno.version"

function Get-Sha256([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $algorithm.ComputeHash($stream)
        return -join ($bytes | ForEach-Object { $_.ToString("x2") })
    } finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

function Download-File([string]$url, [string]$destination) {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $destination
}

function Download-Text([string]$url) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url
    if ($response.Content -is [byte[]]) {
        return [Text.Encoding]::UTF8.GetString($response.Content)
    }
    return [string]$response.Content
}

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

$ytDlpSumsUrl = "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/SHA2-256SUMS"
$ytDlpUrl = "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp"
$ytDlpSums = Download-Text $ytDlpSumsUrl
$ytDlpMatch = [regex]::Match(
    $ytDlpSums,
    "(?im)^([0-9a-f]{64})\s+\*?yt-dlp\s*$"
)
if (-not $ytDlpMatch.Success) {
    throw "Official yt-dlp checksum could not be read."
}
$ytDlpExpected = $ytDlpMatch.Groups[1].Value.ToLowerInvariant()
if (-not (Test-Path -LiteralPath $bundledYtDlp) -or
    (Get-Sha256 $bundledYtDlp) -ne $ytDlpExpected) {
    $ytDlpDownload = Join-Path $assetDir "yt-dlp.download"
    Download-File $ytDlpUrl $ytDlpDownload
    if ((Get-Sha256 $ytDlpDownload) -ne $ytDlpExpected) {
        Remove-Item -LiteralPath $ytDlpDownload -Force -ErrorAction SilentlyContinue
        throw "Official yt-dlp checksum verification failed."
    }
    Move-Item -LiteralPath $ytDlpDownload -Destination $bundledYtDlp -Force
}
Set-Content -LiteralPath $bundledYtDlpHash -Value $ytDlpExpected -Encoding ascii

$denoVersion = (Download-Text "https://dl.deno.land/release-latest.txt").Trim()
$denoArchiveName = "deno-x86_64-pc-windows-msvc.zip"
$denoBaseUrl = "https://github.com/denoland/deno/releases/download/$denoVersion"
$denoChecksumText = Download-Text "$denoBaseUrl/$denoArchiveName.sha256sum"
$denoMatch = [regex]::Match($denoChecksumText, "(?i)[0-9a-f]{64}")
if (-not $denoMatch.Success) {
    throw "Official Deno checksum could not be read."
}
$denoExpected = $denoMatch.Value.ToLowerInvariant()
$denoCachedVersion = if (Test-Path -LiteralPath $bundledDenoVersion) {
    (Get-Content -Raw -LiteralPath $bundledDenoVersion).Trim()
} else {
    ""
}
if (-not (Test-Path -LiteralPath $bundledDeno) -or $denoCachedVersion -ne $denoVersion) {
    $denoArchive = Join-Path $assetDir $denoArchiveName
    $denoExtract = Join-Path $assetDir "deno-extract"
    Remove-Item -LiteralPath $denoExtract -Recurse -Force -ErrorAction SilentlyContinue
    Download-File "$denoBaseUrl/$denoArchiveName" $denoArchive
    if ((Get-Sha256 $denoArchive) -ne $denoExpected) {
        Remove-Item -LiteralPath $denoArchive -Force -ErrorAction SilentlyContinue
        throw "Official Deno checksum verification failed."
    }
    Expand-Archive -LiteralPath $denoArchive -DestinationPath $denoExtract -Force
    Copy-Item -LiteralPath (Join-Path $denoExtract "deno.exe") -Destination $bundledDeno -Force
    Remove-Item -LiteralPath $denoArchive -Force
    Remove-Item -LiteralPath $denoExtract -Recurse -Force
}
Set-Content -LiteralPath $bundledDenoHash -Value (Get-Sha256 $bundledDeno) -Encoding ascii
Set-Content -LiteralPath $bundledDenoVersion -Value $denoVersion -Encoding ascii

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
    --add-data "$bundledYtDlp;." `
    --add-data "$bundledYtDlpHash;." `
    --add-binary "$bundledDeno;." `
    --add-data "$bundledDenoHash;." `
    (Join-Path $root "backend.py")

Move-Item -LiteralPath $output -Destination $sidecar
Write-Host "Backend sidecar hazır: $sidecar"
