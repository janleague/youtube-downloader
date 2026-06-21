import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  LinkIcon,
  ClipboardIcon,
  CloseIcon,
  MusicIcon,
  VideoIcon,
  CheckIcon,
  DownloadIcon,
} from "../components/icons";
import { RESOLUTIONS } from "../data/mock";
import { readClipboard, type Format } from "../lib/tauri";
import { useDownload } from "../lib/useDownload";
import { useApp } from "../lib/AppContext";
import { buttonMotion, EASE } from "../lib/motion";

const Label = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-[11px] text-[11px] font-bold tracking-[1.5px] text-[#56565d]">
    {children}
  </div>
);

export function DownloadPage() {
  const { settings, tr, ffmpegOk } = useApp();
  const [url, setUrl] = useState("");
  const [format, setFormat] = useState<Format>(settings.defaultFormat);
  const [resolution, setResolution] = useState(settings.resolution);
  const { state, start, setMessage } = useDownload();

  useEffect(() => {
    if (!state.busy) {
      setFormat(settings.defaultFormat);
      setResolution(settings.resolution);
    }
  }, [settings.defaultFormat, settings.resolution, state.busy]);

  const complete =
    state.progress >= 100 && !state.busy && state.level === "success";
  const statusColor = {
    idle: "#9a9aa2",
    info: "#cfcfd4",
    success: "#4ade80",
    warning: "#f59e0b",
    error: "#f87171",
  }[state.level];

  async function onPaste() {
    try {
      const text = (await readClipboard())?.trim();
      if (text) setUrl(text);
      else setMessage(tr("emptyClipboard"), "warning");
    } catch {
      setMessage(tr("emptyClipboard"), "warning");
    }
  }

  return (
    <div className="max-w-[935px]">
      <h1 className="m-0 font-sora text-[29px] font-bold tracking-[-.6px] text-[#f5f5f7]">
        {tr("downloadTitle")}
      </h1>
      <p className="mt-[7px] text-[14.5px] font-medium text-[#86868e]">
        {tr("downloadSub")}
      </p>

      <div className="mt-[26px]">
        <Label>{tr("youtubeLink")}</Label>
      </div>
      <div className="flex gap-[10px]">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#6a6a72]">
            <LinkIcon size={17} />
          </span>
          <input
            value={url}
            disabled={state.busy}
            onChange={(event) => setUrl(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                void start(url, format, format === "mp4" ? resolution : null);
              }
            }}
            placeholder="https://www.youtube.com/watch?v=..."
            className="h-[54px] w-full rounded-[14px] border border-white/[0.08] bg-white/[0.03] px-11 text-[14px] font-medium text-[#f4f4f6] outline-none focus:border-[rgba(255,40,60,0.5)] focus:bg-white/[0.04] disabled:opacity-60"
            style={{ transition: "border-color .2s, box-shadow .2s, background .2s" }}
            onFocus={(event) =>
              (event.currentTarget.style.boxShadow =
                "0 0 0 4px rgba(255,40,60,.1)")
            }
            onBlur={(event) => (event.currentTarget.style.boxShadow = "none")}
          />
          {url && !state.busy && (
            <button
              onClick={() => setUrl("")}
              className="absolute right-[13px] top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-[7px] bg-white/5 text-[#86868e] hover:bg-white/10 hover:text-[#e4e4e8]"
              style={{ border: "none", cursor: "pointer" }}
            >
              <CloseIcon size={11} />
            </button>
          )}
        </div>
        <motion.button
          {...buttonMotion}
          disabled={state.busy}
          onClick={() => void onPaste()}
          className="flex h-[54px] items-center gap-[9px] rounded-[14px] border border-white/[0.08] bg-glass-2 px-5 text-[13.5px] font-semibold text-[#cfcfd4] disabled:opacity-60"
          style={{ cursor: "pointer" }}
        >
          <ClipboardIcon size={16} /> {tr("paste")}
        </motion.button>
      </div>

      <div className="mt-6">
        <Label>{tr("format")}</Label>
      </div>
      <div className="flex gap-3">
        <FormatCard
          active={format === "mp3"}
          accent="accent"
          title="MP3"
          sub={`${settings.audioQuality} kbps · ${tr("audioOnly")}`}
          Icon={MusicIcon}
          onClick={() => !state.busy && setFormat("mp3")}
        />
        <FormatCard
          active={format === "mp4"}
          accent="info"
          title="MP4"
          sub={tr("videoAudio")}
          Icon={VideoIcon}
          onClick={() => !state.busy && setFormat("mp4")}
        />
      </div>

      <AnimatePresence>
        {format === "mp4" && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22, ease: EASE }}
          >
            <div className="mt-[22px]">
              <Label>{tr("resolution")}</Label>
            </div>
            <div className="flex flex-wrap gap-2">
              {RESOLUTIONS.map((item) => {
                const selected = item === resolution;
                return (
                  <button
                    key={item}
                    disabled={state.busy}
                    onClick={() => setResolution(item)}
                    className="h-[38px] rounded-[10px] px-4 text-[13px] font-semibold disabled:opacity-60"
                    style={{
                      cursor: "pointer",
                      border: `1px solid ${
                        selected
                          ? "rgba(255,40,60,0.4)"
                          : "rgba(255,255,255,0.07)"
                      }`,
                      background: selected
                        ? "rgba(255,40,60,0.12)"
                        : "rgba(255,255,255,0.03)",
                      color: selected ? "#ff8089" : "#9a9aa2",
                      transition: "all .18s",
                    }}
                  >
                    {item === "En İyi" ? tr("best") : item}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={state.busy ? undefined : { y: -2, scale: 1.005 }}
        whileTap={state.busy ? undefined : { y: 1, scale: 0.992 }}
        transition={{ duration: 0.15, ease: EASE }}
        disabled={state.busy || (format === "mp3" && !ffmpegOk)}
        onClick={() =>
          void start(url, format, format === "mp4" ? resolution : null)
        }
        className="mt-6 flex h-14 w-full items-center justify-center gap-[10px] rounded-[14px] font-sora text-[16px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
        style={{
          border: "none",
          cursor: "pointer",
          background: "linear-gradient(135deg,#ff3a47,#e0001a)",
          boxShadow:
            "0 12px 36px -8px rgba(255,40,60,.55), inset 0 1px 0 rgba(255,255,255,.2)",
        }}
      >
        {state.busy ? (
          <span className="inline-block h-[18px] w-[18px] animate-spin rounded-full border-2 border-white/35 border-t-white" />
        ) : (
          <DownloadIcon size={19} strokeWidth={1.9} />
        )}
        {state.busy ? tr("downloading") : tr("download")}
      </motion.button>

      <div className="mt-[22px] rounded-[16px] border border-line bg-glass p-[19px_20px]">
        <div className="flex items-center gap-3">
          {state.busy ? (
            <span className="inline-block h-[15px] w-[15px] animate-spin rounded-full border-2 border-white/20 border-t-accent-light" />
          ) : (
            <span
              className="h-2 w-2 rounded-full"
              style={{
                background: statusColor,
                boxShadow: `0 0 8px ${statusColor}`,
              }}
            />
          )}
          <span className="text-[14px] font-semibold" style={{ color: statusColor }}>
            {state.status}
          </span>
          <div className="flex-1" />
          <span
            className="font-sora text-[19px] font-bold tracking-[-.3px]"
            style={{ color: complete ? "#4ade80" : "#ff5a68" }}
          >
            %{state.progress.toFixed(1)}
          </span>
        </div>
        <div className="mt-[14px] h-2 overflow-hidden rounded-[6px] bg-white/5">
          <motion.div
            className="h-full rounded-[6px]"
            style={{
              background: complete
                ? "linear-gradient(90deg,#16a34a,#4ade80)"
                : "linear-gradient(90deg,#e0001a,#ff5a68)",
              boxShadow:
                state.progress > 0
                  ? `0 0 14px ${
                      complete
                        ? "rgba(34,197,94,.55)"
                        : "rgba(255,40,60,.55)"
                    }`
                  : "none",
            }}
            animate={{ width: `${state.progress}%` }}
            transition={{ duration: 0.28, ease: EASE }}
          />
        </div>
        <div className="mt-[11px] flex justify-between text-[12px] font-medium text-[#7a7a82]">
          <span>{state.speed}</span>
          <span>{state.eta}</span>
        </div>
      </div>
    </div>
  );
}

function FormatCard({
  active,
  accent,
  title,
  sub,
  Icon,
  onClick,
}: {
  active: boolean;
  accent: "accent" | "info";
  title: string;
  sub: string;
  Icon: typeof MusicIcon;
  onClick: () => void;
}) {
  const colors =
    accent === "accent"
      ? { rgb: "255,40,60", grad: "#ff3a47,#e0001a" }
      : { rgb: "45,123,255", grad: "#3d8bff,#1456d6" };
  return (
    <motion.button
      whileHover={{ y: -1 }}
      onClick={onClick}
      className="relative flex flex-1 items-center gap-[14px] rounded-[15px] p-[17px] text-left"
      style={{
        cursor: "pointer",
        border: `1px solid ${
          active
            ? `rgba(${colors.rgb},0.45)`
            : "rgba(255,255,255,0.07)"
        }`,
        background: active
          ? `rgba(${colors.rgb},0.07)`
          : "rgba(255,255,255,0.022)",
        boxShadow: active
          ? `inset 0 0 0 1px rgba(${colors.rgb},0.2), 0 10px 34px -12px rgba(${colors.rgb},0.4)`
          : "none",
        transition: "all .2s cubic-bezier(.4,0,.2,1)",
      }}
    >
      <span
        className="flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-[12px] text-white"
        style={{
          background: active
            ? `linear-gradient(150deg,${colors.grad})`
            : "rgba(255,255,255,0.06)",
          boxShadow: active
            ? `0 6px 18px -4px rgba(${colors.rgb},0.6)`
            : "none",
        }}
      >
        <Icon size={20} />
      </span>
      <span className="flex flex-col gap-[3px]">
        <span className="font-sora text-[16px] font-bold text-[#f4f4f6]">
          {title}
        </span>
        <span className="text-[12.5px] font-medium text-[#86868e]">{sub}</span>
      </span>
      {active && (
        <span
          className="absolute right-[13px] top-[13px] flex h-5 w-5 items-center justify-center rounded-full"
          style={{
            background: `linear-gradient(135deg,${colors.grad})`,
            boxShadow: `0 2px 8px rgba(${colors.rgb},0.5)`,
          }}
        >
          <CheckIcon size={11} className="text-white" />
        </span>
      )}
    </motion.button>
  );
}
