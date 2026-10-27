"""Topneah Video APP - cortar, juntar e extrair audio de clips de jogos.

Requer: PySide6 e imageio-ffmpeg (ou FFmpeg no PATH).
"""
from __future__ import annotations

import math
import json
import uuid
from dataclasses import asdict
import os
import sys
import traceback
from pathlib import Path

def _start_without_console():
    """Use pythonw on Windows, leaving an existing terminal available."""
    if sys.platform != "win32" or getattr(sys, "frozen", False):
        return
    executable = Path(sys.executable)
    if executable.name.lower() not in ("python.exe", "python_d.exe"):
        return
    windowed = executable.with_name("pythonw_d.exe" if executable.name.lower() == "python_d.exe" else "pythonw.exe")
    if not windowed.is_file():
        return
    import subprocess
    subprocess.Popen(
        [str(windowed), str(Path(__file__).resolve()), *sys.argv[1:]],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    raise SystemExit(0)


if __name__ == "__main__":
    _start_without_console()


from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QThread, QUrl, QSettings, Signal
from PySide6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QIcon,
                           QKeySequence, QLinearGradient, QPainter, QPen,
                           QPixmap, QPolygonF, QShortcut)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSlider, QStyledItemDelegate, QStyle, QStyleOptionComboBox, QVBoxLayout, QWidget,
)

import core
from themes import DISPLAY, T, THEME_LABELS, activate_theme, build_style

APP_NAME = "Topneah Video APP"
VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".ts")


def fmt_t(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:06.3f}" if h else f"{int(m):02d}:{s:06.3f}"


# ------------------------------------------------------------------ icones
def make_app_icon() -> QIcon:
    """Render the taskbar icon in memory at common Windows icon sizes."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 40, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(size / 32, size / 32)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#286EC5"))
        painter.drawRoundedRect(QRectF(1, 1, 30, 30), 7, 7)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawPolygon(QPolygonF([QPointF(12, 8), QPointF(24, 16), QPointF(12, 24)]))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def make_icon(kind: str, color: str = T["muted"], size: int = 22) -> QIcon:
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 24, size / 24)
    c = QColor(color)
    fill = QBrush(c)
    stroke = QPen(c, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(Qt.NoPen)
    p.setBrush(fill)
    poly = lambda pts: QPolygonF([QPointF(x, y) for x, y in pts])
    if kind == "play":
        p.drawPolygon(poly([(7, 4), (20, 12), (7, 20)]))
    elif kind == "pause":
        p.drawRoundedRect(QRectF(6, 4, 4, 16), 1, 1)
        p.drawRoundedRect(QRectF(14, 4, 4, 16), 1, 1)
    elif kind == "skip_in":
        p.drawRect(QRectF(5, 5, 3, 14))
        p.drawPolygon(poly([(20, 5), (9, 12), (20, 19)]))
    elif kind == "skip_out":
        p.drawRect(QRectF(16, 5, 3, 14))
        p.drawPolygon(poly([(4, 5), (15, 12), (4, 19)]))
    elif kind == "plus":
        p.drawRoundedRect(QRectF(10.5, 4, 3, 16), 1.2, 1.2)
        p.drawRoundedRect(QRectF(4, 10.5, 16, 3), 1.2, 1.2)
    elif kind == "eye":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawEllipse(QRectF(2.5, 6, 19, 12))
        p.setPen(Qt.NoPen); p.setBrush(fill)
        p.drawEllipse(QRectF(9, 9, 6, 6))
    elif kind == "folder":
        p.drawPolygon(poly([(3, 6), (9.5, 6), (11.5, 8.5), (21, 8.5), (21, 19), (3, 19)]))
    elif kind == "trash":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawRoundedRect(QRectF(6, 8, 12, 12), 2, 2)
        p.drawLine(QPointF(4, 6), QPointF(20, 6))
        p.drawLine(QPointF(9.5, 3.5), QPointF(14.5, 3.5))
    elif kind == "download":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawLine(QPointF(12, 4), QPointF(12, 15))
        p.drawPolyline(poly([(7, 11), (12, 16.5), (17, 11)]))
        p.drawLine(QPointF(5, 20), QPointF(19, 20))
    elif kind == "link":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawRoundedRect(QRectF(2.5, 8.5, 11, 7), 3.5, 3.5)
        p.drawRoundedRect(QRectF(10.5, 8.5, 11, 7), 3.5, 3.5)
    elif kind == "speaker":
        p.drawPolygon(poly([(4, 9), (8, 9), (13, 5), (13, 19), (8, 15), (4, 15)]))
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawArc(QRectF(10, 8, 7, 8), -60 * 16, 120 * 16)
        p.drawArc(QRectF(9, 4.5, 12, 15), -60 * 16, 120 * 16)
    elif kind == "full":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            x0, y0 = (4 if sx > 0 else 20), (4 if sy > 0 else 20)
            p.drawPolyline(poly([(x0 + 5 * sx, y0), (x0, y0), (x0, y0 + 5 * sy)]))
    elif kind == "crown":
        p.drawPolygon(poly([(3, 19), (3, 8), (8, 13), (12, 5), (16, 13), (21, 8), (21, 19)]))
    elif kind == "chat":
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawEllipse(QRectF(3, 3, 18, 16))
        p.setPen(Qt.NoPen); p.setBrush(fill)
        p.drawPolygon(poly([(6.5, 16), (3.5, 22), (10, 18.5)]))
        p.setBrush(Qt.NoBrush); p.setPen(stroke)
        p.drawArc(QRectF(8, 8, 8, 6), 200 * 16, 140 * 16)
    elif kind == "gear":
        for i in range(8):
            p.save(); p.translate(12, 12); p.rotate(i * 45)
            p.drawRoundedRect(QRectF(-2, -11, 4, 5), 1, 1)
            p.restore()
        p.drawEllipse(QRectF(5, 5, 14, 14))
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.drawEllipse(QRectF(9, 9, 6, 6))
    elif kind == "hd":
        p.drawRoundedRect(QRectF(1.5, 5, 21, 14), 3, 3)
        p.setPen(QColor(T["on_amber"]))
        f = QFont("Arial"); f.setPixelSize(10); f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(1.5, 5, 21, 14), Qt.AlignCenter, "HD")
    p.end()
    return QIcon(pm)


def icon_pixmap(kind: str, size: int = 28, color: str = T["amber"]) -> QPixmap:
    return make_icon(kind, color, size).pixmap(size, size)


def video_drop_paths(mime) -> list[str]:
    return [url.toLocalFile() for url in mime.urls()
            if url.isLocalFile() and url.toLocalFile().lower().endswith(VIDEO_EXT)]


class VideoPreview(QVideoWidget):
    """Handle file drops on the native video surface, including fullscreen."""
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if video_drop_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        paths = video_drop_paths(event.mimeData())
        if paths:
            event.acceptProposedAction()
            self.filesDropped.emit(paths)
        else:
            event.ignore()


# ------------------------------------------------------------------ Timeline
class Timeline(QWidget):
    seekRequested = Signal(float)
    inChanged = Signal(float)
    outChanged = Signal(float)
    PAD = 12

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(74)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.duration = 0.0
        self.pos = 0.0
        self.kf: list[float] = []
        self.t_in: float | None = None
        self.t_out: float | None = None
        self.segments: list[tuple[float, float]] = []
        self._drag: str | None = None

    def _x(self, t: float) -> float:
        w = self.width() - 2 * self.PAD
        return self.PAD + (t / self.duration * w if self.duration else 0)

    def _t(self, x: float) -> float:
        w = self.width() - 2 * self.PAD
        return min(max((x - self.PAD) / w, 0), 1) * self.duration if w > 0 else 0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bar = QRectF(self.PAD, 26, self.width() - 2 * self.PAD, 28)
        p.setPen(QPen(QColor("#2B2B30"), 1))
        p.setBrush(QColor(T["track"]))
        p.drawRoundedRect(bar, T.get("corner_radius", 0 if T["bg"] == "#C0C0C0" else 9), T.get("corner_radius", 0 if T["bg"] == "#C0C0C0" else 9))
        if self.duration <= 0:
            return
        p.setPen(QPen(QColor(T["tick"]), 1))
        if len(self.kf) < 700:
            for k in self.kf:
                x = self._x(k)
                p.drawLine(int(x), 47, int(x), 53)
        acc = QColor(T["amber"])
        p.setPen(Qt.NoPen)
        soft = QColor(acc)
        soft.setAlpha(90)
        p.setBrush(soft)
        for a, b in self.segments:
            p.drawRoundedRect(QRectF(self._x(a), 26, max(3, self._x(b) - self._x(a)), 28), 6, 6)
        if self.t_in is not None and self.t_out is not None and self.t_out > self.t_in:
            g = QLinearGradient(0, 26, 0, 54)
            g.setColorAt(0, QColor(T["amber2"]))
            g.setColorAt(1, QColor(T["amber_dark"]))
            p.setBrush(QBrush(g))
            p.drawRoundedRect(QRectF(self._x(self.t_in), 26, self._x(self.t_out) - self._x(self.t_in), 28), 6, 6)
        for t, col in ((self.t_in, T["in_col"]), (self.t_out, T["out_col"])):
            if t is not None:
                x = self._x(t)
                p.setPen(QPen(QColor(col), 4, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(int(x), 20, int(x), 60)
        x = self._x(self.pos)
        p.setPen(QPen(QColor(T["text"]), 2))
        p.drawLine(int(x), 12, int(x), 64)
        p.setBrush(QColor(T["text"]))
        p.drawEllipse(QRectF(x - 6, 5, 12, 12))
        p.setPen(QColor(T["muted"]))
        p.drawText(self.PAD, 72, "00:00")
        p.drawText(self.width() - self.PAD - 60, 72, fmt_t(self.duration)[:-4])

    def mousePressEvent(self, e):
        if self.duration <= 0:
            return
        x = e.position().x()
        for name, t in (("in", self.t_in), ("out", self.t_out)):
            if t is not None and abs(self._x(t) - x) < 8:
                self._drag = name
                return
        self._drag = "seek"
        self.seekRequested.emit(self._t(x))

    def mouseMoveEvent(self, e):
        if not self._drag:
            return
        t = self._t(e.position().x())
        if self._drag == "seek":
            self.seekRequested.emit(t)
        elif self._drag == "in":
            self.inChanged.emit(t)
        else:
            self.outChanged.emit(t)

    def mouseReleaseEvent(self, _):
        self._drag = None


# ------------------------------------------------------------------ widgets
class Dropdown(QComboBox):
    """Draw a text arrow without an external image asset."""

    def paintEvent(self, event):
        super().paintEvent(event)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        rect = self.style().subControlRect(
            QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxArrow, self)
        painter = QPainter(self)
        font = QFont("Segoe UI")
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor(T["text"] if self.isEnabled() else T["muted"]))
        painter.drawText(rect, Qt.AlignCenter, "▾")


class Switch(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        on = self.isChecked()
        if not self.isEnabled():
            p.setOpacity(0.45)
        p.setPen(QPen(QColor(T["amber"] if on else T["switch_border"]), 1))
        p.setBrush(QColor(T["amber"] if on else T["switch_off"]))
        p.drawRoundedRect(QRectF(1, 1, 44, 24), 12, 12)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFFFFF" if on else T["switch_thumb"]))
        p.drawEllipse(QRectF(23.5 if on else 3.5, 3.5, 19, 19))


class SegList(QListWidget):
    """Lista de trechos com mensagem quando esta vazia."""

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.count() == 0:
            p = QPainter(self.viewport())
            p.setRenderHint(QPainter.Antialiasing)
            r = self.viewport().rect()
            ic = icon_pixmap("play", 34, "#3A3A40")
            p.drawPixmap(r.center().x() - 17, r.center().y() - 46, ic)
            p.setPen(QColor(T["muted"]))
            p.drawText(r.adjusted(0, 18, 0, 0), Qt.AlignCenter,
                       "Seus trechos aparecerão aqui.\nMarque o começo e o fim no vídeo.")


PRESET_DETAILS_ROLE = int(Qt.UserRole) + 1


class PresetItemDelegate(QStyledItemDelegate):
    """Two-line popup rows; the closed combo keeps the preset name compact."""

    def sizeHint(self, option, index):
        return QSize(340, 58)

    def paint(self, painter, option, index):
        painter.save()
        selected = bool(option.state & (QStyle.State_Selected | QStyle.State_MouseOver))
        painter.fillRect(option.rect, QColor(T["sel_bg"] if selected else T["panel2"]))
        area = option.rect.adjusted(12, 5, -12, -5)
        font = QFont(option.font)
        font.setPixelSize(13)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF" if selected and T.get("light", T["bg"] == "#C0C0C0") and T["sel_bg"] in ("#000080", "#245EDB") else T["text"]))
        name = painter.fontMetrics().elidedText(index.data(Qt.DisplayRole) or "", Qt.ElideRight, area.width())
        painter.drawText(area.adjusted(0, 0, 0, -24), Qt.AlignLeft | Qt.AlignVCenter, name)
        font.setPixelSize(11)
        font.setWeight(QFont.Normal)
        painter.setFont(font)
        painter.setPen(QColor(("#DDDDDD" if selected and T["sel_bg"] in ("#000080", "#245EDB") else T["muted"]) if T.get("light", T["bg"] == "#C0C0C0") else "#B8B8B8"))
        details = painter.fontMetrics().elidedText(index.data(PRESET_DETAILS_ROLE) or "", Qt.ElideRight, area.width())
        painter.drawText(area.adjusted(0, 24, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, details)
        painter.restore()


class TitleBar(QFrame):
    """Compact window controls with native dragging and double-click maximize."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName("titleBar")
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)
        title = QLabel("Topneah Video Editor by Fergobirck")
        title.setObjectName("caption")
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(title)
        layout.addStretch()
        self.theme_selector = Dropdown()
        self.theme_selector.setObjectName("themeSelector")
        self.theme_selector.setAccessibleName("Tema")
        self.theme_selector.setToolTip("Tema do aplicativo")
        for key, label in THEME_LABELS.items():
            self.theme_selector.addItem(label, key)
        self.theme_selector.setFixedSize(120, 26)
        self.theme_selector.currentIndexChanged.connect(
            lambda _: window.apply_theme(self.theme_selector.currentData()))
        layout.addWidget(self.theme_selector)
        layout.addSpacing(6)
        self.minimize = self.control("−", "Minimizar", window.showMinimized)
        self.maximize = self.control("□", "Maximizar", self.toggle_maximized)
        self.close_button = self.control("×", "Fechar", window.close)
        self.close_button.setObjectName("windowClose")
        for button in (self.minimize, self.maximize, self.close_button):
            layout.addWidget(button)

    def control(self, text, tooltip, action):
        button = QPushButton(text)
        button.setObjectName("windowControl")
        button.setFixedSize(46, 32)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setFocusPolicy(Qt.NoFocus)
        button.clicked.connect(action)
        return button

    def toggle_maximized(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def sync_state(self):
        maximized = self.window.isMaximized()
        self.maximize.setText("❐" if maximized else "□")
        label = "Restaurar" if maximized else "Maximizar"
        self.maximize.setToolTip(label)
        self.maximize.setAccessibleName(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.window.windowHandle():
            self.window.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximized()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class DropZone(QFrame):
    """Area grande para soltar o video, com o logo."""
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(2)
        logo = self.logo = QLabel()
        logo.setPixmap(icon_pixmap("folder", 48, T["muted"]))
        logo.setAlignment(Qt.AlignCenter)
        t1 = QLabel("Arraste seu vídeo para cá")
        t1.setObjectName("dropTitle")
        t1.setAlignment(Qt.AlignCenter)
        t2 = QLabel("Ou clique para escolher o arquivo")
        t2.setObjectName("dropSub")
        t2.setAlignment(Qt.AlignCenter)
        self.btn = QPushButton("  Escolher vídeo")
        self.btn.setObjectName("primary")
        self.btn.setIcon(make_icon("folder", T["on_amber"], 24))
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setMinimumSize(260, 52)
        self.btn.setStyleSheet(f"font-family:{DISPLAY}; font-size:14px; letter-spacing:0px;")
        self.btn.clicked.connect(self.clicked.emit)
        cap = QLabel("Formatos: MP4, MOV, MKV, AVI, WEBM")
        cap.setObjectName("caption")
        cap.setAlignment(Qt.AlignCenter)
        lay.addStretch(1)
        lay.addWidget(logo, 0, Qt.AlignCenter)
        lay.addSpacing(6)
        lay.addWidget(t1)
        lay.addWidget(t2)
        lay.addSpacing(14)
        lay.addWidget(self.btn, 0, Qt.AlignCenter)
        lay.addSpacing(8)
        lay.addWidget(cap)
        lay.addStretch(1)

    def resizeEvent(self, e):
        self.logo.setVisible(self.height() >= 440)
        super().resizeEvent(e)

    def mousePressEvent(self, e):
        self.clicked.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setBrush(QColor(T["track"]))
        p.setPen(QPen(QColor(T["line"]), 1, Qt.DashLine))
        p.drawRoundedRect(r, 3, 3)



class PresetCard(QPushButton):
    def __init__(self, title: str, desc: str, icon_kind: str):
        super().__init__()
        self.setObjectName("preset")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(62)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 10, 8)
        lay.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(icon_pixmap(icon_kind, 30))
        ic.setFixedWidth(34)
        box = QVBoxLayout()
        box.setSpacing(0)
        a, b = QLabel(title), QLabel(desc)
        a.setObjectName("presetTitle")
        b.setObjectName("presetDesc")
        b.setWordWrap(True)
        box.addStretch()
        box.addWidget(a)
        box.addWidget(b)
        box.addStretch()
        lay.addWidget(ic)
        lay.addLayout(box, 1)
        for w in (ic, a, b):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)


# --------------------------------------------------------------- Threads
class Worker(QThread):
    progress = Signal(float)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, job):
        super().__init__()
        self.job = job
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            self.done.emit(self.job(self.progress.emit, lambda: self._cancel) or "Pronto.")
        except core.VideoError as e:
            self.failed.emit(str(e))
        except Exception:
            self.failed.emit(traceback.format_exc())


class KfLoader(QThread):
    ready = Signal(str, list)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            self.ready.emit(self.path, core.keyframes_cached(self.path))
        except Exception:
            self.ready.emit(self.path, [])


class GpuProbe(QThread):
    ready = Signal(bool)

    def run(self):
        try:
            self.ready.emit(core.nvenc_available())
        except Exception:
            self.ready.emit(False)


# ----------------------------------------------------------------- Presets
# chave: (titulo, descricao, icone, ExportSettings)
PRESETS = {
    "original": ("Original", "Sem perda · rápido", "crown", core.ExportSettings("copy")),
    "zap_leve": ("WhatsApp leve", "720p · 30 fps · 16 MB", "chat",
                 core.ExportSettings("encode", 720, 30, 2, 16.0)),
    "zap_hd": ("WhatsApp HD", "1080p · 30 fps · HD", "hd",
               core.ExportSettings("encode", 1080, 30, 1, None)),
    "custom": ("Personalizado", "Você escolhe tudo", "gear", core.ExportSettings("encode")),
}
FILE_TAG = {"original": "", "zap_leve": "_whatsapp", "zap_hd": "_whatsapp-hd", "custom": "_custom"}
RES_OPTS = [("Original", None), ("1080p", 1080), ("720p", 720), ("480p", 480)]
FPS_OPTS = [("Original", None), ("60 fps", 60), ("30 fps", 30), ("24 fps", 24)]
LIMIT_OPTS = [("Sem limite", None), ("8 MB", 8.0), ("16 MB (WhatsApp)", 16.0), ("25 MB", 25.0),
              ("50 MB", 50.0), ("100 MB", 100.0)]


def icon_button(kind: str, tip: str = "", size: int = 44, color: str = T["amber"]) -> QPushButton:
    b = QPushButton()
    b.setObjectName("iconbtn")
    b.setProperty("iconKind", kind)
    b.setProperty("iconColor", color)
    b.setProperty("iconPixels", 22)
    b.setIcon(make_icon(kind, color, 22))
    b.setFixedSize(size, size)
    b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    b.setFocusPolicy(Qt.NoFocus)
    return b


def with_icon(btn: QPushButton, kind: str, color: str = T["amber"], size: int = 20) -> QPushButton:
    btn.setProperty("iconKind", kind)
    btn.setProperty("iconColor", color)
    btn.setProperty("iconPixels", size)
    btn.setIcon(make_icon(kind, color, size))
    btn.setCursor(Qt.PointingHandCursor)
    return btn


# ------------------------------------------------------------------ Janela
class MainWindow(QWidget):
    def __init__(self, settings=None):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle(APP_NAME)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        scr = QApplication.primaryScreen().availableGeometry()
        w0, h0 = min(1300, int(scr.width() * 0.92)), min(860, int(scr.height() * 0.92))
        self.resize(w0, h0)
        self.move(scr.x() + (scr.width() - w0) // 2, scr.y() + (scr.height() - h0) // 2)
        self.setAcceptDrops(True)

        self.infos: dict[str, core.VideoInfo] = {}
        self.cur: str | None = None
        self.kf: list[float] = []
        self.preferences = settings if settings is not None else QSettings("Topneah", "VideoAPP")
        self.saved_presets = self.load_saved_presets()
        self.out_dir = self.preferences.value("output_directory", "") or None
        self.worker: Worker | None = None
        self.kf_loader: KfLoader | None = None
        self.gpu_ok = False
        self.preview_end: float | None = None
        self.t_in: float | None = None
        self.t_out: float | None = None
        self.preset = "original"
        self.save_mode = "cuts"

        # ---- player
        self.video = VideoPreview()
        self.video.filesDropped.connect(self.open_files)
        self.video.setMinimumSize(320, 180)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.positionChanged.connect(self.on_position)
        self.player.playbackStateChanged.connect(self.on_play_state)
        self.player.errorOccurred.connect(
            lambda *_: self.status("Não consegui mostrar a prévia deste vídeo, "
                                   "mas você ainda pode marcar os tempos e salvar."))

        self.title_bar = TitleBar(self)

        # ---- coluna esquerda
        self.lbl_hint = QLabel("")
        self.lbl_hint.setObjectName("hint")
        self.lbl_hint.setWordWrap(True)

        self.dropzone = DropZone()
        self.dropzone.clicked.connect(lambda: self.open_dialog())

        vf = QFrame()
        vf.setObjectName("videoFrame")
        vl = QVBoxLayout(vf)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.addWidget(self.video)
        self.vframe = vf
        vf.hide()

        self.btn_play = icon_button("play", "Play / Pause (Espaço)", 46)
        self.btn_play.clicked.connect(self.toggle_play)
        self.lbl_time = QLabel("00:00.000 / 00:00.000")
        self.lbl_time.setObjectName("value")
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(80)
        self.vol.setFixedWidth(110)
        self.vol.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        spk = QLabel()
        spk.setPixmap(icon_pixmap("speaker", 20, T["muted"]))
        self.btn_full = icon_button("full", "Tela cheia", 38, T["text"])
        self.btn_full.clicked.connect(lambda: self.cur and self.video.setFullScreen(True))
        self.btn_view = with_icon(QPushButton("  Ver só o trecho marcado"), "eye")
        self.btn_view.clicked.connect(self.view_selection)
        self.timeline = Timeline()
        self.timeline.seekRequested.connect(self.seek)
        self.timeline.inChanged.connect(lambda t: self.set_in(t, move=False))
        self.timeline.outChanged.connect(lambda t: self.set_out(t))

        self.btn_in = with_icon(QPushButton("  Marcar início"), "skip_in", T["text"])
        self.btn_out = with_icon(QPushButton("  Marcar fim"), "skip_out", T["text"])
        self.btn_in.clicked.connect(lambda: self.set_in(self.pos()))
        self.btn_out.clicked.connect(lambda: self.set_out(self.pos()))
        self.lbl_in = QLabel("--")
        self.lbl_out = QLabel("--")
        self.lbl_len = QLabel("")
        for l in (self.lbl_in, self.lbl_out, self.lbl_len):
            l.setObjectName("value")
        arrow = QLabel("→")
        arrow.setObjectName("dim")
        self.btn_add = with_icon(QPushButton("  Guardar este trecho"), "plus", T["amber2"])
        self.btn_add.setObjectName("outline")
        self.btn_add.clicked.connect(self.add_segment)
        caption = QLabel("Atalhos:  Espaço = play/pause  |  I = início  |  O = fim  |  Enter = guardar  |  "
                         "← → = quadro a quadro  |  Shift + ← → = 1 segundo")
        caption.setObjectName("caption")

        controls = QFrame()
        controls.setObjectName("card")
        cl = QVBoxLayout(controls)
        cl.setContentsMargins(16, 12, 16, 10)
        cl.setSpacing(4)
        r1 = QHBoxLayout()
        r1.setSpacing(12)
        r1.addWidget(self.btn_play)
        r1.addWidget(self.lbl_time)
        r1.addStretch()
        r1.addWidget(spk)
        r1.addWidget(self.vol)
        r1.addWidget(self.btn_full)
        r1.addSpacing(6)
        r1.addWidget(self.btn_view)
        cl.addLayout(r1)
        cl.addWidget(self.timeline)
        r2 = QHBoxLayout()
        r2.setSpacing(10)
        r2.addWidget(self.btn_in)
        r2.addWidget(self.lbl_in)
        r2.addWidget(arrow)
        r2.addWidget(self.btn_out)
        r2.addWidget(self.lbl_out)
        r2.addWidget(self.lbl_len)
        r2.addStretch()
        r2.addWidget(self.btn_add)
        cl.addLayout(r2)
        cl.addWidget(caption)

        left = QVBoxLayout()
        left.setSpacing(10)
        self.lbl_hint.hide()
        left.addWidget(self.dropzone, 1)
        left.addWidget(vf, 1)
        left.addWidget(controls)

        # ---- card 1: trechos
        self.cmb_videos = Dropdown()
        self.cmb_videos.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_videos.setMinimumContentsLength(10)
        self.cmb_videos.hide()
        self.cmb_videos.currentIndexChanged.connect(self.on_video_selected)
        self.list_segs = SegList()
        self.list_segs.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_segs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_segs.setTextElideMode(Qt.ElideMiddle)
        self.list_segs.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_segs.setMinimumHeight(110)
        self.list_segs.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.list_segs.itemDoubleClicked.connect(self.load_segment)
        self.list_segs.model().rowsMoved.connect(lambda *_: self.refresh_timeline_segments())
        self.list_segs.itemChanged.connect(lambda *_: self.update_buttons())
        self.btn_open = with_icon(QPushButton("  Abrir outro vídeo..."), "folder")
        self.btn_open.clicked.connect(lambda: self.open_dialog())
        self.btn_remove = with_icon(QPushButton("  Remover trecho"), "trash", "#FF8B78")
        self.btn_remove.setObjectName("danger")
        self.btn_remove.clicked.connect(self.remove_segments)

        c1, l1 = self.card("1", "Seus trechos", "Arraste para ordenar")
        l1.addWidget(self.cmb_videos)
        l1.addWidget(self.list_segs, 1)
        rr = QHBoxLayout()
        rr.setSpacing(8)
        rr.addWidget(self.btn_open, 1)
        rr.addWidget(self.btn_remove, 1)
        l1.addLayout(rr)

        # ---- card 2: qualidade
        self.cmb_preset = Dropdown()
        self.cmb_preset.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_preset.setMinimumContentsLength(12)
        self.cmb_preset.setItemDelegate(PresetItemDelegate(self.cmb_preset))
        self.cmb_preset.setMaxVisibleItems(8)
        self.cmb_preset.view().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.refresh_presets()
        self.btn_save_preset = QPushButton("Salvar preset...")
        self.btn_save_preset.clicked.connect(self.save_preset)
        self.btn_delete_preset = QPushButton("Excluir preset")
        self.btn_delete_preset.setObjectName("danger")
        self.btn_delete_preset.clicked.connect(self.delete_preset)

        self.cmb_res = Dropdown()
        self.cmb_fps = Dropdown()
        self.cmb_q = Dropdown()
        self.cmb_limit = Dropdown()
        for cmb, opts in ((self.cmb_res, RES_OPTS), (self.cmb_fps, FPS_OPTS), (self.cmb_limit, LIMIT_OPTS)):
            for lab, val in opts:
                cmb.addItem(lab, val)
        for i, lab in enumerate(core.QUALITY_LEVELS):
            self.cmb_q.addItem(lab, i)
        self.cmb_q.setCurrentIndex(1)
        self.chk_gpu = Switch()
        self.chk_gpu.setAccessibleName("Acelerar com a placa de vídeo (NVIDIA)")
        self.lbl_gpu = QLabel("Acelerar com a placa de vídeo (NVIDIA)")
        self.lbl_gpu.setWordWrap(True)
        self.lbl_gpu.setBuddy(self.chk_gpu)
        self.chk_gpu.setChecked(True)
        for c in (self.cmb_res, self.cmb_fps, self.cmb_q, self.cmb_limit):
            c.currentIndexChanged.connect(self.on_custom_changed)
        self.chk_gpu.toggled.connect(self.on_custom_changed)

        self.custom = QWidget()
        cg = QGridLayout(self.custom)
        cg.setContentsMargins(0, 2, 0, 0)
        cg.setHorizontalSpacing(10)
        cg.setVerticalSpacing(4)
        for col, (lab, w) in enumerate((("TAMANHO DO VÍDEO", self.cmb_res), ("FLUIDEZ (FPS)", self.cmb_fps))):
            l = QLabel(lab); l.setObjectName("h")
            cg.addWidget(l, 0, col); cg.addWidget(w, 1, col)
        for col, (lab, w) in enumerate((("QUALIDADE", self.cmb_q), ("LIMITE DE TAMANHO", self.cmb_limit))):
            l = QLabel(lab); l.setObjectName("h")
            cg.addWidget(l, 2, col); cg.addWidget(w, 3, col)
        gpu_row = QHBoxLayout()
        gpu_row.setSpacing(8)
        gpu_row.addWidget(self.chk_gpu)
        gpu_row.addWidget(self.lbl_gpu, 1)
        cg.addLayout(gpu_row, 4, 0, 1, 2)
        self.custom.hide()

        self.lbl_summary = QLabel("")
        self.lbl_summary.setObjectName("summary")
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setTextFormat(Qt.RichText)

        c2, l2 = self.card("2", "Qualidade do vídeo")
        l2.addWidget(self.cmb_preset)
        preset_actions = QHBoxLayout()
        preset_actions.addWidget(self.btn_save_preset)
        preset_actions.addWidget(self.btn_delete_preset)
        l2.addLayout(preset_actions)
        l2.addWidget(self.custom)
        l2.addWidget(self.lbl_summary)

        # ---- card 3: salvar
        self.btn_cut = with_icon(QPushButton("  Salvar cada trecho"), "download", T["on_amber"])
        self.btn_cut.setObjectName("mode")
        self.btn_merge = with_icon(QPushButton("  Juntar em um vídeo só"), "link", T["text"])
        self.btn_merge.setObjectName("mode")
        for b in (self.btn_cut, self.btn_merge):
            b.setCheckable(True)
        self.btn_cut.setChecked(True)
        mg = QButtonGroup(self)
        mg.setExclusive(True)
        mg.addButton(self.btn_cut)
        mg.addButton(self.btn_merge)
        self.btn_cut.clicked.connect(lambda: self.set_mode("cuts"))
        self.btn_merge.clicked.connect(lambda: self.set_mode("merge"))

        self.sw_audio = Switch()
        self.sw_audio.toggled.connect(lambda *_: self.update_buttons())
        lab_audio = QLabel("Só o áudio")
        lab_audio.setObjectName("value")
        self.cmb_audio = Dropdown()
        for lab in core.AUDIO_FORMATS:
            self.cmb_audio.addItem(lab)
        self.btn_outdir = with_icon(QPushButton("  Salvar em: mesma pasta do vídeo"), "folder", T["muted"], 18)
        self.btn_outdir.setObjectName("ghost")
        self.btn_outdir.clicked.connect(self.choose_outdir)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(lambda: self.worker and self.worker.cancel())
        self.btn_cancel.hide()
        self.lbl_status = QLabel("Pronto.")
        self.lbl_status.setObjectName("caption")
        self.lbl_status.setWordWrap(True)
        self.btn_start = with_icon(QPushButton("  INICIAR SALVAMENTO"), "download", T["on_amber"], 24)
        self.btn_start.setObjectName("primary")
        self.btn_start.setProperty("big", True)
        self.btn_start.setStyleSheet(f"font-family:{DISPLAY}; font-size:14px; letter-spacing:0px; padding:8px 14px;")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.clicked.connect(self.start_saving)

        c3, l3 = self.card("3", "Salvar")
        rv = QHBoxLayout()
        rv.setSpacing(8)
        rv.addWidget(self.btn_cut, 1)
        rv.addWidget(self.btn_merge, 1)
        l3.addLayout(rv)
        ra = QHBoxLayout()
        ra.setSpacing(10)
        ra.addWidget(self.sw_audio)
        ra.addWidget(lab_audio)
        ra.addWidget(self.cmb_audio, 1)
        l3.addLayout(ra)
        l3.addWidget(self.btn_outdir)
        pr = QHBoxLayout()
        pr.addWidget(self.progress, 1)
        pr.addWidget(self.btn_cancel)
        l3.addLayout(pr)
        l3.addWidget(self.lbl_status)
        l3.addWidget(self.btn_start)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(c1, 1)
        right.addWidget(c2)
        right.addWidget(c3)
        inner_p = QWidget()
        inner_p.setLayout(right)
        panel = QScrollArea()
        panel.setWidget(inner_p)
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        panel.setFixedWidth(424)
        panel.viewport().setAutoFillBackground(False)
        inner_p.setAutoFillBackground(False)

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addLayout(left, 1)
        body.addWidget(panel)
        root = QVBoxLayout(self)
        root.setSizeConstraint(QVBoxLayout.SetNoConstraint)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.title_bar)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(16, 12, 16, 14)
        il.addLayout(body, 1)
        body_scroll = QScrollArea()
        body_scroll.setWidget(inner)
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QFrame.NoFrame)
        body_scroll.viewport().setAutoFillBackground(False)
        inner.setAutoFillBackground(False)
        root.addWidget(body_scroll, 1)
        self.setMinimumSize(820, 520)

        # ---- atalhos
        def sc(key, fn):
            s = QShortcut(QKeySequence(key), self)
            s.setContext(Qt.ApplicationShortcut)
            s.activated.connect(fn)
        sc(Qt.Key_Space, self.toggle_play)
        sc(Qt.Key_I, lambda: self.set_in(self.pos()))
        sc(Qt.Key_O, lambda: self.set_out(self.pos()))
        sc(Qt.Key_Return, self.add_segment)
        sc(Qt.Key_Left, lambda: self.step(-1))
        sc(Qt.Key_Right, lambda: self.step(1))
        sc("Shift+Left", lambda: self.step(-60))
        sc("Shift+Right", lambda: self.step(60))
        for b in (self.btn_in, self.btn_out, self.btn_add, self.btn_view):
            b.setFocusPolicy(Qt.NoFocus)

        self.cmb_preset.currentIndexChanged.connect(
            lambda _: self.select_preset(self.cmb_preset.currentData()))
        self.apply_preset_settings(self.load_custom_settings())
        self.select_preset(self.preferences.value("last_preset", "original"))
        self.update_output_directory_label()
        self.apply_theme(self.preferences.value("theme", "dark"))
        self.gpu_probe = GpuProbe()
        self.gpu_probe.ready.connect(self.on_gpu)
        self.gpu_probe.start()
        self.update_buttons()

    def apply_theme(self, theme):
        theme = activate_theme(theme)
        self.theme = theme
        self.setStyleSheet(build_style(theme))
        xp = theme == "xp"
        self.title_bar.layout().setSpacing(5 if xp else 0)
        self.title_bar.layout().setContentsMargins(12, 0, 6 if xp else 0, 0)
        for control in (self.title_bar.minimize, self.title_bar.maximize, self.title_bar.close_button):
            control.setFixedSize(34 if xp else 46, 26 if xp else 32)
        selector = self.title_bar.theme_selector
        selector.blockSignals(True)
        selector.setCurrentIndex(selector.findData(theme))
        selector.blockSignals(False)
        # Rebuild cached icon pixmaps for the new background contrast.
        for button in self.findChildren(QPushButton):
            kind = button.property("iconKind")
            if kind:
                color = button.property("iconColor")
                if theme != "dark":
                    primary = button.objectName() == "primary" or (button.objectName() == "mode" and button.isChecked())
                    color = T["on_amber"] if theme in ("win9x_flat", "xp", "light") and primary else T["text"]
                button.setIcon(make_icon(kind, color, button.property("iconPixels")))
        self.dropzone.logo.setPixmap(icon_pixmap("folder", 48, T["muted"]))
        self.dropzone.btn.setIcon(make_icon("folder", T["text"] if theme == "win9x" else T["on_amber"], 24))
        self.set_mode(self.save_mode)
        self.on_play_state()
        self.update_summary()
        self.preferences.setValue("theme", theme)
        self.preferences.sync()
        for widget in self.findChildren(QWidget):
            widget.update()
        self.update()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange and hasattr(self, "title_bar"):
            self.title_bar.sync_state()

    def nativeEvent(self, event_type, message):
        # Native hit testing retains edge/corner resizing for the frameless HWND.
        if sys.platform == "win32" and not self.isMaximized() and not self.isFullScreen():
            import ctypes
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                rect = wintypes.RECT()
                user32 = ctypes.windll.user32
                user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
                user32.GetWindowRect.restype = wintypes.BOOL
                if user32.GetWindowRect(msg.hWnd, ctypes.byref(rect)):
                    x = ctypes.c_short(msg.lParam & 0xffff).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xffff).value
                    border = max(5, round(6 * self.devicePixelRatioF()))
                    left, right = x < rect.left + border, x >= rect.right - border
                    top, bottom = y < rect.top + border, y >= rect.bottom - border
                    hit = (13 if left else 14 if right else 12) if top else (
                        (16 if left else 17 if right else 15) if bottom else (
                            10 if left else 11 if right else 0))
                    if hit:
                        return True, hit
        return super().nativeEvent(event_type, message)

    # ------------------------------------------------------------ montagem
    def card(self, num: str, title: str, sub: str = ""):
        f = QFrame()
        f.setObjectName("card")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(16, 12, 16, 14)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.setSpacing(10)
        n = QLabel(num)
        n.setObjectName("num")
        n.setAlignment(Qt.AlignCenter)
        n.setFixedSize(30, 30)
        h = QLabel(title.upper())
        h.setObjectName("sectionTitle")
        head.addWidget(n)
        head.addWidget(h)
        if sub:
            s = QLabel(sub)
            s.setObjectName("caption")
            s.setWordWrap(True)
            head.addWidget(s, 1)
        else:
            head.addStretch()
        lay.addLayout(head)
        return f, lay

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(T["bg"]))

    def on_gpu(self, ok: bool):
        self.gpu_ok = ok
        self.lbl_gpu.setText("Acelerar com a placa de vídeo (NVIDIA)" if ok
                             else "Placa NVIDIA não encontrada (usando o processador)")
        self.chk_gpu.setEnabled(ok)
        self.lbl_gpu.setEnabled(ok)
        self.chk_gpu.setToolTip(self.lbl_gpu.text())
        self.update_summary()

    def on_play_state(self, *_):
        playing = self.player.playbackState() == QMediaPlayer.PlayingState
        self.btn_play.setIcon(make_icon("pause" if playing else "play", T["amber"], 22))

    # ------------------------------------------------------------ util
    def status(self, msg: str):
        self.lbl_status.setText(msg)

    def pos(self) -> float:
        return self.player.position() / 1000.0

    def duration(self) -> float:
        return self.infos[self.cur].duration if self.cur else 0.0

    def fps(self) -> float:
        return (self.infos[self.cur].fps or 30.0) if self.cur else 30.0

    def busy(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def is_copy(self) -> bool:
        return self.preset == "original"

    def set_mode(self, mode: str):
        self.save_mode = mode
        if getattr(self, "theme", "dark") == "win9x":
            self.btn_cut.setIcon(make_icon("download", T["text"], 20))
            self.btn_merge.setIcon(make_icon("link", T["text"], 20))
            return
        self.btn_cut.setIcon(make_icon("download", T["on_amber"] if mode == "cuts" else T["text"], 20))
        self.btn_merge.setIcon(make_icon("link", T["on_amber"] if mode == "merge" else T["text"], 20))

    # ------------------------------------------------------------ presets
    @staticmethod
    def decode_preset(data):
        settings = core.ExportSettings(**data)
        if (settings.mode not in ("copy", "encode")
                or settings.height not in [v for _, v in RES_OPTS]
                or settings.fps not in [v for _, v in FPS_OPTS]
                or settings.max_mb not in [v for _, v in LIMIT_OPTS]
                or type(settings.quality) is not int or not 0 <= settings.quality <= 3
                or type(settings.use_gpu) is not bool):
            raise ValueError("Invalid preset")
        return settings

    def load_saved_presets(self):
        try:
            data = json.loads(self.preferences.value("saved_presets", "{}"))
            result = {}
            for key, entry in data.items():
                try:
                    if not key.startswith("saved:") or not isinstance(entry["name"], str) or not entry["name"].strip():
                        continue
                    self.decode_preset(entry["settings"])
                    result[key] = entry
                except (TypeError, ValueError, KeyError):
                    continue
            return result
        except (TypeError, ValueError, AttributeError):
            return {}

    def load_custom_settings(self):
        try:
            return self.decode_preset(json.loads(self.preferences.value("custom_settings", "{}")))
        except (TypeError, ValueError):
            return core.ExportSettings(mode="encode")

    @staticmethod
    def preset_details(settings):
        if settings.mode == "copy":
            return "Resolução e FPS originais · Sem recompressão"
        resolution = f"Até {settings.height}p" if settings.height else "Resolução original"
        fps = f"Até {settings.fps} fps" if settings.fps else "FPS original"
        limit = f"{settings.max_mb:g} MB" if settings.max_mb else "Sem limite"
        return f"{resolution} · {fps} · {core.QUALITY_LEVELS[settings.quality]} · {limit}"

    def set_preset_details(self, row, settings):
        details = self.preset_details(settings)
        self.cmb_preset.setItemData(row, details, PRESET_DETAILS_ROLE)
        self.cmb_preset.setItemData(row, self.cmb_preset.itemText(row) + "\n" + details, Qt.ToolTipRole)
        self.cmb_preset.setItemData(row, details, Qt.AccessibleDescriptionRole)

    def refresh_presets(self):
        self.cmb_preset.blockSignals(True)
        self.cmb_preset.clear()
        for key, (title, _, _, settings) in PRESETS.items():
            self.cmb_preset.addItem(title, key)
            if key == "custom":
                settings = self.load_custom_settings()
            self.set_preset_details(self.cmb_preset.count() - 1, settings)
        for key, entry in self.saved_presets.items():
            self.cmb_preset.addItem(entry["name"], key)
            self.set_preset_details(self.cmb_preset.count() - 1, self.decode_preset(entry["settings"]))
        self.cmb_preset.blockSignals(False)

    def apply_preset_settings(self, settings):
        for control, value in ((self.cmb_res, settings.height), (self.cmb_fps, settings.fps),
                               (self.cmb_q, settings.quality), (self.cmb_limit, settings.max_mb)):
            control.blockSignals(True)
            control.setCurrentIndex(max(0, control.findData(value)))
            control.blockSignals(False)
        self.chk_gpu.blockSignals(True)
        self.chk_gpu.setChecked(settings.use_gpu)
        self.chk_gpu.blockSignals(False)

    def persist_preferences(self):
        self.preferences.setValue("last_preset", self.preset)
        self.preferences.setValue("output_directory", self.out_dir or "")
        self.preferences.setValue("saved_presets", json.dumps(self.saved_presets, ensure_ascii=False))
        if self.preset == "custom":
            self.set_preset_details(self.cmb_preset.findData("custom"), self.build_settings())
            self.preferences.setValue("custom_settings", json.dumps(asdict(self.build_settings())))
        self.preferences.sync()

    def select_preset(self, key: str):
        if key not in PRESETS and key not in self.saved_presets:
            key = "original"
        self.preset = key
        self.cmb_preset.blockSignals(True)
        self.cmb_preset.setCurrentIndex(self.cmb_preset.findData(key))
        self.cmb_preset.blockSignals(False)
        if key in self.saved_presets:
            self.apply_preset_settings(self.decode_preset(self.saved_presets[key]["settings"]))
        elif key != "custom" and PRESETS[key][3].mode == "encode":
            self.apply_preset_settings(PRESETS[key][3])
        self.custom.setVisible(key == "custom" or key in self.saved_presets)
        self.btn_delete_preset.setEnabled(key in self.saved_presets)
        self.btn_save_preset.setEnabled(not self.is_copy())
        self.update_buttons()
        self.persist_preferences()

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Salvar preset", "Nome do preset:")
        name = name.strip()
        if not ok or not name:
            return
        if any(name.casefold() == title.casefold() for title, *_ in PRESETS.values()):
            QMessageBox.warning(self, APP_NAME, "Escolha um nome diferente dos presets padrão.")
            return
        key = next((key for key, entry in self.saved_presets.items()
                    if entry["name"].casefold() == name.casefold()), None)
        if key is not None:
            if QMessageBox.question(self, APP_NAME, f'Substituir o preset "{name}"?') != QMessageBox.Yes:
                return
        else:
            key = "saved:" + uuid.uuid4().hex
        self.saved_presets[key] = {"name": name, "settings": asdict(self.build_settings())}
        self.refresh_presets()
        self.select_preset(key)
        self.status(f'Preset "{name}" salvo.')

    def delete_preset(self):
        key = self.preset
        if key not in self.saved_presets:
            return
        name = self.saved_presets[key]["name"]
        if QMessageBox.question(self, APP_NAME, f'Excluir o preset "{name}"?') != QMessageBox.Yes:
            return
        del self.saved_presets[key]
        self.refresh_presets()
        self.select_preset("custom")
        self.status(f'Preset "{name}" excluído.')

    def on_custom_changed(self, *_):
        if self.preset != "custom":
            self.select_preset("custom")
        else:
            self.update_summary()
            self.persist_preferences()

    def build_settings(self) -> core.ExportSettings:
        if self.is_copy():
            return core.ExportSettings("copy")
        return core.ExportSettings(
            "encode", self.cmb_res.currentData(), self.cmb_fps.currentData(),
            self.cmb_q.currentData(), self.cmb_limit.currentData(),
            self.chk_gpu.isChecked(),
        )

    def selection_duration(self) -> float:
        segs = self.checked_segments()
        if segs:
            return sum(s["end"] - s["start"] for s in segs)
        if self.t_in is not None and self.t_out is not None:
            return self.t_out - self.t_in
        return self.duration()

    def update_summary(self):
        if not self.cur:
            self.lbl_summary.setText("Abra um vídeo para ver o resultado aqui.")
            return
        info = self.infos[self.cur]
        dur = self.selection_duration()
        if self.is_copy():
            if info.vbitrate:
                est = (info.vbitrate + 196_000) / 8 * dur / 1e6
            else:
                est = os.path.getsize(self.cur) / max(info.duration, 1) * dur / 1e6
            self.lbl_summary.setText(
                f"<b>Mesma qualidade do original</b>, sem recompressão.<br>"
                f"{info.width}×{info.height} · {info.fps:.0f} fps · ≈ {est:.0f} MB para {dur:.0f} s<br>"
                f"<span style='color:{T['muted']}'>O início do corte ajusta para o ponto mais próximo "
                f"(a cada ~0,5 s) para não perder qualidade.</span>")
            return
        s = self.build_settings()
        w, h, fps = core.target_dims(info, s)
        kbps = core.plan_kbps(s, dur)
        lines = [f"<b>{w}×{h} · {fps:g} fps</b> · " +
                 (f"até {s.max_mb:g} MB" if kbps else f"qualidade {core.QUALITY_LEVELS[s.quality].lower()}")]
        if kbps:
            lines.append(f"Vídeo com ≈ {kbps / 1000:.1f} Mbps para {dur:.0f} s")
            if kbps < w * h * fps * 0.03 / 1000:
                lines.append(f"<span style='color:{T['warn']}'><b>Muito comprimido:</b> pode ficar borrado. "
                             f"Escolha um trecho menor ou um limite maior.</span>")
        muted = f"color:{T['muted']}"
        if self.preset == "zap_leve":
            lines.append(f"<span style='{muted}'>Pensado para o limite de 16 MB do envio normal.</span>")
        elif self.preset == "zap_hd":
            lines.append(f"<span style='{muted}'>Dica: no WhatsApp, envie como <b>Documento</b> "
                         f"para ele não comprimir de novo.</span>")
        gpu = s.use_gpu and self.gpu_ok
        lines.append(f"<span style='{muted}'>" +
                     ("Usando a placa NVIDIA (rápido)." if gpu else "Usando o processador.") + "</span>")
        self.lbl_summary.setText("<br>".join(lines))

    def update_hint(self):
        if not self.cur:
            msg = "Comece abrindo um vídeo: arraste o arquivo para a janela."
        elif self.t_in is None and not self.segments():
            msg = ("<b>Passo 1:</b> ache o começo do pedaço que você quer "
                   "(clique na barra ou use as setas) e aperte <b>I</b>.")
        elif self.t_in is None:
            msg = "Trecho guardado! Marque outro com <b>I</b> e <b>O</b>, ou escolha a qualidade e salve à direita."
        elif self.t_out is None:
            msg = "<b>Passo 2:</b> agora ache o fim do pedaço e aperte <b>O</b>."
        else:
            msg = "<b>Passo 3:</b> aperte <b>Enter</b> para guardar este trecho. Depois você pode marcar outros."
        self.lbl_hint.setText(msg)

    def update_buttons(self):
        self.update_hint()
        self.update_summary()
        have = self.cur is not None
        free = not self.busy()
        n_checked = len(self.checked_segments())
        audio_only = self.sw_audio.isChecked()
        marks = have and self.t_in is not None and self.t_out is not None
        self.btn_add.setEnabled(marks)
        self.btn_view.setEnabled(marks)
        self.btn_cut.setEnabled(not audio_only)
        self.btn_merge.setEnabled(not audio_only)
        self.cmb_audio.setEnabled(audio_only)
        self.btn_start.setEnabled(free and (have if audio_only else n_checked > 0))
        self.btn_remove.setEnabled(self.list_segs.count() > 0)

    # ------------------------------------------------------------ abrir
    def dragEnterEvent(self, e):
        if video_drop_paths(e.mimeData()):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        self.dragEnterEvent(e)

    def dropEvent(self, e):
        paths = video_drop_paths(e.mimeData())
        if paths:
            e.acceptProposedAction()
            self.open_files(paths)
        else:
            e.ignore()
            self.status("Esse arquivo não parece ser um vídeo.")

    def open_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Abrir vídeo", "", "Vídeos (*" + " *".join(VIDEO_EXT) + ")")
        if files:
            self.open_files(files)

    def open_files(self, paths: list[str]):
        first = None
        for p in paths:
            if p in self.infos:
                first = first or p
                continue
            try:
                info = core.probe(p)
            except core.VideoError as ex:
                QMessageBox.warning(self, APP_NAME, str(ex))
                continue
            self.infos[p] = info
            self.cmb_videos.blockSignals(True)
            self.cmb_videos.addItem(f"{os.path.basename(p)}   ·   {info.describe()}", p)
            self.cmb_videos.blockSignals(False)
            first = first or p
        if first:
            self.cmb_videos.show()
            idx = self.cmb_videos.findData(first)
            self.cmb_videos.blockSignals(True)
            self.cmb_videos.setCurrentIndex(idx)
            self.cmb_videos.blockSignals(False)
            self.on_video_selected(idx)

    def on_video_selected(self, row: int):
        if row < 0:
            return
        path = self.cmb_videos.itemData(row)
        if not path or path == self.cur:
            return
        self.cur = path
        self.dropzone.hide()
        self.vframe.show()
        self.t_in = self.t_out = None
        self.lbl_in.setText("--"); self.lbl_out.setText("--"); self.lbl_len.setText("")
        self.kf = []
        info = self.infos[path]
        self.timeline.duration = info.duration
        self.timeline.kf = []
        self.timeline.t_in = self.timeline.t_out = None
        self.refresh_timeline_segments()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.pause()
        self.player.setPosition(0)
        self.status(f"{os.path.basename(path)} - {info.describe()}  (analisando o vídeo...)")
        self.kf_loader = KfLoader(path)
        self.kf_loader.ready.connect(self.on_keyframes)
        self.kf_loader.start()
        self.update_buttons()

    def on_keyframes(self, path: str, kfs: list):
        if path != self.cur:
            return
        self.kf = kfs
        self.timeline.kf = kfs
        self.timeline.update()
        step = (kfs[1] - kfs[0]) if len(kfs) > 1 else 0
        self.status(f"{os.path.basename(path)} · {self.infos[path].describe()} · "
                    f"pontos de corte a cada ~{step:.1f}s")

    # ------------------------------------------------------------ player
    def toggle_play(self):
        if not self.cur:
            return
        self.preview_end = None
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek(self, t: float):
        self.player.setPosition(int(max(0, min(t, self.duration())) * 1000))

    def step(self, n: int):
        if not self.cur:
            return
        self.player.pause()
        self.seek(self.pos() + n / self.fps())

    def on_position(self, ms: int):
        t = ms / 1000.0
        self.timeline.pos = t
        self.timeline.update()
        self.lbl_time.setText(f"{fmt_t(t)} / {fmt_t(self.duration())}")
        if self.preview_end is not None and t >= self.preview_end:
            self.player.pause()
            self.preview_end = None

    # ------------------------------------------------------------ marcar
    def set_in(self, t: float, move: bool = True):
        if not self.cur:
            return
        if self.is_copy() and self.kf:      # sem perda: o inicio so pode ser um keyframe
            t = core.snap_start(self.kf, t)
        self.t_in = t
        if self.t_out is not None and self.t_out <= t:
            self.t_out = None
        self.refresh_marks()
        if move:
            self.seek(t)

    def set_out(self, t: float):
        if not self.cur:
            return
        t = min(t, self.duration())
        if self.t_in is not None and t <= self.t_in:
            return
        self.t_out = t
        self.refresh_marks()

    def refresh_marks(self):
        self.timeline.t_in, self.timeline.t_out = self.t_in, self.t_out
        self.timeline.update()
        self.lbl_in.setText(fmt_t(self.t_in) if self.t_in is not None else "--")
        self.lbl_out.setText(fmt_t(self.t_out) if self.t_out is not None else "--")
        self.lbl_len.setText(f"   =  {self.t_out - self.t_in:.2f} s"
                             if self.t_in is not None and self.t_out is not None else "")
        self.update_buttons()

    def view_selection(self):
        if self.t_in is None or self.t_out is None:
            return
        self.seek(self.t_in)
        self.preview_end = self.t_out
        self.player.play()

    # ------------------------------------------------------------ trechos
    def add_segment(self):
        if not (self.cur and self.t_in is not None and self.t_out is not None):
            return
        n = self.list_segs.count() + 1
        it = QListWidgetItem()
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        it.setCheckState(Qt.Checked)
        it.setData(Qt.UserRole, {"src": self.cur, "start": self.t_in, "end": self.t_out})
        it.setText(self._seg_text(self.cur, self.t_in, self.t_out, n))
        self.list_segs.addItem(it)
        self.t_in = self.t_out = None
        self.refresh_marks()
        self.refresh_timeline_segments()
        self.status(f"Trecho {n} guardado.")

    @staticmethod
    def _seg_text(src, a, b, n):
        nm = os.path.splitext(os.path.basename(src))[0]
        nm = nm if len(nm) <= 30 else nm[:14] + "…" + nm[-14:]
        return (f"{n}.  {nm}\n"
                f"      {fmt_t(a)}  →  {fmt_t(b)}    ({b - a:.2f} s)")

    def segments(self, only_checked=False):
        out = []
        for i in range(self.list_segs.count()):
            it = self.list_segs.item(i)
            if only_checked and it.checkState() != Qt.Checked:
                continue
            out.append(it.data(Qt.UserRole))
        return out

    def checked_segments(self):
        return self.segments(only_checked=True)

    def remove_segments(self):
        for it in self.list_segs.selectedItems():
            self.list_segs.takeItem(self.list_segs.row(it))
        self.refresh_timeline_segments()

    def renumber(self):
        for i in range(self.list_segs.count()):
            d = self.list_segs.item(i).data(Qt.UserRole)
            self.list_segs.item(i).setText(self._seg_text(d["src"], d["start"], d["end"], i + 1))

    def refresh_timeline_segments(self):
        self.renumber()
        self.timeline.segments = [(d["start"], d["end"]) for d in self.segments() if d["src"] == self.cur]
        self.timeline.update()
        self.update_buttons()

    def load_segment(self, item):
        d = item.data(Qt.UserRole)
        idx = self.cmb_videos.findData(d["src"])
        if idx >= 0 and d["src"] != self.cur:
            self.cmb_videos.blockSignals(True)
            self.cmb_videos.setCurrentIndex(idx)
            self.cmb_videos.blockSignals(False)
            self.on_video_selected(idx)
        self.t_in, self.t_out = d["start"], d["end"]
        self.refresh_marks()
        self.seek(d["start"])

    # ------------------------------------------------------------ saida
    def update_output_directory_label(self):
        d = self.out_dir
        self.btn_outdir.setText("  Salvar em: " + (d if len(d) < 38 else "..." + d[-35:])
                                if d else "  Salvar em: mesma pasta do vídeo")
        self.btn_outdir.setToolTip(d or "Mesma pasta do vídeo")

    def choose_outdir(self):
        d = QFileDialog.getExistingDirectory(self, "Salvar em", self.out_dir or "")
        if d:
            self.out_dir = d
            self.update_output_directory_label()
            self.persist_preferences()

    def folder_for(self, src: str) -> str:
        d = self.out_dir or os.path.dirname(src)
        os.makedirs(d, exist_ok=True)
        return d

    # ------------------------------------------------------------ exportar
    def start_saving(self):
        if self.sw_audio.isChecked():
            self.export_audio()
        elif self.save_mode == "merge":
            self.export_merge()
        else:
            self.export_cuts()

    def run_job(self, job, label: str, open_folder: str | None):
        if self.busy():
            return
        self.progress.setValue(0)
        self.btn_cancel.show()
        self.status(label)
        w = Worker(job)
        self.worker = w
        w.progress.connect(lambda f: self.progress.setValue(int(f * 1000)))

        def finish(msg, ok=True):
            self.btn_cancel.hide()
            self.status(msg)
            if ok:
                self.progress.setValue(1000)
            self.update_buttons()
            if ok and open_folder and QMessageBox.question(
                    self, APP_NAME, msg + "\n\nAbrir a pasta?") == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(open_folder))
            elif not ok:
                QMessageBox.warning(self, APP_NAME, msg)

        w.done.connect(lambda m: finish(m, True))
        w.failed.connect(lambda m: finish(m, False))
        w.start()
        self.update_buttons()

    def export_cuts(self):
        segs = self.checked_segments()
        settings = self.build_settings()
        tag = FILE_TAG.get(self.preset, "_custom")
        folder = self.folder_for(segs[0]["src"])
        outs = []

        def job(prog, cancel):
            total = len(segs)
            for i, s in enumerate(segs):
                stem = os.path.splitext(os.path.basename(s["src"]))[0]
                out = core.unique_path(self.folder_for(s["src"]), f"{stem}_corte{i + 1}{tag}", ".mp4")
                core.cut(s["src"], s["start"], s["end"], out, settings,
                         cb=lambda f, i=i: prog((i + f) / total), cancel=cancel)
                outs.append(out)
            return f"{len(outs)} arquivo(s) salvo(s) em {os.path.dirname(outs[-1])}"
        self.run_job(job, "Salvando os trechos...", folder)

    def export_merge(self):
        segs = self.checked_segments()
        settings = self.build_settings()
        folder = self.folder_for(segs[0]["src"])
        stem = os.path.splitext(os.path.basename(segs[0]["src"]))[0]
        out = core.unique_path(folder, f"{stem}_mesclado{FILE_TAG.get(self.preset, "_custom")}", ".mp4")
        clips = [core.Clip(s["src"], s["start"], s["end"]) for s in segs]
        reencode = False
        if settings.mode == "copy":
            try:
                sigs = {core.probe(c.src).signature() for c in clips}
            except core.VideoError as ex:
                QMessageBox.warning(self, APP_NAME, str(ex))
                return
            if len(sigs) > 1:
                r = QMessageBox.question(
                    self, APP_NAME,
                    "Os trechos têm formatos diferentes (resolução, fps ou codec).\n"
                    "Para juntar, o app precisa recodificar (alta qualidade, mais lento).\n\nContinuar?")
                if r != QMessageBox.Yes:
                    return
                reencode = True

        def job(prog, cancel):
            lossless = core.merge(clips, out, settings, reencode, cb=prog, cancel=cancel)
            return f"Vídeo salvo ({'sem perda' if lossless else 'recodificado'}): {out}"
        self.run_job(job, "Juntando os trechos...", folder)

    def export_audio(self):
        segs = self.checked_segments()          # trechos marcados -> marca atual -> video todo
        if not segs and self.cur and self.t_in is not None and self.t_out is not None:
            segs = [{"src": self.cur, "start": self.t_in, "end": self.t_out}]
        if not segs and self.cur:
            segs = [{"src": self.cur, "start": 0.0, "end": self.duration()}]
        kind, ext = core.AUDIO_FORMATS[self.cmb_audio.currentText()]
        folder = self.folder_for(segs[0]["src"])

        def job(prog, cancel):
            total, last = len(segs), ""
            for i, s in enumerate(segs):
                stem = os.path.splitext(os.path.basename(s["src"]))[0]
                out = core.unique_path(self.folder_for(s["src"]), f"{stem}_audio{i + 1}", "." + ext)
                core.extract_audio(s["src"], s["start"], s["end"], out, kind,
                                   cb=lambda f, i=i: prog((i + f) / total), cancel=cancel)
                last = out
            return f"{total} áudio(s) salvo(s) em {os.path.dirname(last)}"
        self.run_job(job, "Extraindo o áudio...", folder)

    def closeEvent(self, e):
        self.persist_preferences()
        if self.busy():
            self.worker.cancel()
            self.worker.wait(3000)
        e.accept()


def main():
    try:  # icone proprio na barra de tarefas do Windows
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Topneah.VideoAPP")
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(make_app_icon())
    base = QFont("Segoe UI", 10)
    base.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(base)
    w = MainWindow()
    w.show()
    for a in sys.argv[1:]:
        if os.path.isfile(a) and a.lower().endswith(VIDEO_EXT):
            w.open_files([os.path.abspath(a)])
    sys.exit(app.exec())


def _log_crash(exc_type, exc, tb):
    # roda sem janela preta: erros vao para erro.txt (ao lado do app)
    try:
        base = os.environ.get("LOCALAPPDATA") or os.path.dirname(os.path.abspath(__file__))
        os.makedirs(os.path.join(base, "Topneah Video APP"), exist_ok=True)
        with open(os.path.join(base, "Topneah Video APP", "erro.txt"), "w",
                  encoding="utf-8") as f:
            f.write("".join(traceback.format_exception(exc_type, exc, tb)))
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)


if __name__ == "__main__":
    sys.excepthook = _log_crash
    main()
