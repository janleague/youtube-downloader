import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { listen } from "@tauri-apps/api/event";
import {
  cancelDownload,
  isTauri,
  showNotification,
  startDownload,
  type DownloadProgress,
  type Format,
} from "./tauri";
import { useApp } from "./AppContext";

type Level = "idle" | "info" | "success" | "warning" | "error";

export interface DownloadState {
  busy: boolean;
  progress: number;
  status: string;
  level: Level;
  speed: string;
  eta: string;
}

interface StatusPayload {
  message: string;
  level: Level;
}

interface CompletePayload {
  filepath: string;
  title: string;
}

interface ErrorPayload {
  message: string;
}

interface DownloadContextValue {
  state: DownloadState;
  completedVersion: number;
  start: (url: string, format: Format, resolution: string | null) => Promise<void>;
  cancel: () => Promise<void>;
  setMessage: (message: string, level?: Level) => void;
}

const DownloadContext = createContext<DownloadContextValue | null>(null);

export function DownloadProvider({ children }: { children: React.ReactNode }) {
  const { settings, tr } = useApp();
  const [completedVersion, setCompletedVersion] = useState(0);
  const [state, setState] = useState<DownloadState>({
    busy: false,
    progress: 0,
    status: tr("ready"),
    level: "idle",
    speed: "",
    eta: "",
  });

  useEffect(() => {
    if (!state.busy && state.progress === 0 && state.level === "idle") {
      setState((current) => ({ ...current, status: tr("ready") }));
    }
  }, [state.busy, state.level, state.progress, tr]);

  useEffect(() => {
    if (!isTauri()) return;
    const unlisteners = Promise.all([
      listen<DownloadProgress>("download://progress", ({ payload }) => {
        setState((current) => ({
          ...current,
          busy: true,
          progress: payload.pct,
          speed: payload.speed,
          eta: payload.eta,
        }));
      }),
      listen<StatusPayload>("download://status", ({ payload }) => {
        setState((current) => ({
          ...current,
          busy: true,
          status: payload.message,
          level: payload.level,
        }));
      }),
      listen<CompletePayload>("download://complete", ({ payload }) => {
        setState({
          busy: false,
          progress: 100,
          status: tr("done"),
          level: "success",
          speed: "",
          eta: "100%",
        });
        setCompletedVersion((version) => version + 1);
        if (settings.notifications) {
          void showNotification(tr("notificationDone"), payload.title);
        }
      }),
      listen<ErrorPayload>("download://error", ({ payload }) => {
        setState({
          busy: false,
          progress: 0,
          status: payload.message,
          level: "error",
          speed: "",
          eta: "",
        });
        if (settings.notifications) {
          void showNotification(tr("notificationError"), payload.message);
        }
      }),
      listen<boolean>("download://busy", ({ payload }) => {
        if (!payload) {
          setState((current) =>
            current.busy
              ? {
                  ...current,
                  busy: false,
                  status:
                    current.status === tr("connecting")
                      ? tr("notificationError")
                      : current.status,
                  level:
                    current.status === tr("connecting")
                      ? "error"
                      : current.level,
                }
              : current,
          );
        }
      }),
    ]);
    return () => {
      void unlisteners.then((items) => items.forEach((unlisten) => unlisten()));
    };
  }, [settings.notifications, tr]);

  const setMessage = useCallback((message: string, level: Level = "info") => {
    setState((current) => ({ ...current, status: message, level }));
  }, []);

  const start = useCallback(
    async (url: string, format: Format, resolution: string | null) => {
      if (state.busy) return;
      if (!/^https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\//i.test(url.trim())) {
        setMessage(tr("invalidUrl"), "warning");
        return;
      }
      setState({
        busy: true,
        progress: 0,
        status: tr("connecting"),
        level: "info",
        speed: "",
        eta: "",
      });
      try {
        await startDownload(url.trim(), format, resolution);
      } catch (error) {
        setState({
          busy: false,
          progress: 0,
          status: String(error),
          level: "error",
          speed: "",
          eta: "",
        });
      }
    },
    [setMessage, state.busy, tr],
  );

  const cancel = useCallback(async () => {
    await cancelDownload();
    setState({
      busy: false,
      progress: 0,
      status: tr("cancelled"),
      level: "warning",
      speed: "",
      eta: "",
    });
  }, [tr]);

  const value = useMemo(
    () => ({ state, completedVersion, start, cancel, setMessage }),
    [cancel, completedVersion, setMessage, start, state],
  );
  return <DownloadContext.Provider value={value}>{children}</DownloadContext.Provider>;
}

export function useDownload() {
  const context = useContext(DownloadContext);
  if (!context) throw new Error("useDownload must be used inside DownloadProvider");
  return context;
}
