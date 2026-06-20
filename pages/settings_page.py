"""
Ayarlar sayfası — yapılandırma satırları.
Arayüz katmanı; gerçek tercih kaydı backend tarafından yapılacak.

BACKEND BAĞLANTI NOKTALARI (sinyaller):
    folder_change_requested()
    default_format_changed(fmt:str)
    quality_change_requested()
    language_change_requested()
    notifications_toggled(on:bool)
    dark_theme_toggled(on:bool)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

from theme import COLORS, font
from icons import render_svg
from widgets.components import Heading, Sub, SectionLabel, GhostButton, ToggleSwitch, hline
from i18n import tr


def _row(title, desc, control, last=False):
    row = QFrame()
    row.setStyleSheet("QFrame { background: transparent; border: none; }")
    outer = QVBoxLayout(row)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    inner = QWidget()
    lay = QHBoxLayout(inner)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(12)
    col = QVBoxLayout()
    col.setSpacing(3)
    t = QLabel(title)
    t.setFont(font(13.5, "semibold", "ui"))
    t.setStyleSheet(
        f"color: {COLORS['card_text']}; background: transparent; border: none;"
    )
    d = QLabel(desc)
    d.setFont(font(12, "regular", "ui"))
    d.setStyleSheet(f"color: {COLORS['dim']}; background: transparent; border: none;")
    col.addWidget(t)
    col.addWidget(d)
    lay.addLayout(col)
    lay.addStretch(1)
    lay.addWidget(control, alignment=Qt.AlignmentFlag.AlignVCenter)
    outer.addWidget(inner)
    if not last:
        outer.addWidget(hline())
    return row


class _Segmented(QFrame):
    """İki seçenekli segment kontrol (MP3 / MP4)."""
    changed = pyqtSignal(str)

    def __init__(self, options, selected, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['elev']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: 9px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(0)
        self._segs = {}
        self._selected = selected
        for opt in options:
            seg = QLabel(opt)
            seg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            seg.setFixedHeight(28)
            seg.setMinimumWidth(52)
            seg.setCursor(Qt.CursorShape.PointingHandCursor)
            seg.setFont(font(12.5, "bold", "ui"))
            seg.mousePressEvent = lambda e, o=opt: self._pick(o)
            self._segs[opt] = seg
            lay.addWidget(seg)
        self._apply()

    def _pick(self, opt):
        self.setSelected(opt)
        self.changed.emit(opt)

    def setSelected(self, opt):
        if opt in self._segs:
            self._selected = opt
            self._apply()

    def _apply(self):
        for opt, seg in self._segs.items():
            if opt == self._selected:
                seg.setStyleSheet(
                    f"QLabel {{ background: {COLORS['accent']}; color: #ffffff;"
                    f" border-radius: 7px; }}")
                seg.setFont(font(12.5, "bold", "ui"))
            else:
                seg.setStyleSheet(
                    f"QLabel {{ background: transparent; color: {COLORS['text3']};"
                    f" border-radius: 7px; }}")
                seg.setFont(font(12.5, "semibold", "ui"))


class SettingsPage(QWidget):
    folder_change_requested = pyqtSignal()
    default_format_changed = pyqtSignal(str)
    quality_change_requested = pyqtSignal()
    language_change_requested = pyqtSignal()
    notifications_toggled = pyqtSignal(bool)
    dark_theme_toggled = pyqtSignal(bool)

    def __init__(
        self,
        downloads_path="…\\Converter\\Downloads",
        default_format="MP3",
        audio_quality="320",
        language="tr",
        notifications=True,
        dark_theme=True,
        parent=None,
    ):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 32)
        root.setSpacing(0)

        root.addWidget(Heading(tr("settings.title")))
        sub = Sub(tr("settings.subtitle"))
        sub.setContentsMargins(0, 5, 0, 0)
        root.addWidget(sub)
        root.addSpacing(24)

        # ── İNDİRME ──
        root.addWidget(SectionLabel(tr("settings.download")))
        root.addSpacing(10)
        self.folder_btn = GhostButton(
            tr("settings.change"), "folder", height=36, bg=COLORS["elev"],
            font_size=12.5, pad=14,
        )
        self.folder_btn.clicked.connect(self.folder_change_requested.emit)
        self.format_segment = _Segmented(
            ["MP3", "MP4"], default_format.upper(),
        )
        self.format_segment.changed.connect(self.default_format_changed.emit)
        self.quality_btn = GhostButton(
            f"{audio_quality} kbps", height=36, bg=COLORS["elev"],
            font_size=12.5, pad=14, chevron=True,
        )
        self.quality_btn.clicked.connect(self.quality_change_requested.emit)
        self.folder_row = _row(tr("settings.folder"), downloads_path, self.folder_btn)
        folder_labels = self.folder_row.findChildren(QLabel)
        self.folder_path_label = next(
            (label for label in folder_labels if label.text() == downloads_path),
            None,
        )
        root.addWidget(self._card([
            self.folder_row,
            _row(
                tr("settings.default_format"),
                tr("settings.default_format_desc"),
                self.format_segment,
            ),
            _row(
                tr("settings.quality"),
                tr("settings.quality_desc"),
                self.quality_btn,
                last=True,
            ),
        ]))
        root.addSpacing(22)

        # ── GENEL ──
        root.addWidget(SectionLabel(tr("settings.general")))
        root.addSpacing(10)
        self.language_btn = GhostButton(
            "Türkçe" if language == "tr" else "English",
            height=36, bg=COLORS["elev"],
            font_size=12.5, pad=14, chevron=True,
        )
        self.language_btn.clicked.connect(self.language_change_requested.emit)
        self.tg_notif = ToggleSwitch(notifications)
        self.tg_notif.toggled.connect(self.notifications_toggled.emit)
        self.tg_theme = ToggleSwitch(dark_theme)
        self.tg_theme.toggled.connect(self.dark_theme_toggled.emit)
        root.addWidget(self._card([
            _row(
                tr("settings.language"),
                tr("settings.language_desc"),
                self.language_btn,
            ),
            _row(
                tr("settings.notifications"),
                tr("settings.notifications_desc"),
                self.tg_notif,
            ),
            _row(
                tr("settings.theme"),
                tr("settings.theme_desc"),
                self.tg_theme,
                last=True,
            ),
        ]))
        root.addStretch(1)

    def set_downloads_path(self, path: str):
        short = path if len(path) <= 48 else "…" + path[-47:]
        if self.folder_path_label:
            self.folder_path_label.setText(short)
            self.folder_path_label.setToolTip(path)

    def set_audio_quality(self, quality: str):
        self.quality_btn.setText(f"{quality} kbps")

    def set_language(self, language: str):
        self.language_btn.setText("Türkçe" if language == "tr" else "English")

    def set_default_format(self, fmt: str):
        self.format_segment.setSelected(fmt.upper())

    def _card(self, rows):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border_faint']};"
            f" border-radius: 14px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        for r in rows:
            lay.addWidget(r)
        return card
