"""
Tema: renk paleti, font yükleme (QFontDatabase) ve yardımcı font/etiket fabrikaları.
Tüm görsel sabitler tek yerde toplanır; widget'lar buradan beslenir.
"""
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase, QColor


# ──────────────────────────────────────────────────────────────
#  RENK PALETLERİ
# ──────────────────────────────────────────────────────────────
DARK_COLORS = {
    "bg_app":       "#0a0a0c",   # ana içerik arka planı
    "bg_titlebar":  "#0e0e11",   # başlık çubuğu
    "bg_sidebar":   "#0c0c0f",   # sol menü
    "card":         "#101013",   # kart / panel
    "card2":        "#121215",   # seçili olmayan format kartı
    "input":        "#141417",   # giriş kutusu / pill
    "elev":         "#17171b",   # yükseltilmiş kontrol (select, ghost)
    "border":       "#232327",   # standart kenarlık
    "border_faint": "#1a1a1d",   # ince ayraç
    "border2":      "#2a2a2e",   # daha belirgin kenarlık

    "accent":       "#ff2233",   # YouTube kırmızısı (vurgu)
    "accent2":      "#ff3b47",   # açık kırmızı (gradient ucu)
    "accent_dk":    "#d10018",   # koyu kırmızı (gradient başı)
    "accent_soft":  "#ff5560",   # metin kırmızısı

    "text":         "#f5f5f6",   # ana metin
    "text2":        "#cfcfd4",   # ikincil metin (açık)
    "text3":        "#9a9aa2",   # ikincil metin
    "text4":        "#86868e",   # soluk metin
    "dim":          "#56565d",   # etiket / placeholder
    "dim2":         "#46464d",   # en soluk

    "green":        "#22c55e",
    "green2":       "#4ade80",
    "blue":         "#2d7bff",
    "purple":       "#6e40c9",
    "white":        "#ffffff",
    "selected_text":"#ffffff",
    "card_text":    "#e7e7ea",
    "icon_muted_bg":"#1d1d21",
    "card_hover":   "#151518",
    "border_hover": "#33333a",
    "progress_track":"#1c1c20",
    "spinner_track":"#2a2a2e",
    "switch_off":   "#2a2a2e",
    "thumb_bg":     "#17171b",
    "thumb_stripe": "#1c1c20",
    "thumb_icon":   "#3a3a40",
    "hover_surface":"#1a1a1e",
    "hover_border": "#3a3a40",
    "window_hover": "#1d1d20",
    "scroll_hover": "#3a3a40",
}

LIGHT_COLORS = {
    "bg_app":       "#f7f8fb",
    "bg_titlebar":  "#ffffff",
    "bg_sidebar":   "#f1f3f7",
    "card":         "#ffffff",
    "card2":        "#fafbfc",
    "input":        "#ffffff",
    "elev":         "#f2f4f8",
    "border":       "#d9dde6",
    "border_faint": "#e7e9ef",
    "border2":      "#c8cdd8",
    "accent":       "#ff0033",
    "accent2":      "#ff304f",
    "accent_dk":    "#d50024",
    "accent_soft":  "#db1538",
    "text":         "#15171c",
    "text2":        "#30343c",
    "text3":        "#5e6470",
    "text4":        "#747b87",
    "dim":          "#8a919d",
    "dim2":         "#a0a6b1",
    "green":        "#16a34a",
    "green2":       "#15803d",
    "blue":         "#246fe5",
    "purple":       "#6e40c9",
    "white":        "#ffffff",
    "selected_text":"#a10f2d",
    "card_text":    "#23262d",
    "icon_muted_bg":"#eceff4",
    "card_hover":   "#f1f3f7",
    "border_hover": "#b8beca",
    "progress_track":"#e5e8ee",
    "spinner_track":"#d3d8e1",
    "switch_off":   "#cbd1db",
    "thumb_bg":     "#eef1f5",
    "thumb_stripe": "#e1e5ec",
    "thumb_icon":   "#aeb5c1",
    "hover_surface":"#edf0f5",
    "hover_border": "#b7bdc9",
    "window_hover": "#e9ecf2",
    "scroll_hover": "#aeb5c1",
}

COLORS = DARK_COLORS.copy()
_DARK_THEME = True


def set_theme(dark: bool) -> dict:
    """Aktif paleti değiştirir. Pencere yeniden kurulduğunda tüm UI güncellenir."""
    global _DARK_THEME
    _DARK_THEME = bool(dark)
    COLORS.clear()
    COLORS.update(DARK_COLORS if _DARK_THEME else LIGHT_COLORS)
    return COLORS


def is_dark_theme() -> bool:
    return _DARK_THEME


def c(name: str) -> str:
    """Renk kodunu döndürür (kısayol)."""
    return COLORS[name]


def qc(name: str, alpha: int = 255) -> QColor:
    """QColor döndürür; isteğe bağlı alfa (0-255)."""
    col = QColor(COLORS[name])
    if alpha != 255:
        col.setAlpha(alpha)
    return col


# ──────────────────────────────────────────────────────────────
#  FONT YÜKLEME
# ──────────────────────────────────────────────────────────────
# Sora  → başlıklar / display
# Manrope → arayüz / gövde
# fonts/ klasörüne .ttf dosyaları bırakılırsa otomatik yüklenir;
# bulunamazsa sistem yazı tipine (Segoe UI) zarifçe düşer.

FONTS = {"display": "Segoe UI", "ui": "Segoe UI"}

_WEIGHTS = {
    "regular":  QFont.Weight.Normal,     # 400
    "medium":   QFont.Weight.Medium,     # 500
    "semibold": QFont.Weight.DemiBold,   # 600
    "bold":     QFont.Weight.Bold,       # 700
    "extra":    QFont.Weight.ExtraBold,  # 800
}


def load_fonts() -> dict:
    """
    fonts/ klasöründeki tüm .ttf dosyalarını QFontDatabase'e ekler ve
    Sora / Manrope ailelerini tespit eder. QApplication oluşturulduktan
    sonra çağrılmalıdır.
    """
    base = Path(__file__).resolve().parent / "fonts"
    loaded_families = set()

    if base.exists():
        for ttf in sorted(base.glob("*.ttf")):
            fid = QFontDatabase.addApplicationFont(str(ttf))
            if fid != -1:
                for fam in QFontDatabase.applicationFontFamilies(fid):
                    loaded_families.add(fam)

    def pick(preferred: str, fallback: str) -> str:
        if preferred in loaded_families:
            return preferred
        for fam in loaded_families:
            if fam.lower() == preferred.lower():
                return fam
        # sistemde kayıtlı mı?
        if preferred in QFontDatabase.families():
            return preferred
        return fallback

    # Mantıklı sistem yedeği seç
    sys_fallback = "Segoe UI"
    for cand in ("Segoe UI", "Helvetica Neue", "Arial"):
        if cand in QFontDatabase.families():
            sys_fallback = cand
            break

    FONTS["display"] = pick("Sora", sys_fallback)
    FONTS["ui"] = pick("Manrope", sys_fallback)
    return FONTS


def font(size: float, weight: str = "regular", family: str = "ui",
         spacing: float | None = None) -> QFont:
    """Yapılandırılmış bir QFont döndürür."""
    f = QFont(FONTS[family])
    f.setPixelSize(round(size))
    f.setWeight(_WEIGHTS.get(weight, QFont.Weight.Normal))
    if spacing is not None:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


# ──────────────────────────────────────────────────────────────
#  UYGULAMA GENELİ QSS (scrollbar, tooltip, scroll alanı)
# ──────────────────────────────────────────────────────────────
def app_qss() -> str:
    return f"""
    QWidget {{
        color: {COLORS['text']};
        font-family: "{FONTS['ui']}";
    }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 4px 2px 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border2']}; border-radius: 4px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {COLORS['scroll_hover']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QScrollBar:horizontal {{ height: 0; }}
    QToolTip {{
        background: {COLORS['elev']}; color: {COLORS['text2']};
        border: 1px solid {COLORS['border2']}; border-radius: 6px; padding: 5px 8px;
    }}
    """
