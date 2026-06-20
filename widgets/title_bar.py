"""
Özel başlık çubuğu — frameless pencere için.
Sol: logo + uygulama adı + sürüm.  Sağ: küçült / büyüt / kapat kontrolleri.
Pencere sürüklemesi burada yönetilir.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

from theme import COLORS, font
from icons import render_svg
from widgets.components import Logo, soft_shadow
from theme import qc
from i18n import tr


class _WinButton(QFrame):
    """Pencere kontrol düğmesi (küçült/büyüt/kapat)."""
    clicked = pyqtSignal()

    def __init__(self, icon_name, danger=False, parent=None):
        super().__init__(parent)
        self._name = icon_name
        self._danger = danger
        self.setFixedSize(46, 52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._lb = QLabel(self)
        self._lb.setPixmap(render_svg(icon_name, 13, COLORS["text3"]))
        self._lb.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lb, alignment=Qt.AlignmentFlag.AlignCenter)

    def enterEvent(self, _):
        self._hover = True
        self._lb.setPixmap(render_svg(
            self._name, 13, "#ffffff" if self._danger else COLORS["text"]))
        self.update()

    def leaveEvent(self, _):
        self._hover = False
        self._lb.setPixmap(render_svg(self._name, 13, COLORS["text3"]))
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _):
        if not self._hover:
            return
        p = QPainter(self)
        p.fillRect(
            self.rect(),
            QColor("#e01428") if self._danger else QColor(COLORS["window_hover"]),
        )
        p.end()


class TitleBar(QWidget):
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self._drag_offset = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 0, 0)
        lay.setSpacing(0)

        # ── sol: logo + ad ──
        left = QHBoxLayout()
        left.setSpacing(11)
        logo = Logo(30, 9)
        soft_shadow(logo, qc("accent", 105), blur=18, dy=4)
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        left.addWidget(logo)
        title = QLabel(tr("app.name"))
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title.setFont(font(14, "bold", "display", spacing=-0.2))
        title.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        left.addWidget(title)
        ver = QLabel("v2.0")
        ver.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        ver.setFont(font(11, "medium", "ui"))
        ver.setStyleSheet(f"color: {COLORS['dim']}; background: transparent;")
        left.addWidget(ver, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(left)

        lay.addStretch(1)

        # ── sağ: pencere kontrolleri ──
        self.btn_min = _WinButton("minimize")
        self.btn_max = _WinButton("maximize")
        self.btn_close = _WinButton("close", danger=True)
        self.btn_min.clicked.connect(self.minimize_clicked.emit)
        self.btn_max.clicked.connect(self.maximize_clicked.emit)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        for b in (self.btn_min, self.btn_max, self.btn_close):
            lay.addWidget(b)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(COLORS["bg_titlebar"]))
        # alt ayraç
        p.setPen(QColor(COLORS["border_faint"]))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()

    # ── pencere sürükleme ──
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None and (e.buttons() & Qt.MouseButton.LeftButton):
            self.window().move(e.globalPosition().toPoint() - self._drag_offset)
            e.accept()

    def mouseReleaseEvent(self, _):
        self._drag_offset = None
