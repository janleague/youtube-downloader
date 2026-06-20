"""
Özel QWidget bileşenleri — QSS'in yetmediği yerlerde QPainter ile çizilir.
Hepsi yeniden kullanılabilir; sayfalar bu yapı taşlarından kurulur.

İçindekiler:
  Logo            — kırmızı-beyaz play-button logosu (QPainter)
  IconChip        — yuvarlatılmış renkli ikon kutucuğu
  GhostButton     — ince kenarlı, ikon+metin düğmesi
  FormatCard      — MP3 / MP4 seçim kartı (glow'lu)
  ResolutionPill  — çözünürlük seçim hapı
  GradientBar     — gradyan + glow ilerleme çubuğu
  Spinner         — dönen yükleme halkası
  ToggleSwitch    — animasyonlu aç/kapa anahtarı
  SectionLabel / Heading / Sub  — tipografi yardımcıları
  hline           — ince ayraç
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QRectF, QSize, QTimer,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QPixmap,
)

from theme import COLORS, qc, font
from icons import render_svg


# ──────────────────────────────────────────────────────────────
#  Tipografi yardımcıları
# ──────────────────────────────────────────────────────────────
def _label(text, fnt, color):
    lb = QLabel(text)
    lb.setFont(fnt)
    lb.setStyleSheet(f"color: {color}; background: transparent;")
    return lb


def Heading(text):
    lb = _label(text, font(25, "bold", "display", spacing=-0.5), COLORS["text"])
    return lb


def Sub(text):
    return _label(text, font(13.5, "regular", "ui"), COLORS["text4"])


def SectionLabel(text):
    lb = _label(text, font(10, "bold", "ui", spacing=1.2), COLORS["dim"])
    return lb


def hline(color=None):
    ln = QFrame()
    ln.setFixedHeight(1)
    ln.setStyleSheet(f"background: {color or COLORS['border_faint']}; border: none;")
    return ln


def soft_shadow(widget, color: QColor, blur=26, dy=6):
    """Bir widget'a yumuşak (glow) gölge ekler."""
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setColor(color)
    eff.setOffset(0, dy)
    widget.setGraphicsEffect(eff)
    return eff


# ──────────────────────────────────────────────────────────────
#  Logo  —  kırmızı squircle + beyaz play üçgeni
# ──────────────────────────────────────────────────────────────
class Logo(QWidget):
    def __init__(self, size=30, radius=9, parent=None):
        super().__init__(parent)
        self._size = size
        self._radius = radius
        self.setFixedSize(size, size)

    def sizeHint(self):
        return QSize(self._size, self._size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self._size, self._size)

        # yuvarlatılmış kırmızı gövde (köşegen gradyan)
        path = QPainterPath()
        path.addRoundedRect(r, self._radius, self._radius)
        grad = QLinearGradient(0, 0, self._size, self._size)
        grad.setColorAt(0.0, QColor("#ff2a38"))
        grad.setColorAt(1.0, QColor("#d10018"))
        p.fillPath(path, QBrush(grad))

        # beyaz play üçgeni (optik olarak ortalanmış)
        s = self._size
        tri = QPainterPath()
        tri.moveTo(s * 0.40, s * 0.30)
        tri.lineTo(s * 0.72, s * 0.50)
        tri.lineTo(s * 0.40, s * 0.70)
        tri.closeSubpath()
        p.fillPath(tri, QColor("#ffffff"))
        p.end()


# ──────────────────────────────────────────────────────────────
#  IconChip  —  yuvarlatılmış renkli ikon kutucuğu
# ──────────────────────────────────────────────────────────────
class IconChip(QWidget):
    def __init__(self, icon_name, chip=46, icon=22, parent=None):
        super().__init__(parent)
        self._name = icon_name
        self._chip = chip
        self._icon = icon
        self._active = True
        self._grad = ("#ff2a38", "#d10018")
        self.setFixedSize(chip, chip)
        self._glow = soft_shadow(self, qc("accent", 95), blur=20, dy=4)
        self._refresh()

    def setActive(self, active: bool, accent_grad=("#ff2a38", "#d10018")):
        self._active = active
        self._grad = accent_grad
        self._refresh()

    def _refresh(self):
        col = "#ffffff" if self._active else COLORS["text3"]
        self._pm = render_svg(self._name, self._icon, col)
        self._glow.setEnabled(self._active)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0, 0, self._chip, self._chip)
        path = QPainterPath()
        path.addRoundedRect(r, 12, 12)
        if self._active:
            g0, g1 = self._grad
            grad = QLinearGradient(0, 0, self._chip, self._chip)
            grad.setColorAt(0.0, QColor(g0))
            grad.setColorAt(1.0, QColor(g1))
            p.fillPath(path, QBrush(grad))
        else:
            p.fillPath(path, QColor(COLORS["icon_muted_bg"]))
        # ikon ortala
        x = (self._chip - self._icon) / 2
        p.drawPixmap(int(x), int(x), self._pm)
        p.end()


# ──────────────────────────────────────────────────────────────
#  GhostButton  —  ince kenarlı ikon + metin düğmesi
# ──────────────────────────────────────────────────────────────
class GhostButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, text, icon_name=None, height=54, parent=None,
                 bg=None, icon_size=16, font_size=13.5, pad=18, chevron=False):
        super().__init__(parent)
        self._bg = bg or COLORS["input"]
        self.setFixedHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background: {self._bg}; border: 1px solid {COLORS['border']};"
            f" border-radius: 11px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(pad, 0, pad, 0)
        lay.setSpacing(8)
        if icon_name:
            ic = QLabel()
            ic.setPixmap(render_svg(icon_name, icon_size, COLORS["text3"]))
            ic.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(ic)
        self._text = QLabel(text)
        self._text.setFont(font(font_size, "semibold", "ui"))
        self._text.setStyleSheet(f"color: {COLORS['text2']}; background: transparent; border: none;")
        lay.addWidget(self._text)
        if chevron:
            lay.addSpacing(2)
            cv = QLabel()
            cv.setPixmap(render_svg("chevron", 13, COLORS["text4"]))
            cv.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(cv)

    def enterEvent(self, _):
        self.setStyleSheet(
            f"QFrame {{ background: {COLORS['elev']}; border: 1px solid {COLORS['border2']};"
            f" border-radius: 11px; }}"
        )

    def leaveEvent(self, _):
        self.setStyleSheet(
            f"QFrame {{ background: {self._bg}; border: 1px solid {COLORS['border']};"
            f" border-radius: 11px; }}"
        )

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def setText(self, text: str):
        self._text.setText(text)


# ──────────────────────────────────────────────────────────────
#  FormatCard  —  MP3 / MP4 seçim kartı
# ──────────────────────────────────────────────────────────────
class FormatCard(QFrame):
    clicked = pyqtSignal(str)   # değer ("mp3" / "mp4")

    def __init__(self, value, title, subtitle, icon_name,
                 accent=("#ff2a38", "#d10018"), parent=None):
        super().__init__(parent)
        self.value = value
        self._accent = accent
        self._selected = False
        self._hover = False
        self.setFixedHeight(78)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(14)

        self.chip = IconChip(icon_name)
        lay.addWidget(self.chip)

        col = QVBoxLayout()
        col.setSpacing(3)
        col.setContentsMargins(0, 0, 0, 0)
        self._title = QLabel(title)
        self._title.setFont(font(16, "bold", "display"))
        self._title.setStyleSheet(f"color: {COLORS['text']}; background: transparent;")
        self._subtitle = QLabel(subtitle)
        self._subtitle.setFont(font(12, "regular", "ui"))
        self._subtitle.setStyleSheet(f"color: {COLORS['text3']}; background: transparent;")
        col.addWidget(self._title)
        col.addWidget(self._subtitle)
        lay.addLayout(col)
        lay.addStretch(1)

        # onay rozeti
        self.check = QLabel()
        self.check.setFixedSize(20, 20)
        self.check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check.setStyleSheet(
            f"background: {COLORS['accent']}; border-radius: 10px;"
        )
        self.check.setPixmap(render_svg("check", 11, "#ffffff"))
        lay.addWidget(self.check, alignment=Qt.AlignmentFlag.AlignTop)

        self._glow = soft_shadow(self, qc("accent", 70), blur=30, dy=6)
        self.setSelected(False)

    def setSelected(self, sel: bool):
        self._selected = sel
        self.chip.setActive(sel, self._accent)
        self._title.setStyleSheet(
            f"color: {COLORS['text'] if sel else COLORS['text2']}; background: transparent;"
        )
        self._subtitle.setStyleSheet(
            f"color: {COLORS['text3'] if sel else COLORS['text4']}; background: transparent;"
        )
        self.check.setVisible(sel)
        self._glow.setEnabled(sel)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(0.75, 0.75, self.width() - 1.5, self.height() - 1.5)
        path = QPainterPath()
        path.addRoundedRect(r, 15, 15)
        if self._selected:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0.0, QColor(255, 34, 51, 26))
            grad.setColorAt(1.0, QColor(255, 34, 51, 8))
            p.fillPath(path, QBrush(grad))
            p.setPen(QPen(qc("accent"), 1.5))
        else:
            p.fillPath(path, QColor(COLORS["card_hover"] if self._hover else COLORS["card2"]))
            p.setPen(QPen(QColor(COLORS["border_hover"]) if self._hover else qc("border"), 1.5))
        p.drawPath(path)
        p.end()

    def enterEvent(self, _):
        if not self._selected:
            self._hover = True
            self.update()

    def leaveEvent(self, _):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.value)


# ──────────────────────────────────────────────────────────────
#  ResolutionPill  —  çözünürlük seçim hapı
# ──────────────────────────────────────────────────────────────
class ResolutionPill(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.value = value
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self._lb = QLabel(value)
        self._lb.setFont(font(13, "semibold", "ui"))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 0, 15, 0)
        lay.addWidget(self._lb)
        self.setSelected(False)

    def setSelected(self, sel: bool):
        self._selected = sel
        if sel:
            self.setStyleSheet(
                f"QFrame {{ background: rgba(255,34,51,0.12); border: 1px solid {COLORS['accent']};"
                f" border-radius: 9px; }}"
            )
            self._lb.setStyleSheet(f"color: {COLORS['accent_soft']}; background: transparent; border: none;")
            self._lb.setFont(font(13, "bold", "ui"))
        else:
            self.setStyleSheet(
                f"QFrame {{ background: {COLORS['input']}; border: 1px solid {COLORS['border']};"
                f" border-radius: 9px; }}"
            )
            self._lb.setStyleSheet(f"color: {COLORS['text3']}; background: transparent; border: none;")
            self._lb.setFont(font(13, "semibold", "ui"))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.value)


# ──────────────────────────────────────────────────────────────
#  GradientBar  —  gradyan + glow ilerleme çubuğu
# ──────────────────────────────────────────────────────────────
class GradientBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._c0 = QColor("#e00018")
        self._c1 = QColor("#ff3b47")
        self.setFixedHeight(9)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._glow = soft_shadow(self, QColor(255, 40, 55, 110), blur=16, dy=0)
        self._glow.setEnabled(False)

    def setValue(self, v: float):
        self._value = max(0.0, min(100.0, v))
        self._glow.setEnabled(self._value > 0.5)
        self.update()

    def setColors(self, c0: str, c1: str):
        self._c0 = QColor(c0)
        self._c1 = QColor(c1)
        glow = QColor(c1)
        glow.setAlpha(110)
        self._glow.setColor(glow)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # iz
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.fillPath(track, QColor(COLORS["progress_track"]))
        # dolgu
        fw = w * self._value / 100.0
        if fw > 1:
            fill = QPainterPath()
            fill.addRoundedRect(QRectF(0, 0, fw, h), h / 2, h / 2)
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, self._c0)
            grad.setColorAt(1.0, self._c1)
            p.fillPath(fill, QBrush(grad))
        p.end()


# ──────────────────────────────────────────────────────────────
#  Spinner  —  dönen yükleme halkası
# ──────────────────────────────────────────────────────────────
class Spinner(QWidget):
    def __init__(self, size=15, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._timer.start(28)
            self.setVisible(True)

    def stop(self):
        self._running = False
        self._timer.stop()
        self.setVisible(False)

    def _tick(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, _):
        if not self._running:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 2
        rect = QRectF(m, m, self._size - 2 * m, self._size - 2 * m)
        # zemin halkası
        p.setPen(QPen(QColor(COLORS["spinner_track"]), 2))
        p.drawArc(rect, 0, 360 * 16)
        # dönen yay
        arc_pen = QPen(qc("accent"), 2)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        p.drawArc(rect, -self._angle * 16, 100 * 16)
        p.end()


# ──────────────────────────────────────────────────────────────
#  ToggleSwitch  —  animasyonlu aç/kapa anahtarı
# ──────────────────────────────────────────────────────────────
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 1.0 if checked else 0.0
        self.setFixedSize(44, 25)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._glow = soft_shadow(self, qc("accent", 85), blur=18, dy=0)
        self._glow.setEnabled(checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, val: bool):
        if val == self._checked:
            return
        self._checked = val
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if val else 0.0)
        self._anim.start()
        self._glow.setEnabled(val)
        self.toggled.emit(val)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def get_pos(self):
        return self._pos

    def set_pos(self, v):
        self._pos = v
        self.update()

    pos = pyqtProperty(float, fget=get_pos, fset=set_pos)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        off = QColor(COLORS["switch_off"])
        on = qc("accent")
        # iki renk arası interpolasyon
        def lerp(a, b, t):
            return int(a + (b - a) * t)
        col = QColor(
            lerp(off.red(), on.red(), self._pos),
            lerp(off.green(), on.green(), self._pos),
            lerp(off.blue(), on.blue(), self._pos),
        )
        p.fillPath(track, col)
        # knob
        d = h - 6
        x = 3 + (w - d - 6) * self._pos
        p.setBrush(QColor("#ffffff"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(x, 3, d, d))
        p.end()
