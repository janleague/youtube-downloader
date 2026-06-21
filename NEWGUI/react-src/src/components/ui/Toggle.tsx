import { motion } from "framer-motion";
import { EASE } from "../../lib/motion";

/** iOS tarzı premium anahtar — açıkken kırmızı gradient, knob yumuşak kayar. */
export function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className="no-drag relative h-[27px] w-[46px] shrink-0 rounded-[14px] p-0"
      style={{
        border: "none",
        cursor: "pointer",
        background: on ? "linear-gradient(135deg,#ff3a47,#e0001a)" : "rgba(255,255,255,0.12)",
        transition: "background .08s",
      }}
      role="switch"
      aria-checked={on}
    >
      <motion.span
        className="absolute left-[3px] top-[3px] h-[21px] w-[21px] rounded-full bg-white"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,.4)" }}
        animate={{ x: on ? 19 : 0 }}
        transition={{ duration: 0.08, ease: EASE }}
      />
    </button>
  );
}
