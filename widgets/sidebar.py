"""
Sol kenar menüsü (sidebar).
Dört gezinme öğesi (İndir / Kütüphane / Ayarlar / Hakkında) + altta
ffmpeg durumu ve GitHub bağlantısı. Aktif öğe kırmızı vurgulu çizilir.
"""
import webbrowser
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QRadialGradient, QBrush

from theme import COLORS, font, qc
from icons import render_svg
from i18n import tr

GITHUB_URL = "https://github.com/janleague"


class NavItem(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, key, label, icon_name, parent=None):
        super().__init__(parent)
        self.key = key
        self._icon = icon_name
        self._selected = False
        self._hover = False
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(13)
        self._ic = QLabel()
        self._ic.setFixedSize(19, 19)
        self._ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self._ic, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._lb = QLabel(label)
        self._lb.setFont(font(14, "semibold", "ui"))
        self._lb.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(self._lb)
        lay.addStretch(1)
        self._apply()

    def setSelected(self, sel: bool):
        self._selected = sel
        self._apply()

    def _apply(self):
        icon_color = COLORS["accent2"] if self._selected else COLORS["text4"]
        text_color = COLORS["selected_text"] if self._selected else COLORS["text3"]
        self._ic.setPixmap(render_svg(self._icon, 19, icon_color))
        self._lb.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.update()

    def enterEvent(self, _):
        self._hover = True
        self.update()

    def leaveEvent(self, _):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(r, 11, 11)
        if self._selected:
            p.fillPath(path, QColor(255, 34, 51, 26))
            # sol gösterge çubuğu
            bar = QPainterPath()
            bar.addRoundedRect(QRectF(0, 11, 3, 24), 1.5, 1.5)
            p.fillPath(bar, qc("accent"))
        elif self._hover:
            p.fillPath(path, QColor(COLORS["card2"]))
        p.end()


class Sidebar(QWidget):
    page_changed = pyqtSignal(str)

    ITEMS = [
        ("download", "nav.download", "download"),
        ("library", "nav.library", "library"),
        ("settings", "nav.settings", "settings"),
        ("about", "nav.about", "info"),
    ]

    def __init__(self, ffmpeg_ok=True, parent=None):
        super().__init__(parent)
        self.setFixedWidth(232)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 18, 14, 18)
        lay.setSpacing(4)

        cap = QLabel(tr("menu"))
        cap.setFont(font(10, "bold", "ui", spacing=1.4))
        cap.setStyleSheet(f"color: {COLORS['dim2']}; background: transparent;")
        cap.setContentsMargins(10, 6, 0, 12)
        lay.addWidget(cap)

        self._items = {}
        for key, label_key, icon in self.ITEMS:
            it = NavItem(key, tr(label_key), icon)
            it.clicked.connect(self.select)
            self._items[key] = it
            lay.addWidget(it)

        lay.addStretch(1)

        # ── alt bilgi kartı ──
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border_faint']};"
            f" border-radius: 12px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(9)

        status = QHBoxLayout()
        status.setSpacing(8)
        self._ffmpeg_dot = _Dot(COLORS["green"] if ffmpeg_ok else "#ef4444")
        status.addWidget(self._ffmpeg_dot)
        self._ffmpeg_label = QLabel(
            tr("ffmpeg.ready") if ffmpeg_ok else tr("ffmpeg.missing")
        )
        self._ffmpeg_label.setFont(font(11, "semibold", "ui"))
        self._ffmpeg_label.setStyleSheet(
            f"color: {COLORS['text4']}; background: transparent; border: none;"
        )
        status.addWidget(self._ffmpeg_label)
        status.addStretch(1)
        cl.addLayout(status)

        gh = _GithubRow()
        cl.addWidget(gh)
        lay.addWidget(card)

        self.select("download")

    def set_ffmpeg_status(self, ready: bool):
        self._ffmpeg_dot.setColor(COLORS["green"] if ready else "#ef4444")
        self._ffmpeg_label.setText(
            tr("ffmpeg.ready") if ready else tr("ffmpeg.missing")
        )

    def select(self, key: str):
        for k, it in self._items.items():
            it.setSelected(k == key)
        self.page_changed.emit(key)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(COLORS["bg_sidebar"]))
        p.setPen(QColor(COLORS["border_faint"]))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()


class _Dot(QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(8, 8)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QRadialGradient(4, 4, 4)
        glow.setColorAt(0.0, QColor(self._color))
        outer = QColor(self._color)
        outer.setAlpha(0)
        glow.setColorAt(1.0, outer)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(0, 0, 8, 8)
        p.setBrush(self._color)
        p.drawEllipse(2, 2, 5, 5)
        p.end()

    def setColor(self, color: str):
        self._color = QColor(color)
        self.update()


class _GithubRow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self._base()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(9, 0, 9, 0)
        lay.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(render_svg("github", 15, COLORS["text4"]))
        ic.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(ic)
        lb = QLabel("github.com/janleague")
        lb.setFont(font(11, "semibold", "ui"))
        lb.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
        lay.addWidget(lb)
        lay.addStretch(1)

    def _base(self):
        self.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px solid {COLORS['border']};"
            f" border-radius: 8px; }}"
        )

    def enterEvent(self, _):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['elev']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: 8px; }}"
        )

    def leaveEvent(self, _):
        self._base()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            webbrowser.open(GITHUB_URL)
