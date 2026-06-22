/** Tek satırlık, tutarlı SVG ikon seti (stroke = currentColor). */
import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement> & { size?: number };
const base = (p: P) => ({
  width: p.size ?? 18, height: p.size ?? 18, viewBox: "0 0 24 24",
  fill: "none", stroke: "currentColor", strokeWidth: 1.7,
  strokeLinecap: "round" as const, strokeLinejoin: "round" as const, ...p,
});

export const DownloadIcon = (p: P) => (
  <svg {...base(p)}><path d="M12 3v12" /><path d="m7 11 5 5 5-5" /><path d="M5 20h14" /></svg>
);
export const LibraryIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.7}>
    <rect x="3" y="3" width="7.2" height="7.2" rx="1.6" /><rect x="13.8" y="3" width="7.2" height="7.2" rx="1.6" />
    <rect x="3" y="13.8" width="7.2" height="7.2" rx="1.6" /><rect x="13.8" y="13.8" width="7.2" height="7.2" rx="1.6" />
  </svg>
);
export const SettingsIcon = (p: P) => (
  <svg {...base(p)}>
    <line x1="4" y1="7.5" x2="20" y2="7.5" /><line x1="4" y1="16.5" x2="20" y2="16.5" />
    <circle cx="15.5" cy="7.5" r="2.6" fill="#0a0a0d" /><circle cx="8.5" cy="16.5" r="2.6" fill="#0a0a0d" />
  </svg>
);
export const InfoIcon = (p: P) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><line x1="12" y1="11" x2="12" y2="16.5" /><circle cx="12" cy="7.8" r="0.9" fill="currentColor" stroke="none" /></svg>
);
export const LinkIcon = (p: P) => (
  <svg {...base(p)}><path d="M9 15l6-6" /><path d="M11 6l1-1a4 4 0 0 1 6 6l-1 1" /><path d="M13 18l-1 1a4 4 0 0 1-6-6l1-1" /></svg>
);
export const ClipboardIcon = (p: P) => (
  <svg {...base(p)}><rect x="8" y="3" width="8" height="4" rx="1.2" /><path d="M16 5h2a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2" /></svg>
);
export const CloseIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={2.2}><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></svg>
);
export const MusicIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.8}><path d="M9 18V5l11-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="17" cy="16" r="3" /></svg>
);
export const VideoIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.8}><rect x="2.5" y="5" width="14" height="14" rx="3" /><path d="m16.5 9.5 5-2.5v10l-5-2.5" /></svg>
);
export const PlayIcon = (p: P) => (
  <svg width={p.size ?? 12} height={p.size ?? 12} viewBox="0 0 24 24" fill="currentColor" {...p}>
    <path d="M7 5.5v13a1 1 0 0 0 1.54.84l10-6.5a1 1 0 0 0 0-1.68l-10-6.5A1 1 0 0 0 7 5.5Z" />
  </svg>
);
export const SearchIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.8}><circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.5" y2="16.5" /></svg>
);
export const FolderIcon = (p: P) => (
  <svg {...base(p)}><path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h4l2 2.5h7A1.5 1.5 0 0 1 19 10v7a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 3 17V7.5Z" /></svg>
);
export const EditIcon = (p: P) => (
  <svg {...base(p)}><path d="m14.5 5.5 4 4" /><path d="M4 20h4l10.5-10.5a2.8 2.8 0 0 0-4-4L4 16v4Z" /></svg>
);
export const TrashIcon = (p: P) => (
  <svg {...base(p)}><path d="M4 7h16" /><path d="M9 3h6l1 4H8l1-4Z" /><path d="m7 7 1 14h8l1-14" /><path d="M10 11v6M14 11v6" /></svg>
);
export const RefreshIcon = (p: P) => (
  <svg {...base(p)}><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M6.1 8a7 7 0 0 1 11.4-2.2L20 8" /><path d="M17.9 16a7 7 0 0 1-11.4 2.2L4 16" /></svg>
);
export const CheckIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={3}><polyline points="20 6 9 17 4 12" /></svg>
);
export const ChevronIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={2}><polyline points="6 9 12 15 18 9" /></svg>
);
export const MinIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.8}><line x1="5" y1="12" x2="19" y2="12" /></svg>
);
export const MaxIcon = (p: P) => (
  <svg {...base(p)} strokeWidth={1.8}><rect x="4" y="4" width="16" height="16" rx="2.4" /></svg>
);
export const GithubIcon = (p: P) => (
  <svg width={p.size ?? 15} height={p.size ?? 15} viewBox="0 0 24 24" fill="currentColor" {...p}>
    <path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.1.68-.22.68-.49 0-.24-.01-.88-.01-1.73-2.78.62-3.37-1.37-3.37-1.37-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.9 1.56 2.35 1.11 2.92.85.09-.66.35-1.11.63-1.37-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.7 0 0 .84-.28 2.75 1.05A9.36 9.36 0 0 1 12 6.85c.85 0 1.71.12 2.51.34 1.91-1.33 2.75-1.05 2.75-1.05.55 1.4.2 2.44.1 2.7.64.72 1.03 1.63 1.03 2.75 0 3.93-2.35 4.79-4.58 5.05.36.32.68.94.68 1.9 0 1.37-.01 2.48-.01 2.82 0 .27.18.6.69.49A10.04 10.04 0 0 0 22 12.25C22 6.58 17.52 2 12 2Z" />
  </svg>
);

/** Marka logosu — jenerik kırmızı "play" rozeti (orijinal YouTube logosu DEĞİL). */
export const BrandMark = ({ size = 26, radius = 8 }: { size?: number; radius?: number }) => (
  <div
    className="flex items-center justify-center"
    style={{
      width: size, height: size, borderRadius: radius,
      background: "linear-gradient(150deg,#ff3a47,#e0001a)",
      boxShadow: "0 4px 14px -3px rgba(255,40,60,.6), inset 0 1px 0 rgba(255,255,255,.25)",
    }}
  >
    <PlayIcon size={size * 0.42} color="#fff" />
  </div>
);
