import {
  DownloadIcon,
  LibraryIcon,
  SettingsIcon,
  InfoIcon,
  GithubIcon,
} from "./icons";
import { openUrl } from "../lib/tauri";
import { useApp } from "../lib/AppContext";
import type { MessageKey } from "../lib/i18n";

export type Page = "download" | "library" | "settings" | "about";

const NAV: { id: Page; label: MessageKey; Icon: typeof DownloadIcon }[] = [
  { id: "download", label: "download", Icon: DownloadIcon },
  { id: "library", label: "library", Icon: LibraryIcon },
  { id: "settings", label: "settings", Icon: SettingsIcon },
  { id: "about", label: "about", Icon: InfoIcon },
];

export function Sidebar({
  page,
  onNavigate,
}: {
  page: Page;
  onNavigate: (page: Page) => void;
}) {
  const { ffmpegOk, tr } = useApp();
  const activeIndex = NAV.findIndex(({ id }) => id === page);
  return (
    <aside className="sidebar flex w-[244px] shrink-0 flex-col border-r border-white/5 bg-[rgba(9,9,12,0.5)] p-[18px_14px_16px]">
      <div className="mb-[14px] px-2 text-[10.5px] font-bold tracking-[1.6px] text-[#4d4d55]">
        {tr("menu")}
      </div>

      <nav className="relative flex flex-col gap-1">
        {/* Aktif gösterge: layout ölçümü yapan framer-motion yerine saf CSS
            transform — her geçişte reflow yok, sadece GPU kayması. */}
        <span
          aria-hidden
          className="pointer-events-none absolute left-[-14px] w-[3px] rounded-r-[4px]"
          style={{
            top: 12,
            height: 20,
            background: "linear-gradient(#ff5a68,#ff2740)",
            boxShadow: "0 0 12px rgba(255,40,60,.8)",
            transform: `translateY(${activeIndex * 48}px)`,
            opacity: activeIndex < 0 ? 0 : 1,
            transition: "transform .22s cubic-bezier(.4,0,.2,1)",
          }}
        />
        {NAV.map(({ id, label, Icon }) => {
          const active = page === id;
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className="relative flex h-11 items-center gap-[13px] rounded-[11px] px-[13px] text-left text-[14px] font-semibold"
              style={{
                border: "none",
                cursor: "pointer",
                color: active ? "#fff" : "#9a9aa2",
                background: active ? "rgba(255,40,60,0.09)" : "transparent",
                boxShadow: active
                  ? "inset 0 0 0 1px rgba(255,40,60,0.16)"
                  : "none",
                transition:
                  "background .2s cubic-bezier(.4,0,.2,1), color .2s, box-shadow .2s",
              }}
            >
              <Icon size={18} />
              {tr(label)}
            </button>
          );
        })}
      </nav>

      <div className="flex-1" />
      <div className="rounded-[14px] border border-white/[0.06] bg-white/[0.018] p-[13px]">
        <div className="mb-[11px] flex items-center gap-[9px]">
          <span
            className={`h-[7px] w-[7px] rounded-full ${ffmpegOk ? "bg-ok" : "bg-red-500"}`}
            style={{
              boxShadow: ffmpegOk
                ? "0 0 8px 1px rgba(34,197,94,.7)"
                : "0 0 8px 1px rgba(239,68,68,.7)",
            }}
          />
          <span className="text-[12.5px] font-semibold text-[#b9b9c2]">
            {tr(ffmpegOk ? "ffmpegReady" : "ffmpegMissing")}
          </span>
        </div>
        <button
          onClick={() => void openUrl("https://github.com/janleague")}
          className="flex h-[34px] w-full items-center gap-[9px] rounded-[9px] border border-white/[0.07] bg-white/[0.025] px-[11px] text-[12px] font-semibold text-[#9a9aa2] hover:border-line-strong hover:bg-[rgba(255,255,255,0.05)] hover:text-[#e0e0e6]"
          style={{
            cursor: "pointer",
            transition: "background .18s, color .18s, border-color .18s",
          }}
        >
          <GithubIcon size={15} />
          github.com/janleague
        </button>
      </div>
    </aside>
  );
}
