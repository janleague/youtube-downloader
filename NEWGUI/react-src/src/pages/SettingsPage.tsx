import { FolderIcon } from "../components/icons";
import { Toggle } from "../components/ui/Toggle";
import { Dropdown } from "../components/ui/Dropdown";
import { AUDIO_QUALITIES } from "../data/mock";
import { useApp } from "../lib/AppContext";
import type { Format, Language } from "../lib/tauri";

const Label = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-[11px] text-[11px] font-bold tracking-[1.5px] text-[#56565d]">
    {children}
  </div>
);

const Row = ({
  title,
  sub,
  children,
}: {
  title: string;
  sub: string;
  children: React.ReactNode;
}) => (
  <div className="flex items-center justify-between gap-4 py-4">
    <div className="min-w-0">
      <div className="text-[14px] font-semibold text-[#e7e7ea]">{title}</div>
      <div className="mt-[3px] truncate text-[12.5px] text-[#7a7a82]" title={sub}>
        {sub}
      </div>
    </div>
    {children}
  </div>
);

const Divider = () => <div className="h-px bg-white/5" />;
const Card = ({ children }: { children: React.ReactNode }) => (
  <div className="rounded-[16px] border border-line bg-glass px-[18px] py-1">
    {children}
  </div>
);

export function SettingsPage() {
  const { settings, tr, updateSetting, chooseFolder } = useApp();
  const languageLabels: Record<Language, string> = {
    tr: "Türkçe",
    en: "English",
  };

  return (
    <div className="max-w-[760px]">
      <h1 className="m-0 font-sora text-[29px] font-bold tracking-[-.6px] text-[#f5f5f7]">
        {tr("settingsTitle")}
      </h1>
      <p className="mt-[7px] text-[14.5px] font-medium text-[#86868e]">
        {tr("settingsSub")}
      </p>

      <div className="mt-7">
        <Label>{tr("downloadSection")}</Label>
      </div>
      <Card>
        <Row title={tr("downloadFolder")} sub={settings.downloadsDir}>
          <button
            onClick={() => void chooseFolder()}
            className="flex h-[38px] shrink-0 items-center gap-2 rounded-[10px] border border-white/[0.08] bg-glass-2 px-[14px] text-[12.5px] font-semibold text-[#cfcfd4] hover:border-line-strong hover:bg-[rgba(255,255,255,0.07)]"
            style={{ cursor: "pointer", transition: "all .18s" }}
          >
            <FolderIcon size={15} /> {tr("change")}
          </button>
        </Row>
        <Divider />
        <Row title={tr("defaultFormat")} sub={tr("defaultFormatSub")}>
          <div className="flex gap-[3px] rounded-[11px] border border-white/[0.07] bg-glass-2 p-[3px]">
            {(["mp3", "mp4"] as Format[]).map((format) => {
              const selected = settings.defaultFormat === format;
              return (
                <button
                  key={format}
                  onClick={() =>
                    void updateSetting(
                      "defaultFormat",
                      "default_format",
                      format,
                    )
                  }
                  className="h-[30px] rounded-[8px] px-4 text-[12.5px] font-bold uppercase"
                  style={{
                    border: "none",
                    cursor: "pointer",
                    color: selected ? "#fff" : "#9a9aa2",
                    background: selected
                      ? "linear-gradient(135deg,#ff3a47,#e0001a)"
                      : "transparent",
                    boxShadow: selected
                      ? "0 4px 14px -4px rgba(255,40,60,.6)"
                      : "none",
                    transition: "all .18s",
                  }}
                >
                  {format}
                </button>
              );
            })}
          </div>
        </Row>
        <Divider />
        <Row title={tr("audioQuality")} sub={tr("audioQualitySub")}>
          <Dropdown
            value={`${settings.audioQuality} kbps`}
            options={AUDIO_QUALITIES.map((quality) => `${quality} kbps`)}
            onChange={(value) =>
              void updateSetting(
                "audioQuality",
                "audio_quality",
                value.replace(/\D/g, ""),
              )
            }
          />
        </Row>
      </Card>

      <div className="mt-[26px]">
        <Label>{tr("general")}</Label>
      </div>
      <Card>
        <Row title={tr("language")} sub={tr("languageSub")}>
          <Dropdown
            value={languageLabels[settings.language]}
            options={Object.values(languageLabels)}
            onChange={(value) => {
              const language = (
                value === languageLabels.en ? "en" : "tr"
              ) as Language;
              void updateSetting("language", "language", language);
            }}
          />
        </Row>
        <Divider />
        <Row title={tr("notifications")} sub={tr("notificationsSub")}>
          <Toggle
            on={settings.notifications}
            onChange={(value) =>
              void updateSetting("notifications", "notifications", value)
            }
          />
        </Row>
        <Divider />
        <Row title={tr("darkTheme")} sub={tr("darkThemeSub")}>
          <Toggle
            on={settings.darkTheme}
            onChange={(value) =>
              void updateSetting("darkTheme", "dark_theme", value)
            }
          />
        </Row>
      </Card>
    </div>
  );
}
