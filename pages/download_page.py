"""
İndir sayfası — ana ekran.
URL girişi, MP3/MP4 kartları, çözünürlük seçimi, indir düğmesi ve ilerleme paneli.

BACKEND BAĞLANTI NOKTALARI (sinyaller):
    download_requested(url:str, fmt:str, resolution:str|None)
    paste_requested()        # Yapıştır düğmesi

BACKEND'İN ÇAĞIRACAĞI GENEL METOTLAR (GUI güncelleme):
    set_progress(pct, speed, eta)
    set_status(text, level)     # level: info|success|warning|error
    set_complete(title)
    set_error(message)
    reset_progress()
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

from theme import COLORS, font, qc
from icons import render_svg
from i18n import tr
from widgets.components import (
    Heading, Sub, SectionLabel, FormatCard, ResolutionPill, GradientBar,
    Spinner, GhostButton, soft_shadow,
)

RESOLUTIONS = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "En İyi"]


class _UrlField(QFrame):
    """İkon + giriş + temizle düğmeli URL kutusu."""
    cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['input']}; border: 1px solid {COLORS['border']};"
            f" border-radius: 13px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 12, 0)
        lay.setSpacing(11)

        ic = QLabel()
        ic.setPixmap(render_svg("link", 17, COLORS["dim"]))
        ic.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(ic)

        self.input = QLineEdit()
        self.input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.input.setFont(font(14, "medium", "ui"))
        self.input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; color: {COLORS['text']};"
            f" selection-background-color: {COLORS['accent']}; }}"
        )
        self.input.textChanged.connect(self._on_text)
        lay.addWidget(self.input, 1)

        self.clear_btn = QLabel()
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clear_btn.setPixmap(render_svg("close", 11, COLORS["text4"]))
        self.clear_btn.setStyleSheet(
            f"QLabel {{ background: transparent; border-radius: 7px; }}"
            f"QLabel:hover {{ background: {COLORS['elev']}; }}"
        )
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.mousePressEvent = lambda e: self._clear()
        self.clear_btn.setVisible(False)
        lay.addWidget(self.clear_btn)

    def _on_text(self, t):
        self.clear_btn.setVisible(bool(t))

    def _clear(self):
        self.input.clear()
        self.cleared.emit()

    def text(self):
        return self.input.text().strip()

    def setText(self, t):
        self.input.setText(t)


class DownloadPage(QWidget):
    download_requested = pyqtSignal(str, str, object)   # url, fmt, resolution|None
    paste_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fmt = "mp3"
        self._resolution = "1080p"
        self._busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 26)
        root.setSpacing(0)

        root.addWidget(Heading(tr("download.title")))
        sub = Sub(tr("download.subtitle"))
        sub.setContentsMargins(0, 5, 0, 0)
        root.addWidget(sub)
        root.addSpacing(24)

        # ── URL ──
        root.addWidget(SectionLabel(tr("download.url")))
        root.addSpacing(9)
        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url = _UrlField()
        self.url.cleared.connect(lambda: None)
        url_row.addWidget(self.url, 1)
        self.paste = GhostButton(tr("download.paste"), "clipboard", height=54)
        self.paste.clicked.connect(self._on_paste)
        url_row.addWidget(self.paste)
        root.addLayout(url_row)
        root.addSpacing(22)

        # ── FORMAT ──
        root.addWidget(SectionLabel(tr("download.format")))
        root.addSpacing(9)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(12)
        self.card_mp3 = FormatCard("mp3", "MP3", tr("download.mp3sub"), "music",
                                   accent=("#ff2a38", "#d10018"))
        self.card_mp4 = FormatCard("mp4", "MP4", tr("download.mp4sub"), "video",
                                   accent=("#2d7bff", "#1456d6"))
        self.card_mp3.clicked.connect(self._select_format)
        self.card_mp4.clicked.connect(self._select_format)
        fmt_row.addWidget(self.card_mp3)
        fmt_row.addWidget(self.card_mp4)
        root.addLayout(fmt_row)
        root.addSpacing(22)

        # ── ÇÖZÜNÜRLÜK (yalnız MP4) ──
        self.res_wrap = QWidget()
        rw = QVBoxLayout(self.res_wrap)
        rw.setContentsMargins(0, 0, 0, 0)
        rw.setSpacing(0)
        rw.addWidget(SectionLabel(tr("download.resolution")))
        rw.addSpacing(9)
        pills = QHBoxLayout()
        pills.setSpacing(8)
        self._pills = []
        for val in RESOLUTIONS:
            pill = ResolutionPill(val)
            pill.setSelected(val == self._resolution)
            pill.clicked.connect(self._select_resolution)
            self._pills.append(pill)
            pills.addWidget(pill)
        pills.addStretch(1)
        rw.addLayout(pills)
        rw.addSpacing(22)
        root.addWidget(self.res_wrap)
        self.res_wrap.setVisible(False)

        # ── İNDİR DÜĞMESİ ──
        self.dl_btn = _DownloadButton()
        self.dl_btn.clicked.connect(self._on_start)
        root.addWidget(self.dl_btn)
        root.addSpacing(22)

        # ── İLERLEME PANELİ ──
        root.addWidget(self._build_progress())
        root.addStretch(1)
        self._select_format("mp3")

    # ───────────────────────── ilerleme paneli ─────────────────────────
    def _build_progress(self):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border_faint']};"
            f" border-radius: 15px; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(11)
        self.spinner = Spinner(15)
        top.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.status = QLabel(tr("download.ready"))
        self.status.setFont(font(13.5, "semibold", "ui"))
        self.status.setStyleSheet(f"color: {COLORS['text2']}; background: transparent; border: none;")
        top.addWidget(self.status)
        top.addStretch(1)
        self.pct = QLabel("%0.0")
        self.pct.setFont(font(18, "bold", "display"))
        self.pct.setStyleSheet(f"color: {COLORS['accent2']}; background: transparent; border: none;")
        top.addWidget(self.pct)
        lay.addLayout(top)
        lay.addSpacing(13)

        self.bar = GradientBar()
        lay.addWidget(self.bar)
        lay.addSpacing(11)

        meta = QHBoxLayout()
        self.speed = QLabel("")
        self.speed.setFont(font(12, "medium", "ui"))
        self.speed.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
        self.eta = QLabel("")
        self.eta.setFont(font(12, "medium", "ui"))
        self.eta.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
        meta.addWidget(self.speed)
        meta.addStretch(1)
        meta.addWidget(self.eta)
        lay.addLayout(meta)

        self.spinner.stop()
        return card

    # ───────────────────────── etkileşim ─────────────────────────
    def _select_format(self, fmt):
        self._fmt = fmt
        self.card_mp3.setSelected(fmt == "mp3")
        self.card_mp4.setSelected(fmt == "mp4")
        self.res_wrap.setVisible(fmt == "mp4")

    def _select_resolution(self, val):
        self._resolution = val
        for pill in self._pills:
            pill.setSelected(pill.value == val)

    def _on_paste(self):
        self.paste_requested.emit()

    def _on_start(self):
        if self._busy:
            return
        url = self.url.text()
        res = self._resolution if self._fmt == "mp4" else None
        self.download_requested.emit(url, self._fmt, res)

    # ───────────────────────── genel API (backend → GUI) ─────────────────────────
    def set_url(self, text: str):
        self.url.setText(text)

    def set_default_format(self, fmt: str):
        self._select_format(fmt.lower())

    def set_default_resolution(self, resolution: str):
        if resolution in {pill.value for pill in self._pills}:
            self._select_resolution(resolution)

    def set_busy(self, busy: bool):
        self._busy = busy
        self.dl_btn.set_busy(busy)
        self.url.input.setEnabled(not busy)

    def set_progress(self, pct: float, speed: str = "", eta: str = ""):
        self.spinner.start()
        self.bar.setColors("#e00018", "#ff3b47")
        self.bar.setValue(pct)
        self.pct.setStyleSheet(f"color: {COLORS['accent2']}; background: transparent; border: none;")
        self.pct.setText(f"%{pct:.1f}")
        self.speed.setText(speed)
        self.eta.setText(eta)

    def set_status(self, text: str, level: str = "info"):
        colors = {
            "info": COLORS["text2"], "success": COLORS["green2"],
            "warning": "#f59e0b", "error": "#ef4444",
        }
        self.status.setText(text)
        self.status.setStyleSheet(
            f"color: {colors.get(level, COLORS['text2'])}; background: transparent; border: none;")

    def set_complete(self, title: str = ""):
        self.spinner.stop()
        self.set_busy(False)
        self.bar.setColors("#16a34a", "#22c55e")
        self.bar.setValue(100)
        self.pct.setStyleSheet(f"color: {COLORS['green2']}; background: transparent; border: none;")
        self.pct.setText("%100")
        self.speed.setText("")
        self.eta.setText("bitti")
        self.set_status(tr("download.done"), "success")

    def set_error(self, message: str):
        self.spinner.stop()
        self.set_busy(False)
        self.reset_progress()
        self.set_status(message, "error")

    def reset_progress(self):
        self.bar.setValue(0)
        self.pct.setText("%0.0")
        self.pct.setStyleSheet(f"color: {COLORS['accent2']}; background: transparent; border: none;")
        self.speed.setText("")
        self.eta.setText("")


class _DownloadButton(QFrame):
    """Kırmızı gradyan + glow indir düğmesi."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._busy = False
        self._hover = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addStretch(1)
        self._ic = QLabel()
        self._ic.setPixmap(render_svg("download", 19, "#ffffff"))
        self._ic.setStyleSheet("background: transparent; border: none;")
        self._ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self._ic)
        self._lb = QLabel(tr("download.button"))
        self._lb.setFont(font(15.5, "bold", "display"))
        self._lb.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        self._lb.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self._lb)
        lay.addStretch(1)

        self._glow = soft_shadow(self, qc("accent", 92), blur=30, dy=8)

    def set_busy(self, busy):
        self._busy = busy
        self._lb.setText(
            tr("download.busy") if busy else tr("download.button")
        )
        self._ic.setVisible(not busy)
        self.update()

    def enterEvent(self, _):
        self._hover = True
        self.update()

    def leaveEvent(self, _):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self._busy:
            self.clicked.emit()

    def paintEvent(self, _):
        from PyQt6.QtGui import QLinearGradient, QBrush, QPainterPath
        from PyQt6.QtCore import QRectF
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 13, 13)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        if self._busy:
            grad.setColorAt(0.0, QColor("#7a0a12"))
            grad.setColorAt(1.0, QColor("#5e000c"))
        elif self._hover:
            grad.setColorAt(0.0, QColor("#ff3a47"))
            grad.setColorAt(1.0, QColor("#f00020"))
        else:
            grad.setColorAt(0.0, QColor("#ff2a38"))
            grad.setColorAt(1.0, QColor("#e00018"))
        p.fillPath(path, QBrush(grad))
        p.end()
