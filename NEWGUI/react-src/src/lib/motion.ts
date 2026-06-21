/** Framer Motion yumuşak geçiş ön ayarları — her yerde tutarlı 200–300ms ease. */
import type { Transition, Variants } from "framer-motion";

export const EASE = [0.4, 0, 0.2, 1] as const;

export const smooth = (duration = 0.12): Transition => ({ duration, ease: EASE });

/** Sayfa giriş/çıkış animasyonu (AnimatePresence ile). */
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.1, ease: EASE } },
  exit: { opacity: 0, y: -4, transition: { duration: 0.07, ease: EASE } },
};

/** Açılır panel / popover. */
export const popVariants: Variants = {
  initial: { opacity: 0, y: -6, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.08, ease: EASE } },
  exit: { opacity: 0, y: -3, scale: 0.99, transition: { duration: 0.05, ease: EASE } },
};

/** Premium buton mikro-etkileşimi: hover'da hafif yüksel, tıklamada içeri çök. */
export const buttonMotion = {
  whileHover: { y: -2, scale: 1.006 },
  whileTap: { y: 1, scale: 0.992 },
  transition: { duration: 0.08, ease: EASE },
};
