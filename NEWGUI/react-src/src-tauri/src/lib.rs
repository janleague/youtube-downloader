use std::{
    collections::HashMap,
    fs,
    io::{BufRead, BufReader, Read},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::UNIX_EPOCH,
};

use serde_json::Value;
use tauri::{AppHandle, Emitter, Manager, State, WebviewWindow};
use tauri_plugin_notification::NotificationExt;

struct DownloadProcess(Mutex<Option<Child>>);

fn data_root() -> PathBuf {
    std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("USERPROFILE").map(PathBuf::from))
        .unwrap_or_else(std::env::temp_dir)
        .join("janleague")
        .join("YouTubeDownloader")
}

fn read_settings() -> HashMap<String, String> {
    let Ok(contents) = fs::read_to_string(data_root().join("settings.ini")) else {
        return HashMap::new();
    };
    let mut values = HashMap::new();
    let mut in_general = false;
    for raw_line in contents.lines() {
        let line = raw_line.trim();
        if line.starts_with('[') && line.ends_with(']') {
            in_general = line.eq_ignore_ascii_case("[General]");
        } else if in_general && !line.is_empty() && !line.starts_with(['#', ';']) {
            if let Some((key, value)) = line.split_once('=') {
                values.insert(key.trim().to_lowercase(), value.trim().to_string());
            }
        }
    }
    values
}

fn setting_bool(values: &HashMap<String, String>, key: &str, default: bool) -> bool {
    values
        .get(key)
        .map(|value| matches!(value.to_lowercase().as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(default)
}

fn ffmpeg_available(app: &AppHandle) -> bool {
    let mut candidates = Vec::new();
    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push(
            resource_dir
                .join("binaries")
                .join("backend")
                .join("_internal")
                .join("ffmpeg.exe"),
        );
    }
    candidates.push(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("binaries")
            .join("backend")
            .join("_internal")
            .join("ffmpeg.exe"),
    );
    candidates.into_iter().any(|path| path.is_file())
}

fn app_state(app: &AppHandle) -> Result<Value, String> {
    let values = read_settings();
    let root = data_root();
    let default_downloads = root.join("Downloads");
    let downloads_dir = values
        .get("downloads_dir")
        .filter(|value| !value.trim().is_empty())
        .map(PathBuf::from)
        .unwrap_or(default_downloads);
    fs::create_dir_all(&downloads_dir)
        .map_err(|error| format!("İndirme klasörü hazırlanamadı: {error}"))?;

    Ok(serde_json::json!({
        "settings": {
            "downloadsDir": downloads_dir.to_string_lossy(),
            "defaultFormat": values.get("default_format").map(|value| value.to_lowercase()).unwrap_or_else(|| "mp3".into()),
            "resolution": values.get("resolution").cloned().unwrap_or_else(|| "1080p".into()),
            "audioQuality": values.get("audio_quality").cloned().unwrap_or_else(|| "320".into()),
            "language": values.get("language").cloned().unwrap_or_else(|| "tr".into()),
            "notifications": setting_bool(&values, "notifications", true),
            "darkTheme": setting_bool(&values, "dark_theme", true),
        },
        "ffmpegOk": ffmpeg_available(app),
    }))
}

const MEDIA_EXTENSIONS: &[&str] = &["mp3", "m4a", "mp4", "mkv", "webm"];
const THUMBNAIL_EXTENSIONS: &[&str] = &["jpg", "jpeg", "png", "webp", "avif"];
const SIDECAR_EXTENSIONS: &[&str] = &[
    "json", "description", "vtt", "srt", "ass", "lrc", "part", "ytdl",
];

fn downloads_dir() -> Result<PathBuf, String> {
    let values = read_settings();
    let root = data_root();
    let folder = values
        .get("downloads_dir")
        .filter(|value| !value.trim().is_empty())
        .map(PathBuf::from)
        .unwrap_or_else(|| root.join("Downloads"));
    fs::create_dir_all(&folder)
        .map_err(|error| format!("İndirme klasörü hazırlanamadı: {error}"))?;
    Ok(folder)
}

fn extension(path: &Path) -> String {
    path.extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_lowercase()
}

fn is_media(path: &Path) -> bool {
    MEDIA_EXTENSIONS.contains(&extension(path).as_str())
}

fn metadata_path(path: &Path) -> PathBuf {
    path.with_file_name(format!(
        "{}.info.json",
        path.file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or_default()
    ))
}

fn load_metadata(path: &Path) -> Value {
    fs::read_to_string(metadata_path(path))
        .ok()
        .and_then(|contents| serde_json::from_str(&contents).ok())
        .filter(Value::is_object)
        .unwrap_or_else(|| serde_json::json!({}))
}

fn format_size(size: u64) -> String {
    if size >= 1_073_741_824 {
        format!("{:.1} GB", size as f64 / 1_073_741_824.0)
    } else if size >= 1_048_576 {
        format!("{:.1} MB", size as f64 / 1_048_576.0)
    } else {
        format!("{} KB", std::cmp::max(1, size / 1024))
    }
}

fn format_duration(value: Option<f64>) -> String {
    let Some(seconds) = value.map(|value| value.max(0.0).round() as u64) else {
        return String::new();
    };
    let hours = seconds / 3600;
    let minutes = (seconds % 3600) / 60;
    let seconds = seconds % 60;
    if hours > 0 {
        format!("{hours}:{minutes:02}:{seconds:02}")
    } else {
        format!("{minutes}:{seconds:02}")
    }
}

fn number(value: Option<&Value>) -> Option<f64> {
    value.and_then(|value| {
        value
            .as_f64()
            .or_else(|| value.as_str().and_then(|text| text.parse().ok()))
    })
}

fn metadata_quality(metadata: &Value, format: &str) -> String {
    if format == "MP3" {
        return number(metadata.get("abr").or_else(|| metadata.get("tbr")))
            .map(|value| format!("{} kbps", value.round() as u64))
            .unwrap_or_else(|| "ses".into());
    }

    let direct = number(metadata.get("height"));
    let requested = metadata
        .get("requested_formats")
        .and_then(Value::as_array)
        .and_then(|formats| {
            formats
                .iter()
                .filter_map(|item| number(item.get("height")))
                .max_by(|left, right| left.total_cmp(right))
        });
    direct
        .or(requested)
        .map(|value| format!("{}p", value.round() as u64))
        .unwrap_or_else(|| "video".into())
}

fn find_thumbnail(path: &Path) -> Option<PathBuf> {
    let stem = path.file_stem()?.to_str()?;
    fs::read_dir(path.parent()?)
        .ok()?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .find(|candidate| {
            candidate.is_file()
                && candidate.file_stem().and_then(|value| value.to_str()) == Some(stem)
                && THUMBNAIL_EXTENSIONS.contains(&extension(candidate).as_str())
        })
}

fn describe_library_item(path: &Path) -> Result<Value, String> {
    let info = fs::metadata(path)
        .map_err(|error| format!("Dosya bilgisi okunamadı: {error}"))?;
    let metadata = load_metadata(path);
    let format = if matches!(extension(path).as_str(), "mp3" | "m4a") {
        "MP3"
    } else {
        "MP4"
    };
    let title = metadata
        .get("title")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .map(str::to_owned)
        .unwrap_or_else(|| {
            path.file_stem()
                .and_then(|value| value.to_str())
                .unwrap_or("media")
                .to_string()
        });
    Ok(serde_json::json!({
        "title": title,
        "format": format,
        "size": format_size(info.len()),
        "quality": metadata_quality(&metadata, format),
        "duration": format_duration(number(metadata.get("duration"))),
        "path": path.to_string_lossy(),
        "thumbnail": find_thumbnail(path).map(|value| value.to_string_lossy().into_owned()).unwrap_or_default(),
        "source_url": metadata
            .get("webpage_url")
            .or_else(|| metadata.get("original_url"))
            .and_then(Value::as_str)
            .unwrap_or_default(),
        "modified": info
            .modified()
            .ok()
            .and_then(|value| value.duration_since(UNIX_EPOCH).ok())
            .map(|value| value.as_millis())
            .unwrap_or_default(),
    }))
}

fn scan_library_folder(folder: &Path) -> Result<Value, String> {
    if !folder.exists() {
        return Ok(Value::Array(Vec::new()));
    }
    let entries: Vec<PathBuf> = fs::read_dir(folder)
        .map_err(|error| format!("Kütüphane okunamadı: {error}"))?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .collect();
    let mut media_paths = Vec::new();
    for path in entries {
        if path.is_file() && is_media(&path) {
            media_paths.push(path);
        } else if path.is_dir() {
            media_paths.extend(
                fs::read_dir(path)
                    .into_iter()
                    .flatten()
                    .filter_map(Result::ok)
                    .map(|entry| entry.path())
                    .filter(|candidate| candidate.is_file() && is_media(candidate)),
            );
        }
    }
    let mut files: Vec<(PathBuf, u128)> = media_paths
        .into_iter()
        .map(|path| {
            let modified = fs::metadata(&path)
                .and_then(|info| info.modified())
                .ok()
                .and_then(|value| value.duration_since(UNIX_EPOCH).ok())
                .map(|value| value.as_millis())
                .unwrap_or_default();
            (path, modified)
        })
        .collect();
    files.sort_by(|left, right| right.1.cmp(&left.1));
    Ok(Value::Array(
        files
            .iter()
            .filter_map(|(path, _)| describe_library_item(path).ok())
            .collect(),
    ))
}

fn resolve_library_file(folder: &Path, raw_path: &str) -> Result<PathBuf, String> {
    let root = folder
        .canonicalize()
        .map_err(|error| format!("Kütüphane yolu açılamadı: {error}"))?;
    let path = PathBuf::from(raw_path)
        .canonicalize()
        .map_err(|_| "Dosya artık mevcut değil.".to_string())?;
    if !path.starts_with(&root) || !path.is_file() || !is_media(&path) {
        return Err("Kütüphane dışındaki dosyalara işlem yapılamaz.".into());
    }
    Ok(path)
}

fn associated_files(media: &Path) -> Vec<PathBuf> {
    let mut files = vec![media.to_path_buf()];
    let Some(parent) = media.parent() else {
        return files;
    };
    let Some(stem) = media.file_stem().and_then(|value| value.to_str()) else {
        return files;
    };
    let prefix = format!("{stem}.");
    if let Ok(entries) = fs::read_dir(parent) {
        for candidate in entries.filter_map(Result::ok).map(|entry| entry.path()) {
            if candidate == media || !candidate.is_file() || is_media(&candidate) {
                continue;
            }
            let name = candidate
                .file_name()
                .and_then(|value| value.to_str())
                .unwrap_or_default();
            let candidate_extension = extension(&candidate);
            if name.starts_with(&prefix)
                && (THUMBNAIL_EXTENSIONS.contains(&candidate_extension.as_str())
                    || SIDECAR_EXTENSIONS.contains(&candidate_extension.as_str()))
            {
                files.push(candidate);
            }
        }
    }
    files
}

fn sanitize_file_stem(title: &str) -> String {
    let mut value: String = title
        .trim()
        .chars()
        .map(|character| {
            if character.is_control() || r#"<>:"/\|?*"#.contains(character) {
                '_'
            } else {
                character
            }
        })
        .take(180)
        .collect();
    value = value.trim_matches([' ', '.']).to_string();
    if value.is_empty() {
        value = "media".into();
    }
    let reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6",
        "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6",
        "LPT7", "LPT8", "LPT9",
    ];
    if reserved.contains(&value.to_uppercase().as_str()) {
        value.insert(0, '_');
    }
    value
}

fn rename_library_file(folder: &Path, raw_path: &str, title: &str) -> Result<Value, String> {
    let media = resolve_library_file(folder, raw_path)?;
    let title = title.trim();
    if title.is_empty() {
        return Err("Dosya adı boş bırakılamaz.".into());
    }
    let new_stem = sanitize_file_stem(title);
    let old_stem = media
        .file_stem()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "Dosya adı okunamadı.".to_string())?;
    let parent = media
        .parent()
        .ok_or_else(|| "Dosya klasörü bulunamadı.".to_string())?;
    let root = folder
        .canonicalize()
        .map_err(|error| format!("Kütüphane yolu açılamadı: {error}"))?;
    let parent_canonical = parent
        .canonicalize()
        .map_err(|error| format!("Medya klasörü açılamadı: {error}"))?;
    let managed_folder = parent_canonical.parent() == Some(root.as_path());

    if managed_folder {
        let target_folder = root.join(&new_stem);
        if target_folder != parent_canonical && target_folder.exists() {
            return Err("Bu adla başka bir medya klasörü zaten mevcut.".into());
        }

        let mut moves = Vec::new();
        for source in fs::read_dir(&parent_canonical)
            .map_err(|error| format!("Medya klasörü okunamadı: {error}"))?
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .filter(|path| path.is_file())
        {
            let name = source
                .file_name()
                .and_then(|value| value.to_str())
                .ok_or_else(|| "Dosya adı okunamadı.".to_string())?;
            if !name.starts_with(old_stem) {
                continue;
            }
            moves.push((
                source.clone(),
                parent_canonical.join(name.replacen(old_stem, &new_stem, 1)),
            ));
        }

        for (source, target) in &moves {
            if source != target && target.exists() {
                return Err("Bu adla başka bir dosya zaten mevcut.".into());
            }
        }

        let mut completed = Vec::new();
        for (source, target) in &moves {
            if source == target {
                continue;
            }
            if let Err(error) = fs::rename(source, target) {
                for (old, new) in completed.iter().rev() {
                    let _ = fs::rename(new, old);
                }
                return Err(format!("Dosya yeniden adlandırılamadı: {error}"));
            }
            completed.push((source.clone(), target.clone()));
        }

        if target_folder != parent_canonical {
            if let Err(error) = fs::rename(&parent_canonical, &target_folder) {
                for (old, new) in completed.iter().rev() {
                    let _ = fs::rename(new, old);
                }
                return Err(format!("Medya klasörü yeniden adlandırılamadı: {error}"));
            }
        }

        for info_path in fs::read_dir(&target_folder)
            .into_iter()
            .flatten()
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .filter(|path| path.file_name().and_then(|value| value.to_str()).is_some_and(|name| name.ends_with(".info.json")))
        {
            if let Ok(contents) = fs::read_to_string(&info_path) {
                if let Ok(mut metadata) = serde_json::from_str::<Value>(&contents) {
                    metadata["title"] = Value::String(title.to_string());
                    if let Ok(encoded) = serde_json::to_string_pretty(&metadata) {
                        let _ = fs::write(info_path, encoded);
                    }
                }
            }
        }

        let renamed_media =
            target_folder.join(format!("{new_stem}.{}", extension(&media)));
        return describe_library_item(&renamed_media);
    }

    let sources = associated_files(&media);
    let mut moves = Vec::new();
    for source in sources {
        let name = source
            .file_name()
            .and_then(|value| value.to_str())
            .ok_or_else(|| "Yan dosya adı okunamadı.".to_string())?;
        let target_name = if source == media {
            format!("{new_stem}.{}", extension(&source))
        } else {
            name.replacen(old_stem, &new_stem, 1)
        };
        let target = parent.join(target_name);
        if target != source && target.exists() {
            return Err("Bu adla başka bir dosya zaten mevcut.".into());
        }
        moves.push((source, target));
    }

    let mut completed = Vec::new();
    for (source, target) in &moves {
        if source == target {
            continue;
        }
        if let Err(error) = fs::rename(source, target) {
            for (old, new) in completed.iter().rev() {
                let _ = fs::rename(new, old);
            }
            return Err(format!("Dosya yeniden adlandırılamadı: {error}"));
        }
        completed.push((source.clone(), target.clone()));
    }

    let renamed_media = parent.join(format!("{new_stem}.{}", extension(&media)));
    let info_path = metadata_path(&renamed_media);
    let mut metadata = fs::read_to_string(&info_path)
        .ok()
        .and_then(|contents| serde_json::from_str::<Value>(&contents).ok())
        .filter(Value::is_object)
        .unwrap_or_else(|| serde_json::json!({}));
    metadata["title"] = Value::String(title.to_string());
    let encoded = serde_json::to_string_pretty(&metadata)
        .map_err(|error| format!("Metadata hazırlanamadı: {error}"))?;
    fs::write(info_path, encoded)
        .map_err(|error| format!("Başlık kaydedilemedi: {error}"))?;
    describe_library_item(&renamed_media)
}

fn delete_library_file(folder: &Path, raw_path: &str) -> Result<(), String> {
    let media = resolve_library_file(folder, raw_path)?;
    let root = folder
        .canonicalize()
        .map_err(|error| format!("Kütüphane yolu açılamadı: {error}"))?;
    let parent = media
        .parent()
        .and_then(|path| path.canonicalize().ok())
        .ok_or_else(|| "Medya klasörü bulunamadı.".to_string())?;
    if parent.parent() == Some(root.as_path()) {
        return fs::remove_dir_all(parent)
            .map_err(|error| format!("Medya klasörü silinemedi: {error}"));
    }
    for path in associated_files(&media) {
        match fs::remove_file(&path) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(format!("Dosya silinemedi: {error}")),
        }
    }
    Ok(())
}

fn backend_script() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .join("backend.py")
}

fn hidden_command(program: &str) -> Command {
    let mut command = Command::new(program);
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    command
}

fn configure_backend_command(program: &std::path::Path) -> Command {
    let mut command = hidden_command(program.to_string_lossy().as_ref());
    command
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1");
    command
}

fn backend_command(app: &AppHandle) -> Result<Command, String> {
    if let Ok(resource_dir) = app.path().resource_dir() {
        let bundled = resource_dir
            .join("binaries")
            .join("backend")
            .join("youtube-downloader-backend.exe");
        if bundled.exists() {
            return Ok(configure_backend_command(&bundled));
        }
    }

    let development_bundle = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("binaries")
        .join("backend")
        .join("youtube-downloader-backend.exe");
    if development_bundle.exists() {
        return Ok(configure_backend_command(&development_bundle));
    }

    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            let bundled = parent.join("youtube-downloader-backend.exe");
            if bundled.exists() {
                return Ok(configure_backend_command(&bundled));
            }
        }
    }

    let script = backend_script();
    if !script.exists() {
        return Err(format!("Python backend bulunamadı: {}", script.display()));
    }
    let mut command = hidden_command("python");
    command
        .arg("-u")
        .arg(script)
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1");
    Ok(command)
}

fn run_backend_json(app: &AppHandle, args: &[&str]) -> Result<Value, String> {
    let output = backend_command(app)?
        .args(args)
        .stdin(Stdio::null())
        .output()
        .map_err(|error| format!("Python başlatılamadı: {error}"))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("Backend yanıtı okunamadı: {error}"))
}

#[tauri::command]
fn get_app_state(app: AppHandle) -> Result<Value, String> {
    app_state(&app)
}

#[tauri::command]
async fn list_library() -> Result<Value, String> {
    let folder = downloads_dir()?;
    tauri::async_runtime::spawn_blocking(move || scan_library_folder(&folder))
        .await
        .map_err(|error| format!("Kütüphane görevi tamamlanamadı: {error}"))?
}

#[tauri::command]
async fn edit_library_item(path: String, title: String) -> Result<Value, String> {
    let folder = downloads_dir()?;
    tauri::async_runtime::spawn_blocking(move || rename_library_file(&folder, &path, &title))
        .await
        .map_err(|error| format!("Düzenleme görevi tamamlanamadı: {error}"))?
}

#[tauri::command]
async fn delete_library_item(path: String) -> Result<(), String> {
    let folder = downloads_dir()?;
    tauri::async_runtime::spawn_blocking(move || delete_library_file(&folder, &path))
        .await
        .map_err(|error| format!("Silme görevi tamamlanamadı: {error}"))?
}

#[tauri::command]
fn set_setting(app: AppHandle, key: String, value: Value) -> Result<Value, String> {
    let value = serde_json::to_string(&value).map_err(|error| error.to_string())?;
    run_backend_json(&app, &["set", &key, &value])
}

#[tauri::command]
fn pick_folder(app: AppHandle) -> Result<Option<String>, String> {
    let Some(folder) = rfd::FileDialog::new().pick_folder() else {
        return Ok(None);
    };
    let folder = folder.to_string_lossy().to_string();
    let value = serde_json::to_string(&folder).map_err(|error| error.to_string())?;
    run_backend_json(&app, &["set", "downloads_dir", &value])?;
    Ok(Some(folder))
}

#[tauri::command]
fn read_clipboard() -> Result<String, String> {
    arboard::Clipboard::new()
        .and_then(|mut clipboard| clipboard.get_text())
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    open::that(path).map_err(|error| error.to_string())
}

#[tauri::command]
fn open_download_folder(app: AppHandle) -> Result<(), String> {
    let state = app_state(&app)?;
    let path = state["settings"]["downloadsDir"]
        .as_str()
        .ok_or_else(|| "İndirme klasörü bulunamadı.".to_string())?;
    open::that(path).map_err(|error| error.to_string())
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    if !url.starts_with("https://") && !url.starts_with("http://") {
        return Err("Yalnızca web bağlantıları açılabilir.".into());
    }
    open::that(url).map_err(|error| error.to_string())
}

#[tauri::command]
fn download_video(
    app: AppHandle,
    state: State<'_, DownloadProcess>,
    url: String,
    format: String,
    resolution: Option<String>,
) -> Result<(), String> {
    if state.0.lock().map_err(|_| "İndirme durumu kilitlendi.")?.is_some() {
        return Err("Bir indirme zaten devam ediyor.".into());
    }

    let mut command = backend_command(&app)?;
    command
        .arg("download")
        .arg(url)
        .arg(format)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .stdin(Stdio::null());
    if let Some(resolution) = resolution {
        command.arg("--resolution").arg(resolution);
    }
    let mut child = command
        .spawn()
        .map_err(|error| format!("İndirme motoru başlatılamadı: {error}"))?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "İndirme çıktısı açılamadı.".to_string())?;
    let stderr = child.stderr.take();
    *state.0.lock().map_err(|_| "İndirme durumu kilitlendi.")? = Some(child);

    let app_for_thread = app.clone();
    thread::spawn(move || {
        let mut terminal_event_received = false;
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            let Ok(message) = serde_json::from_str::<Value>(&line) else {
                continue;
            };
            let Some(event) = message["event"].as_str() else {
                continue;
            };
            if matches!(event, "complete" | "error") {
                terminal_event_received = true;
            }
            let payload = message.get("payload").cloned().unwrap_or(Value::Null);
            let _ = app_for_thread.emit(&format!("download://{event}"), payload);
        }

        let exit_status = if let Some(process) = app_for_thread.state::<DownloadProcess>().0.lock().ok().and_then(|mut item| item.take()) {
            let mut process = process;
            process.wait().ok()
        } else {
            None
        };
        let mut stderr_text = String::new();
        if let Some(mut stderr) = stderr {
            let _ = stderr.read_to_string(&mut stderr_text);
        }
        if !terminal_event_received {
            let detail = stderr_text
                .lines()
                .find(|line| !line.trim().is_empty())
                .unwrap_or("İndirme motoru beklenmedik şekilde kapandı.");
            let message = if exit_status.is_some_and(|status| status.success()) {
                "İndirme tamamlanamadı.".to_string()
            } else {
                format!("İndirme motoru hatası: {detail}")
            };
            let _ = app_for_thread.emit(
                "download://error",
                serde_json::json!({ "message": message }),
            );
        }
        let _ = app_for_thread.emit("download://busy", false);
    });
    app.emit("download://busy", true).map_err(|error| error.to_string())
}

#[tauri::command]
fn cancel_download(state: State<'_, DownloadProcess>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|_| "İndirme durumu kilitlendi.")?;
    if let Some(process) = guard.as_mut() {
        process.kill().map_err(|error| error.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn is_download_busy(state: State<'_, DownloadProcess>) -> Result<bool, String> {
    Ok(state
        .0
        .lock()
        .map_err(|_| "İndirme durumu kilitlendi.")?
        .is_some())
}

#[tauri::command]
fn window_minimize(window: WebviewWindow) -> Result<(), String> {
    window.minimize().map_err(|error| error.to_string())
}

#[tauri::command]
fn window_toggle_maximize(window: WebviewWindow) -> Result<(), String> {
    if window.is_maximized().map_err(|error| error.to_string())? {
        window.unmaximize()
    } else {
        window.maximize()
    }
    .map_err(|error| error.to_string())
}

#[tauri::command]
fn window_close(
    window: WebviewWindow,
    state: State<'_, DownloadProcess>,
    force: bool,
) -> Result<bool, String> {
    let mut process = state
        .0
        .lock()
        .map_err(|_| "İndirme durumu kilitlendi.")?;
    let busy = process.is_some();
    if busy && !force {
        return Ok(false);
    }
    if let Some(child) = process.as_mut() {
        let _ = child.kill();
    }
    drop(process);
    window.close().map_err(|error| error.to_string())?;
    Ok(true)
}

#[tauri::command]
fn show_notification(app: AppHandle, title: String, body: String) -> Result<(), String> {
    app.notification()
        .builder()
        .title(title)
        .body(body)
        .show()
        .map_err(|error| error.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn test_folder(label: &str) -> PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!(
            "youtube-downloader-{label}-{}-{unique}",
            std::process::id()
        ))
    }

    #[test]
    fn library_edit_and_delete_move_all_sidecars() {
        let folder = test_folder("library-edit");
        let media_folder = folder.join("Old title");
        fs::create_dir_all(&media_folder).unwrap();
        let media = media_folder.join("Old title.mp3");
        let video = media_folder.join("Old title.mp4");
        let metadata = media_folder.join("Old title.info.json");
        let thumbnail = media_folder.join("Old title.webp");
        fs::write(&media, b"audio").unwrap();
        fs::write(&video, b"video").unwrap();
        fs::write(
            &metadata,
            r#"{"title":"Old title","duration":61,"abr":320}"#,
        )
        .unwrap();
        fs::write(&thumbnail, b"cover").unwrap();

        let items = scan_library_folder(&folder).unwrap();
        assert_eq!(items.as_array().unwrap().len(), 2);

        let updated =
            rename_library_file(&folder, media.to_str().unwrap(), "New / title").unwrap();
        let updated_path = PathBuf::from(updated["path"].as_str().unwrap());
        assert_eq!(updated["title"], "New / title");
        assert!(updated_path.ends_with("New _ title\\New _ title.mp3"));
        assert!(folder.join("New _ title").join("New _ title.mp4").is_file());
        assert!(folder.join("New _ title").join("New _ title.info.json").is_file());
        assert!(folder.join("New _ title").join("New _ title.webp").is_file());

        delete_library_file(&folder, updated_path.to_str().unwrap()).unwrap();
        assert!(fs::read_dir(&folder).unwrap().next().is_none());
        fs::remove_dir_all(folder).unwrap();
    }

    #[test]
    fn library_rejects_files_outside_download_folder() {
        let folder = test_folder("library-root");
        let outside = test_folder("library-outside");
        fs::create_dir_all(&folder).unwrap();
        fs::create_dir_all(&outside).unwrap();
        let media = outside.join("outside.mp3");
        fs::write(&media, b"audio").unwrap();

        let error = delete_library_file(&folder, media.to_str().unwrap()).unwrap_err();
        assert!(error.contains("Kütüphane dışındaki"));

        fs::remove_dir_all(folder).unwrap();
        fs::remove_dir_all(outside).unwrap();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(DownloadProcess(Mutex::new(None)))
        .on_window_event(|window, event| {
            // Köşe yuvarlama artık CSS ile yapılıyor; pencere büyütüldüğünde
            // yuvarlaklığı kapatmak için arayüze maksimize durumunu bildir.
            if let tauri::WindowEvent::Resized(_) = event {
                if let Ok(maximized) = window.is_maximized() {
                    let _ = window.emit("window://maximized", maximized);
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_app_state,
            list_library,
            edit_library_item,
            delete_library_item,
            set_setting,
            pick_folder,
            read_clipboard,
            open_file,
            open_download_folder,
            open_url,
            download_video,
            cancel_download,
            is_download_busy,
            window_minimize,
            window_toggle_maximize,
            window_close,
            show_notification,
        ])
        .run(tauri::generate_context!())
        .expect("Tauri uygulaması başlatılamadı");
}
