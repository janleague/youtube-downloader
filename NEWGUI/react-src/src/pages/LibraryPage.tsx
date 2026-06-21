import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  SearchIcon,
  FolderIcon,
  MusicIcon,
  PlayIcon,
} from "../components/icons";
import {
  listLibrary,
  openDownloadFolder,
  openFile,
  thumbnailUrl,
  type LibraryItem,
} from "../lib/tauri";
import { EASE } from "../lib/motion";
import { useApp } from "../lib/AppContext";
import { useDownload } from "../lib/useDownload";

export function LibraryPage() {
  const { tr } = useApp();
  const { completedVersion } = useDownload();
  const [query, setQuery] = useState("");
  const [library, setLibrary] = useState<LibraryItem[]>([]);

  useEffect(() => {
    void listLibrary().then(setLibrary);
  }, [completedVersion]);

  const items = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return library.filter(
      (item) => !needle || item.title.toLowerCase().includes(needle),
    );
  }, [library, query]);

  return (
    <div>
      <div className="flex items-end justify-between gap-[18px]">
        <div>
          <h1 className="m-0 font-sora text-[29px] font-bold tracking-[-.6px] text-[#f5f5f7]">
            {tr("libraryTitle")}
          </h1>
          <p className="mt-[7px] text-[14.5px] font-medium text-[#86868e]">
            {tr("librarySub")}
          </p>
        </div>
        <div className="flex items-center gap-[10px]">
          <button
            onClick={() => void openDownloadFolder()}
            className="flex h-[42px] items-center gap-2 rounded-[11px] border border-white/[0.08] bg-glass-2 px-[15px] text-[12.5px] font-semibold text-[#cfcfd4] hover:border-line-strong hover:bg-[rgba(255,255,255,0.07)]"
            style={{ cursor: "pointer", transition: "all .18s" }}
          >
            <FolderIcon size={16} /> {tr("openFolder")}
          </button>
          <div className="relative w-[238px]">
            <span className="pointer-events-none absolute left-[13px] top-1/2 -translate-y-1/2 text-[#6a6a72]">
              <SearchIcon size={15} />
            </span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={tr("search")}
              className="h-[42px] w-full rounded-[11px] border border-white/[0.08] bg-white/[0.03] pl-[38px] pr-[14px] text-[13px] font-medium text-[#f4f4f6] outline-none focus:border-[rgba(255,40,60,0.5)]"
              style={{ transition: "border-color .2s" }}
            />
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="mt-[60px] flex flex-col items-center gap-3 text-[#56565d]">
          <SearchIcon size={34} strokeWidth={1.4} />
          <span className="text-[13.5px] font-medium">
            {query ? tr("noMatch") : tr("emptyLibrary")}
          </span>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-3 gap-[14px]">
          {items.map((item, index) => (
            <Card key={item.path} item={item} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}

function Card({ item, index }: { item: LibraryItem; index: number }) {
  const isMp3 = item.format === "MP3";
  const rgb = isMp3 ? "255,40,60" : "45,123,255";
  const thumbnail = thumbnailUrl(item.thumbnail);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: EASE, delay: index * 0.03 }}
      whileHover={{ y: -4 }}
      onDoubleClick={() => void openFile(item.path)}
      className="overflow-hidden rounded-[15px] border border-line bg-glass"
      style={{
        cursor: "pointer",
        transition: "border-color .22s, box-shadow .22s",
      }}
      title={item.path}
    >
      <div
        className="relative flex h-[104px] items-center justify-center bg-cover bg-center"
        style={{
          backgroundImage: thumbnail
            ? `url("${thumbnail}")`
            : "repeating-linear-gradient(125deg,#16161c 0 12px,#101015 12px 24px)",
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            background: thumbnail
              ? "linear-gradient(180deg, rgba(0,0,0,.02) 35%, rgba(0,0,0,.5))"
              : `radial-gradient(closest-side at 35% 30%, rgba(${rgb},0.16), rgba(0,0,0,0))`,
          }}
        />
        <span
          className="relative flex h-[34px] w-[34px] items-center justify-center rounded-full border border-white/[0.16] text-white"
          style={{ background: "rgba(0,0,0,.62)" }}
        >
          {isMp3 ? (
            <MusicIcon size={15} strokeWidth={1.9} />
          ) : (
            <PlayIcon size={13} color="#fff" />
          )}
        </span>
        <span
          className="absolute left-[9px] top-[9px] rounded-[6px] px-[7px] py-[2px] text-[10px] font-bold tracking-[.4px] text-white"
          style={{
            background: `linear-gradient(135deg,${
              isMp3 ? "#ff3a47,#e0001a" : "#3d8bff,#1456d6"
            })`,
            boxShadow: `0 2px 8px rgba(${rgb},0.5)`,
          }}
        >
          {item.format}
        </span>
        {item.duration && (
          <span className="absolute bottom-2 right-[9px] rounded-[5px] bg-black/60 px-[6px] py-[1px] text-[10px] font-bold text-white">
            {item.duration}
          </span>
        )}
      </div>
      <div className="p-[12px_13px_13px]">
        <div className="line-clamp-2 h-9 text-[13px] font-semibold leading-[1.35] text-[#e7e7ea]">
          {item.title}
        </div>
        <div className="mt-2 text-[11.5px] font-medium text-[#6a6a72]">
          {item.size} · {item.quality}
        </div>
      </div>
    </motion.div>
  );
}
