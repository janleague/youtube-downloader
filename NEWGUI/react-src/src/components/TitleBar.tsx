import { BrandMark, MinIcon, MaxIcon, CloseIcon } from "./icons";
import {
  windowClose,
  windowMinimize,
  windowToggleMaximize,
} from "../lib/tauri";
import { useApp } from "../lib/AppContext";

function WinButton({
  children,
  danger,
  onClick,
}: {
  children: React.ReactNode;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="no-drag flex h-[30px] w-[32px] items-center justify-center rounded-[8px] text-[#8a8a93]"
      style={{
        border: "none",
        background: "transparent",
        cursor: "pointer",
        transition: "background .18s, color .18s",
      }}
      onMouseEnter={(event) => {
        event.currentTarget.style.background = danger
          ? "#e0001a"
          : "rgba(255,255,255,0.06)";
        event.currentTarget.style.color = "#fff";
      }}
      onMouseLeave={(event) => {
        event.currentTarget.style.background = "transparent";
        event.currentTarget.style.color = "#8a8a93";
      }}
    >
      {children}
    </button>
  );
}

export function TitleBar() {
  const { tr } = useApp();

  async function close() {
    const closed = await windowClose(false);
    if (!closed && window.confirm(tr("closeWhileBusy"))) {
      await windowClose(true);
    }
  }

  return (
    <div
      data-tauri-drag-region
      className="titlebar drag flex h-12 shrink-0 items-center gap-[13px] border-b border-white/5 pl-4 pr-3"
      style={{ background: "#0c0c10" }}
    >
      <BrandMark />
      <span className="font-sora text-[13.5px] font-bold tracking-[-.2px] text-[#f4f4f6]">
        {tr("appName")}
      </span>
      <span className="rounded-[6px] border border-white/[0.06] bg-white/[0.04] px-[7px] py-[2px] text-[10.5px] font-semibold text-[#6a6a72]">
        v2.2.2
      </span>
      <div className="flex-1" data-tauri-drag-region />
      <WinButton onClick={() => void windowMinimize()}>
        <MinIcon size={13} />
      </WinButton>
      <WinButton onClick={() => void windowToggleMaximize()}>
        <MaxIcon size={11} />
      </WinButton>
      <WinButton danger onClick={() => void close()}>
        <CloseIcon size={13} />
      </WinButton>
    </div>
  );
}
