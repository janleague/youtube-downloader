import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { TitleBar } from "./components/TitleBar";
import { Sidebar, type Page } from "./components/Sidebar";
import { DownloadPage } from "./pages/DownloadPage";
import { LibraryPage } from "./pages/LibraryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AboutPage } from "./pages/AboutPage";
import { pageVariants } from "./lib/motion";
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
    <div className="app-stage h-full w-full bg-transparent">
      <div
        className="app-shell flex h-full w-full flex-col overflow-hidden rounded-[18px] border border-white/[0.08] bg-ink-850"
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
                filter: "blur(8px)",
              }}
            />
            <div className="relative z-10 min-h-0 flex-1 overflow-y-auto p-[34px_40px_44px]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={page}
                  variants={pageVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                >
                  <ActivePage page={page} />
                </motion.div>
              </AnimatePresence>
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
