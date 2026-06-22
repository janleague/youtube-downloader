import { convertFileSrc, invoke } from "@tauri-apps/api/core";

export type Format = "mp3" | "mp4";
export type Language = "tr" | "en";

export interface AppSettings {
  downloadsDir: string;
  defaultFormat: Format;
  resolution: string;
  audioQuality: string;
  language: Language;
  notifications: boolean;
  darkTheme: boolean;
}

export interface AppState {
  settings: AppSettings;
  ffmpegOk: boolean;
}

export interface DownloadProgress {
  pct: number;
  speed: string;
  eta: string;
}

export interface LibraryItem {
  title: string;
  format: "MP3" | "MP4";
  size: string;
  quality: string;
  duration: string;
  path: string;
  thumbnail?: string;
  source_url?: string;
  modified?: number;
}

const FALLBACK_STATE: AppState = {
  settings: {
    downloadsDir: "",
    defaultFormat: "mp3",
    resolution: "1080p",
    audioQuality: "320",
    language: "tr",
    notifications: true,
    darkTheme: true,
  },
  ffmpegOk: false,
};

export const isTauri = () =>
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export async function safeInvoke<T>(
  command: string,
  args?: Record<string, unknown>,
): Promise<T> {
  if (!isTauri()) {
    console.info("[browser preview]", command, args ?? {});
    return undefined as T;
  }
  return invoke<T>(command, args);
}

export async function getAppState(): Promise<AppState> {
  return (await safeInvoke<AppState>("get_app_state")) ?? FALLBACK_STATE;
}

export async function startDownload(
  url: string,
  format: Format,
  resolution: string | null,
) {
  return safeInvoke<void>("download_video", { url, format, resolution });
}

export const cancelDownload = () => safeInvoke<void>("cancel_download");
export const readClipboard = () => safeInvoke<string>("read_clipboard");
export const listLibrary = async () =>
  (await safeInvoke<LibraryItem[]>("list_library")) ?? [];
export const editLibraryItem = (path: string, title: string) =>
  safeInvoke<LibraryItem>("edit_library_item", { path, title });
export const deleteLibraryItem = (path: string) =>
  safeInvoke<void>("delete_library_item", { path });
export const openFile = (path: string) => safeInvoke<void>("open_file", { path });
export const openDownloadFolder = () => safeInvoke<void>("open_download_folder");
export const pickFolder = () => safeInvoke<string | null>("pick_folder");

export const setSetting = (key: string, value: unknown) =>
  safeInvoke<AppState>("set_setting", { key, value });

export const openUrl = (url: string) => safeInvoke<void>("open_url", { url });
export const windowMinimize = () => safeInvoke<void>("window_minimize");
export const windowToggleMaximize = () =>
  safeInvoke<void>("window_toggle_maximize");
export const windowClose = (force = false) =>
  safeInvoke<boolean>("window_close", { force });
export const showNotification = (title: string, body: string) =>
  safeInvoke<void>("show_notification", { title, body });

export function thumbnailUrl(path?: string) {
  if (!path || !isTauri()) return "";
  return convertFileSrc(path);
}
