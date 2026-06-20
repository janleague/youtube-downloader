"""
Kütüphane sayfası — indirilen dosyaların ızgara görünümü.
Gerçek dosyalar populate(items) ile beslenir; arama anlık filtrelenir.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QLineEdit,
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush

from theme import COLORS, font
from icons import render_svg
from widgets.components import Heading, Sub, SectionLabel
from i18n import tr

class _Thumb(QWidget):
    """Çizgili placeholder küçük resim + format rozeti + ikon."""
    def __init__(self, fmt, parent=None):
        super().__init__(parent)
        self._fmt = fmt
        self.setFixedHeight(96)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # üst köşeleri yuvarlak placeholder
        path = QPainterPath()
        path.moveTo(0, h)
        path.lineTo(0, 14)
        path.quadTo(0, 0, 14, 0)
        path.lineTo(w - 14, 0)
        path.quadTo(w, 0, w, 14)
        path.lineTo(w, h)
        path.closeSubpath()
        p.fillPath(path, QColor(COLORS["thumb_bg"]))
        # çizgili doku
        p.setClipPath(path)
        p.setPen(QColor(COLORS["thumb_stripe"]))
        x = -h
        while x < w:
            p.drawLine(int(x), h, int(x + h), 0)
            p.drawLine(int(x + 4), h, int(x + h + 4), 0)
            x += 18
        p.setClipping(False)
        # ortadaki ikon
        name = "music" if self._fmt == "MP3" else "video"
        pm = render_svg(name, 28, COLORS["thumb_icon"])
        p.drawPixmap(int((w - 28) / 2), int((h - 28) / 2), pm)
        # format rozeti
        badge_w = 38
        bcol = QColor("#ff2233") if self._fmt == "MP3" else QColor("#2d7bff")
        bcol.setAlpha(235)
        bpath = QPainterPath()
        bpath.addRoundedRect(QRectF(9, 9, badge_w, 18), 6, 6)
        p.fillPath(bpath, bcol)
        p.setPen(QColor("#ffffff"))
        p.setFont(font(10, "bold", "ui"))
        p.drawText(QRectF(9, 9, badge_w, 18), Qt.AlignmentFlag.AlignCenter, self._fmt)
        p.end()


class _LibCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, title, fmt, size, quality, path="", parent=None):
        super().__init__(parent)
        self.path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(path)
        self._base()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_Thumb(fmt))

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(13, 12, 13, 13)
        bl.setSpacing(9)

        tl = QLabel(title)
        tl.setWordWrap(True)
        tl.setFont(font(13, "semibold", "ui"))
        tl.setStyleSheet(
            f"color: {COLORS['card_text']}; background: transparent; border: none;"
        )
        tl.setFixedHeight(36)
        bl.addWidget(tl)

        meta = QLabel(f"{size}  ·  {quality}")
        meta.setFont(font(11, "medium", "ui"))
        meta.setStyleSheet(f"color: {COLORS['dim']}; background: transparent; border: none;")
        bl.addWidget(meta)
        lay.addWidget(body)

    def _base(self):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border_faint']};"
            f" border-radius: 14px; }}"
        )

    def enterEvent(self, _):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: 14px; }}"
        )

    def leaveEvent(self, _):
        self._base()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.path:
            self.clicked.emit(self.path)


class LibraryPage(QWidget):
    file_open_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 32)
        root.setSpacing(0)

        # başlık + arama
        head = QHBoxLayout()
        head.setSpacing(0)
        col = QVBoxLayout()
        col.setSpacing(5)
        col.addWidget(Heading(tr("library.title")))
        col.addWidget(Sub(tr("library.subtitle")))
        head.addLayout(col)
        head.addStretch(1)
        head.addWidget(self._search(), alignment=Qt.AlignmentFlag.AlignBottom)
        root.addLayout(head)
        root.addSpacing(24)

        self.grid_host = QWidget()
        self.grid_host.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        for cidx in range(3):
            self.grid.setColumnStretch(cidx, 1)
        root.addWidget(self.grid_host)
        root.addStretch(1)
        self.populate([])

    def _search(self):
        box = QFrame()
        box.setFixedSize(240, 42)
        box.setStyleSheet(
            f"QFrame {{ background: {COLORS['input']}; border: 1px solid {COLORS['border']};"
            f" border-radius: 11px; }}"
        )
        lay = QHBoxLayout(box)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(9)
        ic = QLabel()
        ic.setPixmap(render_svg("search", 15, COLORS["dim"]))
        ic.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(ic)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("library.search"))
        self.search_input.setFont(font(13, "medium", "ui"))
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; color: {COLORS['text']};"
            f" selection-background-color: {COLORS['accent']}; }}"
        )
        self.search_input.textChanged.connect(self._render)
        lay.addWidget(self.search_input)
        return box

    def populate(self, items):
        self._items = list(items)
        self._render()

    def _render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        needle = self.search_input.text().strip().casefold()
        visible = [
            item for item in self._items
            if not needle or needle in item["title"].casefold()
        ]
        if not visible:
            empty = QLabel(
                tr("library.no_match") if needle else tr("library.empty")
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(font(13, "medium", "ui"))
            empty.setStyleSheet(
                f"color: {COLORS['text4']}; background: transparent;"
            )
            empty.setMinimumHeight(120)
            self.grid.addWidget(empty, 0, 0, 1, 3)
            return

        for index, item in enumerate(visible):
            card = _LibCard(
                item["title"],
                item["format"],
                item["size"],
                item["quality"],
                item.get("path", ""),
            )
            card.clicked.connect(self.file_open_requested)
            self.grid.addWidget(card, index // 3, index % 3)
