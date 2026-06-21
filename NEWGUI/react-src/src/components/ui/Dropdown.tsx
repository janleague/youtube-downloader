import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronIcon, CheckIcon } from "../icons";
import { popVariants, EASE } from "../../lib/motion";

/** Yumuşak açılan select. Dışarı tıklamada kapanır. */
export function Dropdown({
  value,
  options,
  onChange,
}: {
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative no-drag">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex h-[38px] items-center gap-[9px] rounded-[10px] border border-white/[0.08] bg-white/[0.035] px-[13px] text-[13px] font-semibold text-[#dcdce2] outline-none hover:border-white/[0.13] hover:bg-white/[0.055] focus:border-accent/40"
        style={{ cursor: "pointer", transition: "background .18s, border-color .18s" }}
      >
        {value}
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2, ease: EASE }}>
          <ChevronIcon size={13} />
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-[18]" onClick={() => setOpen(false)} />
            <motion.div
              variants={popVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="absolute right-0 top-[44px] z-20 min-w-[148px] rounded-[12px] border border-white/[0.08] bg-ink-750 p-[5px] shadow-pop"
            >
              {options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => { onChange(opt); setOpen(false); }}
                  className="flex h-[34px] w-full items-center justify-between rounded-[8px] px-[11px] text-[12.5px] font-semibold hover:bg-[rgba(255,255,255,0.05)]"
                  style={{ border: "none", cursor: "pointer", background: "transparent", color: opt === value ? "#f4f4f6" : "#b9b9c2" }}
                >
                  {opt}
                  {opt === value && <CheckIcon size={13} className="text-accent-light" strokeWidth={2.6} />}
                </button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
