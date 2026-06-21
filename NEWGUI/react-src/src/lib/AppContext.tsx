import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { getAppState, pickFolder, setSetting, type AppSettings, type AppState } from "./tauri";
import { translator, type MessageKey } from "./i18n";

const FALLBACK: AppState = {
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

interface AppContextValue extends AppState {
  ready: boolean;
  tr: (key: MessageKey) => string;
  updateSetting: <K extends keyof AppSettings>(
    frontendKey: K,
    backendKey: string,
    value: AppSettings[K],
  ) => Promise<void>;
  chooseFolder: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AppState>(FALLBACK);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    getAppState()
      .then(setState)
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    document.documentElement.lang = state.settings.language;
    document.documentElement.classList.toggle("light", !state.settings.darkTheme);
  }, [state.settings.darkTheme, state.settings.language]);

  const updateSetting = useCallback(
    async <K extends keyof AppSettings>(
      frontendKey: K,
      backendKey: string,
      value: AppSettings[K],
    ) => {
      setState((current) => ({
        ...current,
        settings: { ...current.settings, [frontendKey]: value },
      }));
      const next = await setSetting(backendKey, value);
      if (next) setState(next);
    },
    [],
  );

  const chooseFolder = useCallback(async () => {
    const folder = await pickFolder();
    if (folder) {
      setState((current) => ({
        ...current,
        settings: { ...current.settings, downloadsDir: folder },
      }));
    }
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      ready,
      tr: translator(state.settings.language),
      updateSetting,
      chooseFolder,
    }),
    [chooseFolder, ready, state, updateSetting],
  );
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used inside AppProvider");
  return context;
}
