import { motion } from "framer-motion";
import { BrandMark, GithubIcon } from "../components/icons";
import { openUrl } from "../lib/tauri";
import { buttonMotion } from "../lib/motion";
import { useApp } from "../lib/AppContext";
import { APP_VERSION } from "../lib/appInfo";

export function AboutPage() {
  const { ffmpegOk, tr } = useApp();
  const tech = [
    [tr("interface"), "React + Tauri"],
    [tr("engine"), "yt-dlp"],
    [tr("converter"), "ffmpeg"],
    [tr("license"), "MIT"],
  ];

  return (
    <div className="max-w-[760px]">
      <h1 className="m-0 font-sora text-[29px] font-bold tracking-[-.6px] text-[#f5f5f7]">
        {tr("aboutTitle")}
      </h1>
      <p className="mt-[7px] text-[14.5px] font-medium text-[#86868e]">
        {tr("aboutSub")}
      </p>

      <div className="mt-[26px] flex items-center gap-5 rounded-[18px] border border-line bg-glass p-6">
        <BrandMark size={64} radius={18} />
        <div className="flex-1">
          <div className="font-sora text-[21px] font-bold tracking-[-.4px] text-[#f4f4f6]">
            {tr("appName")}
          </div>
          <div className="mt-[2px] text-[13px] font-medium text-[#86868e]">
            {tr("version")} {APP_VERSION}
          </div>
          <div
            className={`mt-[11px] inline-flex items-center gap-[7px] rounded-[8px] border px-[11px] py-[5px] ${
              ffmpegOk
                ? "border-ok/25 bg-ok/10"
                : "border-red-500/25 bg-red-500/10"
            }`}
          >
            <span
              className={`h-[6px] w-[6px] rounded-full ${
                ffmpegOk ? "bg-ok" : "bg-red-500"
              }`}
            />
            <span
              className={`text-[11.5px] font-semibold ${
                ffmpegOk ? "text-ok-light" : "text-red-400"
              }`}
            >
              {tr(ffmpegOk ? "ffmpegOkLong" : "ffmpegMissingLong")}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 flex gap-[14px]">
        <div className="flex-1 rounded-[16px] border border-line bg-glass p-[18px]">
          <div className="text-[11px] font-bold tracking-[1px] text-[#56565d]">
            {tr("developer")}
          </div>
          <div className="mt-[14px] flex items-center gap-3">
            <img
              src="/janleague-avatar-round.png"
              alt="janleague"
              className="h-11 w-11 rounded-full border border-line-strong object-cover"
            />
            <div>
              <div className="text-[14px] font-bold text-[#e7e7ea]">janleague</div>
              <div className="mt-[2px] text-[12px] text-[#86868e]">
                github.com/janleague
              </div>
            </div>
          </div>
          <motion.button
            {...buttonMotion}
            onClick={() => void openUrl("https://github.com/janleague")}
            className="mt-[15px] flex h-[38px] w-full items-center justify-center gap-[9px] rounded-[10px] border border-white/[0.08] bg-glass-2 text-[12.5px] font-semibold text-[#cfcfd4]"
            style={{ cursor: "pointer" }}
          >
            <GithubIcon size={15} /> {tr("githubProfile")}
          </motion.button>
        </div>

        <div className="flex-1 rounded-[16px] border border-line bg-glass p-[18px]">
          <div className="text-[11px] font-bold tracking-[1px] text-[#56565d]">
            {tr("technology")}
          </div>
          <div className="mt-[14px] flex flex-col gap-[11px]">
            {tech.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-[13px] font-medium text-[#cfcfd4]">
                  {key}
                </span>
                <span className="font-sora text-[12.5px] font-semibold text-[#86868e]">
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="mt-[22px] text-center text-[12px] font-medium text-[#4d4d55]">
        {tr("footer")}
      </p>
    </div>
  );
}
