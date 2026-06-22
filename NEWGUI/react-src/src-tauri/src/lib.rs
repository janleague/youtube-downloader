use std::{
    collections::HashMap,
    fs,
    io::{BufRead, BufReader, Read},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
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
fn list_library(app: AppHandle) -> Result<Value, String> {
    run_backend_json(&app, &["library"])
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
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
