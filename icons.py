"""
SVG ikon sağlayıcı.
Unicode/emoji KULLANILMAZ — tüm ikonlar vektör SVG'dir ve istenen renkle
(QSvgRenderer ile) yüksek DPI'da QPixmap olarak işlenir.
"""
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt6.QtCore import Qt, QByteArray


# {C} → çizgi/dolgu rengi yer tutucusu
_ICONS = {
    "download": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<path d="M10 3V12M10 12L6.5 8.5M10 12L13.5 8.5" stroke="{C}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M4 14.5V16A1 1 0 0 0 5 17H15A1 1 0 0 0 16 16V14.5" stroke="{C}" stroke-width="1.5" stroke-linecap="round"/></svg>',

    "library":  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<rect x="3" y="3" width="6" height="6" rx="1.6" stroke="{C}" stroke-width="1.5"/>'
                '<rect x="11" y="3" width="6" height="6" rx="1.6" stroke="{C}" stroke-width="1.5"/>'
                '<rect x="3" y="11" width="6" height="6" rx="1.6" stroke="{C}" stroke-width="1.5"/>'
                '<rect x="11" y="11" width="6" height="6" rx="1.6" stroke="{C}" stroke-width="1.5"/></svg>',

    "settings": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<circle cx="10" cy="10" r="2.6" stroke="{C}" stroke-width="1.5"/>'
                '<path d="M10 2.2V4M10 16V17.8M17.8 10H16M4 10H2.2M15.5 4.5L14.2 5.8M5.8 14.2L4.5 15.5M15.5 15.5L14.2 14.2M5.8 5.8L4.5 4.5" stroke="{C}" stroke-width="1.5" stroke-linecap="round"/></svg>',

    "info":     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<circle cx="10" cy="10" r="7.2" stroke="{C}" stroke-width="1.5"/>'
                '<path d="M10 9V13.4" stroke="{C}" stroke-width="1.5" stroke-linecap="round"/>'
                '<circle cx="10" cy="6.6" r="0.95" fill="{C}"/></svg>',

    "music":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22" fill="none">'
                '<path d="M8 16V7L17 5V14" stroke="{C}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="6" cy="16" r="2.1" stroke="{C}" stroke-width="1.7"/>'
                '<circle cx="15" cy="14" r="2.1" stroke="{C}" stroke-width="1.7"/></svg>',

    "video":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22" fill="none">'
                '<rect x="3" y="5.5" width="16" height="11" rx="2.5" stroke="{C}" stroke-width="1.7"/>'
                '<path d="M9.2 9.3L13.4 11L9.2 12.7Z" fill="{C}"/></svg>',

    "link":     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<path d="M8.5 11.5a3 3 0 0 0 4.2 0l2.6-2.6a3 3 0 0 0-4.2-4.2l-1.3 1.3" stroke="{C}" stroke-width="1.5" stroke-linecap="round"/>'
                '<path d="M11.5 8.5a3 3 0 0 0-4.2 0l-2.6 2.6a3 3 0 0 0 4.2 4.2l1.3-1.3" stroke="{C}" stroke-width="1.5" stroke-linecap="round"/></svg>',

    "clipboard":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<rect x="5" y="4" width="10" height="13" rx="2" stroke="{C}" stroke-width="1.5"/>'
                '<path d="M8 4V3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1" stroke="{C}" stroke-width="1.5"/></svg>',

    "search":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<circle cx="9" cy="9" r="6" stroke="{C}" stroke-width="1.6"/>'
                '<path d="M13.5 13.5L17 17" stroke="{C}" stroke-width="1.6" stroke-linecap="round"/></svg>',

    "check":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12" fill="none">'
                '<path d="M2.5 6.2L5 8.6L9.5 3.6" stroke="{C}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',

    "chevron":  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 14 14" fill="none">'
                '<path d="M3.5 5.5L7 9L10.5 5.5" stroke="{C}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',

    "folder":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none">'
                '<path d="M3 6a1.5 1.5 0 0 1 1.5-1.5H8l1.5 1.5H15.5A1.5 1.5 0 0 1 17 7.5V14a1.5 1.5 0 0 1-1.5 1.5H4.5A1.5 1.5 0 0 1 3 14Z" stroke="{C}" stroke-width="1.5"/></svg>',

    "minimize": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13 13" fill="none">'
                '<path d="M2.5 6.5H10.5" stroke="{C}" stroke-width="1.3" stroke-linecap="round"/></svg>',

    "maximize": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13 13" fill="none">'
                '<rect x="3" y="3" width="7" height="7" rx="1.5" stroke="{C}" stroke-width="1.3"/></svg>',

    "close":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13 13" fill="none">'
                '<path d="M3.3 3.3L9.7 9.7M9.7 3.3L3.3 9.7" stroke="{C}" stroke-width="1.3" stroke-linecap="round"/></svg>',

    "github":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
                '<path fill="{C}" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>',
}


def render_svg(name: str, size: int, color: str = "#ffffff", ratio: int = 2) -> QPixmap:
    """SVG ikonunu verilen renk ve boyutta (yüksek DPI) QPixmap olarak işler."""
    svg = _ICONS[name].replace("{C}", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    img = QImage(size * ratio, size * ratio, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    renderer.render(painter)
    painter.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(ratio)
    return pm


def make_icon(name: str, size: int, color: str = "#ffffff") -> QIcon:
    return QIcon(render_svg(name, size, color))
