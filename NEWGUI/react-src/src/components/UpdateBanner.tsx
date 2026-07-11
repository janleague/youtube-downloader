import { useEffect, useState } from "react";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import { BrandMark, CloseIcon, DownloadIcon } from "./icons";
import { isTauri } from "../lib/tauri";
import { useApp } from "../lib/AppContext";

type AvailableUpdate = Awaited<ReturnType<typeof check>>;

export function UpdateBanner() {
  const { settings } = useApp();
  const [update, setUpdate] = useState<AvailableUpdate>(null);
  const [downloaded, setDownloaded] = useState(0);
  const [total, setTotal] = useState(0);
  const [installing, setInstalling] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!isTauri()) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void check({ timeout: 12_000 })
        .then((next) => {
          if (!cancelled) setUpdate(next);
        })
        .catch(() => undefined);
    }, 900);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  if (!update || dismissed) return null;

  const availableUpdate = update;
  const turkish = settings.language === "tr";
  const percent = total > 0 ? Math.min(100, Math.round((downloaded / total) * 100)) : 0;

  async function installUpdate() {
    setInstalling(true);
    setFailed(false);
    try {
      await availableUpdate.downloadAndInstall((event) => {
        if (event.event === "Started") setTotal(event.data.contentLength ?? 0);
        if (event.event === "Progress") {
          setDownloaded((value) => value + (event.data.chunkLength ?? 0));
        }
      }, { timeout: 120_000 });
      await relaunch();
    } catch {
      setInstalling(false);
      setFailed(true);
    }
  }

  const detail = failed
    ? (turkish ? "G\u00fcncelleme do\u011frulanamad\u0131. Daha sonra yeniden deneyin." : "The update could not be verified. Try again later.")
    : installing
      ? (turkish ? `\u0130mzalanm\u0131\u015f paket indiriliyor${total ? ` %${percent}` : ""}` : `Downloading signed package${total ? ` ${percent}%` : ""}`)
      : (turkish ? "GitHub Release'den g\u00fcvenle y\u00fcklenecek." : "It will be installed securely from GitHub Releases.");

  return (
    <div className="relative mx-[40px] mt-4 flex min-h-[54px] items-center gap-3 rounded-[8px] border border-[#ff3044]/35 bg-[#270b10] px-4 py-2.5 shadow-[0_10px_30px_rgba(0,0,0,.22)]">
      <BrandMark size={25} radius={7} />
      <div className="min-w-0 flex-1">
        <div className="text-[12.5px] font-bold text-[#f4f4f6]">
          {turkish ? `v${update.version} g\u00fcncellemesi haz\u0131r` : `Update v${update.version} is ready`}
        </div>
        <div className="mt-0.5 text-[11.5px] font-medium text-[#b9a1a5]">{detail}</div>
        {installing && total > 0 && (
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/10">
            <div className="h-full bg-[#ff3044] transition-[width] duration-150" style={{ width: `${percent}%` }} />
          </div>
        )}
      </div>
      <button
        onClick={() => void installUpdate()}
        disabled={installing}
        className="flex h-[32px] shrink-0 items-center gap-2 rounded-[6px] bg-[#ff1831] px-3 text-[11.5px] font-bold text-white disabled:cursor-wait disabled:opacity-70"
        style={{ cursor: installing ? "wait" : "pointer" }}
      >
        <DownloadIcon size={14} />
        {installing ? (turkish ? "Y\u00fckleniyor" : "Installing") : (turkish ? "Y\u00fckle" : "Install")}
      </button>
      {!installing && (
        <button
          onClick={() => setDismissed(true)}
          aria-label={turkish ? "G\u00fcncellemeyi kapat" : "Dismiss update"}
          title={turkish ? "G\u00fcncellemeyi kapat" : "Dismiss update"}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[6px] text-[#b9a1a5] hover:bg-white/10 hover:text-white"
          style={{ cursor: "pointer" }}
        >
          <CloseIcon size={12} />
        </button>
      )}
    </div>
  );
}
