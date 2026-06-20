"""
Hakkında sayfası — uygulama / geliştirici / teknoloji bilgileri.
"""
import sys
import webbrowser
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QPainter, QColor, QPainterPath, QLinearGradient, QBrush, QRadialGradient,
    QPixmap,
)
from PyQt6.QtCore import QRectF
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from theme import COLORS, font
from icons import render_svg
from widgets.components import Heading, Sub, Logo, soft_shadow, qc
from i18n import tr

GITHUB_URL = "https://github.com/janleague"
GITHUB_AVATAR_URL = "https://github.com/janleague.png?size=128"


class _Avatar(QLabel):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        photo = QPixmap(str(base / "assets" / "janleague-avatar-round.png"))
        if not photo.isNull():
            self._set_photo(photo)
        else:
            self.setText("j")
        self.setStyleSheet(
            f"background: {COLORS['purple']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: {size // 2}px; color: white;"
        )
        self._network = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(GITHUB_AVATAR_URL))
        request.setRawHeader(b"User-Agent", b"YouTubeDownloader/2.1")
        self._network.get(request).finished.connect(self._avatar_loaded)

    def _avatar_loaded(self):
        reply = self.sender()
        if not isinstance(reply, QNetworkReply):
            return
        if reply.error() == QNetworkReply.NetworkError.NoError:
            photo = QPixmap()
            if photo.loadFromData(bytes(reply.readAll())):
                self._set_photo(photo)
        reply.deleteLater()

    def _set_photo(self, photo: QPixmap):
        side = min(photo.width(), photo.height())
        cropped = photo.copy(
            (photo.width() - side) // 2,
            (photo.height() - side) // 2,
            side,
            side,
        ).scaled(
            self._size,
            self._size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        rounded = QPixmap(self._size, self._size)
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addEllipse(QRectF(0, 0, self._size, self._size))
        painter.setClipPath(clip)
        painter.drawPixmap(0, 0, cropped)
        painter.end()
        self.setPixmap(rounded)


class AboutPage(QWidget):
    def __init__(self, ffmpeg_ok=True, parent=None):
        super().__init__(parent)
        self.ffmpeg_ok = ffmpeg_ok
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 32)
        root.setSpacing(0)

        root.addWidget(Heading(tr("about.title")))
        sub = Sub(tr("about.subtitle"))
        sub.setContentsMargins(0, 5, 0, 0)
        root.addWidget(sub)
        root.addSpacing(26)

        root.addWidget(self._app_card())
        root.addSpacing(16)

        cols = QHBoxLayout()
        cols.setSpacing(14)
        cols.addWidget(self._dev_card(), 1)
        cols.addWidget(self._tech_card(), 1)
        root.addLayout(cols)
        root.addSpacing(16)

        foot = QLabel(tr("about.footer"))
        foot.setFont(font(12, "regular", "ui"))
        foot.setStyleSheet(f"color: {COLORS['dim2']}; background: transparent;")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(foot)
        root.addStretch(1)

    # ── üst app kartı ──
    def _app_card(self):
        card = _Card()
        lay = QHBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(18)

        logo = Logo(64, 18)
        soft_shadow(logo, qc("accent", 100), blur=30, dy=10)
        lay.addWidget(logo, alignment=Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(4)
        name = QLabel(tr("app.name"))
        name.setFont(font(21, "bold", "display", spacing=-0.4))
        name.setStyleSheet(f"color: {COLORS['text']}; background: transparent; border: none;")
        ver = QLabel(tr("about.version"))
        ver.setFont(font(13, "regular", "ui"))
        ver.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
        col.addWidget(name)
        col.addWidget(ver)
        col.addSpacing(6)
        col.addWidget(self._ffmpeg_pill(), alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addLayout(col)
        lay.addStretch(1)
        return card

    def _ffmpeg_pill(self):
        pill = QFrame()
        pill.setStyleSheet(
            "QFrame { background: rgba(34,197,94,0.10); border: 1px solid rgba(34,197,94,0.25);"
            " border-radius: 8px; }"
        )
        lay = QHBoxLayout(pill)
        lay.setContentsMargins(11, 5, 11, 5)
        lay.setSpacing(7)
        dot = _GreenDot(self.ffmpeg_ok)
        lay.addWidget(dot)
        lb = QLabel(
            tr("about.ffmpeg_ok")
            if self.ffmpeg_ok else tr("about.ffmpeg_missing")
        )
        lb.setFont(font(11.5, "semibold", "ui"))
        color = COLORS["green2"] if self.ffmpeg_ok else "#ef4444"
        lb.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        lay.addWidget(lb)
        return pill

    # ── geliştirici kartı ──
    def _dev_card(self):
        card = _Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(0)
        cap = QLabel(tr("about.developer"))
        cap.setFont(font(11, "bold", "ui", spacing=0.8))
        cap.setStyleSheet(f"color: {COLORS['dim']}; background: transparent; border: none;")
        lay.addWidget(cap)
        lay.addSpacing(12)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(_Avatar(40))
        col = QVBoxLayout()
        col.setSpacing(2)
        n = QLabel("janleague")
        n.setFont(font(14, "bold", "ui"))
        n.setStyleSheet(
            f"color: {COLORS['card_text']}; background: transparent; border: none;"
        )
        h = QLabel("github.com/janleague")
        h.setFont(font(12, "regular", "ui"))
        h.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
        col.addWidget(n)
        col.addWidget(h)
        row.addLayout(col)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addSpacing(14)

        btn = _GithubButton()
        lay.addWidget(btn)
        return card

    # ── teknoloji kartı ──
    def _tech_card(self):
        card = _Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(0)
        cap = QLabel(tr("about.technology"))
        cap.setFont(font(11, "bold", "ui", spacing=0.8))
        cap.setStyleSheet(f"color: {COLORS['dim']}; background: transparent; border: none;")
        lay.addWidget(cap)
        lay.addSpacing(12)
        rows = [
            (tr("about.interface"), "PyQt6"),
            (tr("about.engine"), "yt-dlp"),
            (tr("about.converter"), "ffmpeg"),
            (tr("about.license"), "MIT"),
        ]
        for i, (k, v) in enumerate(rows):
            r = QHBoxLayout()
            kl = QLabel(k)
            kl.setFont(font(13, "medium", "ui"))
            kl.setStyleSheet(f"color: {COLORS['text2']}; background: transparent; border: none;")
            vl = QLabel(v)
            vl.setFont(font(12, "semibold", "display"))
            vl.setStyleSheet(f"color: {COLORS['text4']}; background: transparent; border: none;")
            r.addWidget(kl)
            r.addStretch(1)
            r.addWidget(vl)
            lay.addLayout(r)
            if i < len(rows) - 1:
                lay.addSpacing(9)
        return card


class _Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border_faint']};"
            f" border-radius: 16px; }}"
        )


class _GreenDot(QWidget):
    def __init__(self, ready=True, parent=None):
        super().__init__(parent)
        self._color = QColor(COLORS["green"] if ready else "#ef4444")
        self.setFixedSize(6, 6)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QRadialGradient(3, 3, 3)
        glow.setColorAt(0.0, self._color)
        clear = QColor(self._color)
        clear.setAlpha(0)
        glow.setColorAt(1.0, clear)
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 6, 6)
        p.setBrush(self._color)
        p.drawEllipse(1, 1, 4, 4)
        p.end()


class _GithubButton(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._base()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addStretch(1)
        ic = QLabel()
        ic.setPixmap(render_svg("github", 15, COLORS["text2"]))
        ic.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(ic)
        lb = QLabel(tr("about.github"))
        lb.setFont(font(12.5, "semibold", "ui"))
        lb.setStyleSheet(f"color: {COLORS['text2']}; background: transparent; border: none;")
        lay.addWidget(lb)
        lay.addStretch(1)

    def _base(self):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['elev']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: 9px; }}"
        )

    def enterEvent(self, _):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['hover_surface']};"
            f" border: 1px solid {COLORS['hover_border']}; border-radius: 9px; }}"
        )

    def leaveEvent(self, _):
        self._base()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            webbrowser.open(GITHUB_URL)
