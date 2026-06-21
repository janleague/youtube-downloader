import { useState } from "react";
import { TitleBar } from "./components/TitleBar";
import { Sidebar, type Page } from "./components/Sidebar";
import { DownloadPage } from "./pages/DownloadPage";
import { LibraryPage } from "./pages/LibraryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AboutPage } from "./pages/AboutPage";
import { AppProvider } from "./lib/AppContext";
import { DownloadProvider } from "./lib/useDownload";

function ActivePage({ page }: { page: Page }) {
  if (page === "library") return <LibraryPage />;
  if (page === "settings") return <SettingsPage />;
  if (page === "about") return <AboutPage />;
  return <DownloadPage />;
}

function Shell() {
  const [page, setPage] = useState<Page>("download");
  return (
    <div className="app-stage h-full w-full bg-ink-850">
      <div
        className="app-shell flex h-full w-full flex-col overflow-hidden bg-ink-850"
      >
        <TitleBar />
        <div className="flex min-h-0 flex-1">
          <Sidebar page={page} onNavigate={setPage} />
          <main className="app-content relative flex min-w-0 flex-1 flex-col bg-ink-900">
            <div
              className="pointer-events-none absolute -right-[60px] -top-[80px] h-[280px] w-[380px]"
              style={{
                background:
                  "radial-gradient(closest-side, rgba(255,40,60,.10), rgba(255,40,60,0))",
              }}
            />
            <div className="relative z-10 min-h-0 flex-1 overflow-y-auto p-[34px_40px_44px]">
              <div key={page} className="page-enter">
                <ActivePage page={page} />
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <DownloadProvider>
        <Shell />
      </DownloadProvider>
    </AppProvider>
  );
}
