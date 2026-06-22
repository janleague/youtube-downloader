import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  CloseIcon,
  EditIcon,
  FolderIcon,
  MusicIcon,
  PlayIcon,
  RefreshIcon,
  SearchIcon,
  TrashIcon,
} from "../components/icons";
import {
  deleteLibraryItem,
  editLibraryItem,
  listLibrary,
  openDownloadFolder,
  openFile,
  thumbnailUrl,
  type LibraryItem,
} from "../lib/tauri";
import { EASE } from "../lib/motion";
import { useApp } from "../lib/AppContext";
import { useDownload } from "../lib/useDownload";
import type { MessageKey } from "../lib/i18n";

const librarySignature = (items: LibraryItem[]) =>
  items
    .map(
      (item) =>
        `${item.path}\u0000${item.title}\u0000${item.size}\u0000${item.modified ?? 0}\u0000${item.thumbnail ?? ""}`,
    )
    .join("\u0001");

export function LibraryPage() {
  const { tr } = useApp();
  const { completedVersion } = useDownload();
  const [query, setQuery] = useState("");
  const [library, setLibrary] = useState<LibraryItem[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [editing, setEditing] = useState<LibraryItem | null>(null);
  const [deleting, setDeleting] = useState<LibraryItem | null>(null);
  const signatureRef = useRef("");
  const refreshRunning = useRef(false);

  const refresh = useCallback(async (visible = false) => {
    if (refreshRunning.current) return;
    refreshRunning.current = true;
    if (visible) setSyncing(true);
    try {
      const next = await listLibrary();
      const signature = librarySignature(next);
      if (signature !== signatureRef.current) {
        signatureRef.current = signature;
        setLibrary(next);
      }
    } catch {
      // Geçici dosya kilitlerinde mevcut listeyi koru; sonraki tur yeniden dener.
    } finally {
      refreshRunning.current = false;
      if (visible) setSyncing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 3500);
    const onFocus = () => void refresh();
    const onVisibility = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh]);

  useEffect(() => {
    if (completedVersion > 0) void refresh();
  }, [completedVersion, refresh]);

  const items = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return library.filter(
      (item) => !needle || item.title.toLowerCase().includes(needle),
    );
  }, [library, query]);

  const replaceItem = useCallback((previousPath: string, next: LibraryItem) => {
    setLibrary((current) => {
      const updated = current.map((item) =>
        item.path === previousPath ? next : item,
      );
      signatureRef.current = librarySignature(updated);
      return updated;
    });
  }, []);

  const removeItem = useCallback((path: string) => {
    setLibrary((current) => {
      const updated = current.filter((item) => item.path !== path);
      signatureRef.current = librarySignature(updated);
      return updated;
    });
  }, []);

  return (
    <div>
      <div className="flex items-end justify-between gap-[18px]">
        <div>
          <h1 className="m-0 font-sora text-[29px] font-bold tracking-[-.6px] text-[#f5f5f7]">
            {tr("libraryTitle")}
          </h1>
          <div className="mt-[7px] flex items-center gap-2">
            <p className="m-0 text-[14.5px] font-medium text-[#86868e]">
              {tr("librarySub")}
            </p>
            <span className="h-1 w-1 rounded-full bg-[#45454d]" />
            <span className="flex items-center gap-[6px] text-[11.5px] font-semibold text-[#4f9d72]">
              <span className="h-[6px] w-[6px] rounded-full bg-[#27d980] shadow-[0_0_8px_rgba(39,217,128,.65)]" />
              {tr("librarySynced")}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-[10px]">
          <button
            onClick={() => void refresh(true)}
            className="flex h-[42px] w-[42px] items-center justify-center rounded-[11px] border border-white/[0.08] bg-glass-2 text-[#a8a8af] hover:border-line-strong hover:bg-[rgba(255,255,255,0.07)] hover:text-white"
            style={{ cursor: "pointer", transition: "all .18s" }}
            title={tr("librarySynced")}
          >
            <span className={syncing ? "library-spin" : ""}>
              <RefreshIcon size={16} />
            </span>
          </button>
          <button
            onClick={() => void openDownloadFolder()}
            className="flex h-[42px] items-center gap-2 rounded-[11px] border border-white/[0.08] bg-glass-2 px-[15px] text-[12.5px] font-semibold text-[#cfcfd4] hover:border-line-strong hover:bg-[rgba(255,255,255,0.07)]"
            style={{ cursor: "pointer", transition: "all .18s" }}
          >
            <FolderIcon size={16} /> {tr("openFolder")}
          </button>
          <div className="relative w-[218px]">
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
            <Card
              key={item.path}
              item={item}
              index={index}
              tr={tr}
              onEdit={() => setEditing(item)}
              onDelete={() => setDeleting(item)}
            />
          ))}
        </div>
      )}

      <AnimatePresence>
        {editing && (
          <EditDialog
            key="edit"
            item={editing}
            tr={tr}
            onClose={() => setEditing(null)}
            onSaved={(next) => {
              replaceItem(editing.path, next);
              setEditing(null);
            }}
          />
        )}
        {deleting && (
          <DeleteDialog
            key="delete"
            item={deleting}
            tr={tr}
            onClose={() => setDeleting(null)}
            onDeleted={() => {
              removeItem(deleting.path);
              setDeleting(null);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function Card({
  item,
  index,
  tr,
  onEdit,
  onDelete,
}: {
  item: LibraryItem;
  index: number;
  tr: (key: MessageKey) => string;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const isMp3 = item.format === "MP3";
  const rgb = isMp3 ? "255,40,60" : "45,123,255";
  const thumbnail = thumbnailUrl(item.thumbnail);
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.2,
        ease: EASE,
        delay: Math.min(index, 8) * 0.018,
      }}
      whileHover={{ y: -3 }}
      onDoubleClick={() => void openFile(item.path)}
      className="library-card group overflow-hidden rounded-[15px] border border-line bg-glass"
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
        <div className="absolute right-[8px] top-[8px] flex gap-[6px] opacity-0 translate-y-[-2px] transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
          <CardAction
            title={tr("editFile")}
            onClick={onEdit}
            icon={<EditIcon size={14} />}
          />
          <CardAction
            title={tr("deleteFile")}
            onClick={onDelete}
            danger
            icon={<TrashIcon size={14} />}
          />
        </div>
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

function CardAction({
  title,
  icon,
  danger = false,
  onClick,
}: {
  title: string;
  icon: React.ReactNode;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      title={title}
      onDoubleClick={(event) => event.stopPropagation()}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      className={`flex h-[30px] w-[30px] items-center justify-center rounded-[8px] border backdrop-blur-md ${
        danger
          ? "border-red-400/20 bg-red-500/15 text-red-300 hover:bg-red-500/30"
          : "border-white/10 bg-black/55 text-white/80 hover:bg-black/80 hover:text-white"
      }`}
      style={{ cursor: "pointer", transition: "all .18s" }}
    >
      {icon}
    </button>
  );
}

function DialogFrame({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.16 }}
      onMouseDown={onClose}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/65 p-6 backdrop-blur-[7px]"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.97, y: 6 }}
        transition={{ duration: 0.2, ease: EASE }}
        onMouseDown={(event) => event.stopPropagation()}
        className="w-full max-w-[460px] overflow-hidden rounded-[18px] border border-white/[0.09] bg-[#111115] shadow-[0_30px_90px_rgba(0,0,0,.65)]"
      >
        {children}
      </motion.div>
    </motion.div>,
    document.body,
  );
}

function EditDialog({
  item,
  tr,
  onClose,
  onSaved,
}: {
  item: LibraryItem;
  tr: (key: MessageKey) => string;
  onClose: () => void;
  onSaved: (item: LibraryItem) => void;
}) {
  const [title, setTitle] = useState(item.title);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    if (busy || !title.trim()) return;
    setBusy(true);
    setError("");
    try {
      onSaved(await editLibraryItem(item.path, title.trim()));
    } catch (cause) {
      setError(String(cause));
      setBusy(false);
    }
  };

  return (
    <DialogFrame onClose={busy ? () => {} : onClose}>
      <div className="flex items-start justify-between border-b border-white/[0.06] p-[22px_22px_18px]">
        <div>
          <h2 className="m-0 font-sora text-[18px] font-bold text-white">
            {tr("editFile")}
          </h2>
          <p className="mb-0 mt-[5px] text-[12.5px] font-medium text-[#777780]">
            {tr("editFileSub")}
          </p>
        </div>
        <button
          onClick={onClose}
          disabled={busy}
          className="flex h-8 w-8 items-center justify-center rounded-[8px] text-[#777780] hover:bg-white/[0.06] hover:text-white"
          style={{ cursor: busy ? "default" : "pointer", transition: "all .18s" }}
        >
          <CloseIcon size={15} />
        </button>
      </div>
      <div className="p-[20px_22px_22px]">
        <label className="mb-[8px] block text-[10px] font-bold tracking-[1.3px] text-[#62626b]">
          {tr("fileName")}
        </label>
        <input
          autoFocus
          value={title}
          maxLength={180}
          disabled={busy}
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void save();
          }}
          className="h-[48px] w-full rounded-[11px] border border-white/[0.09] bg-black/20 px-[14px] text-[13.5px] font-semibold text-white outline-none focus:border-[rgba(255,40,60,.55)] focus:shadow-[0_0_0_3px_rgba(255,40,60,.08)]"
          style={{ transition: "border-color .18s, box-shadow .18s" }}
        />
        <p className="mt-[9px] truncate text-[11px] font-medium text-[#55555e]">
          {item.path}
        </p>
        {error && (
          <div className="mt-3 rounded-[9px] border border-red-500/20 bg-red-500/10 px-3 py-2 text-[11.5px] font-semibold text-red-300">
            {error}
          </div>
        )}
        <div className="mt-5 flex justify-end gap-[9px]">
          <DialogButton onClick={onClose} disabled={busy}>
            {tr("cancel")}
          </DialogButton>
          <DialogButton
            primary
            onClick={() => void save()}
            disabled={busy || !title.trim()}
          >
            {busy ? tr("saving") : tr("save")}
          </DialogButton>
        </div>
      </div>
    </DialogFrame>
  );
}

function DeleteDialog({
  item,
  tr,
  onClose,
  onDeleted,
}: {
  item: LibraryItem;
  tr: (key: MessageKey) => string;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const remove = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await deleteLibraryItem(item.path);
      onDeleted();
    } catch (cause) {
      setError(String(cause));
      setBusy(false);
    }
  };

  return (
    <DialogFrame onClose={busy ? () => {} : onClose}>
      <div className="p-[22px]">
        <div className="flex h-[44px] w-[44px] items-center justify-center rounded-[12px] border border-red-400/20 bg-red-500/10 text-red-300">
          <TrashIcon size={19} />
        </div>
        <h2 className="mb-0 mt-4 font-sora text-[18px] font-bold text-white">
          {tr("deleteFile")}
        </h2>
        <p className="mb-0 mt-2 text-[13px] font-medium leading-[1.55] text-[#85858e]">
          {tr("deleteConfirm")}
        </p>
        <div className="mt-4 rounded-[10px] border border-white/[0.06] bg-black/20 px-3 py-[10px] text-[12px] font-semibold text-[#d1d1d5]">
          {item.title}
        </div>
        {error && (
          <div className="mt-3 rounded-[9px] border border-red-500/20 bg-red-500/10 px-3 py-2 text-[11.5px] font-semibold text-red-300">
            {error}
          </div>
        )}
        <div className="mt-5 flex justify-end gap-[9px]">
          <DialogButton onClick={onClose} disabled={busy}>
            {tr("cancel")}
          </DialogButton>
          <DialogButton
            danger
            onClick={() => void remove()}
            disabled={busy}
          >
            {busy ? tr("deleting") : tr("delete")}
          </DialogButton>
        </div>
      </div>
    </DialogFrame>
  );
}

function DialogButton({
  children,
  onClick,
  disabled,
  primary = false,
  danger = false,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  primary?: boolean;
  danger?: boolean;
}) {
  const color = danger
    ? "border-red-400/20 bg-red-500/90 text-white shadow-[0_7px_20px_rgba(255,40,60,.18)] hover:bg-red-500"
    : primary
      ? "border-red-400/20 bg-gradient-to-r from-[#ff3447] to-[#ef001e] text-white shadow-[0_7px_20px_rgba(255,40,60,.18)]"
      : "border-white/[0.08] bg-white/[0.04] text-[#b8b8bf] hover:bg-white/[0.07] hover:text-white";
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`h-[39px] min-w-[92px] rounded-[10px] border px-4 text-[12.5px] font-bold ${color} disabled:cursor-not-allowed disabled:opacity-50`}
      style={{ cursor: disabled ? "not-allowed" : "pointer", transition: "all .18s" }}
    >
      {children}
    </button>
  );
}
