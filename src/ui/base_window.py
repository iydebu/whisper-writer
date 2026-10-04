"""
Shared frame for WhisperWriter's own windows (main, settings, about): no system title bar,
a rounded dark panel with a neon edge, a header row with the app name and a close button,
and click-and-drag anywhere to move it.
"""
from PyQt5.QtCore import Qt, QPoint, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow

from ui.styles import COLORS, FONTS, get_button_style, get_label_style

CORNER = 12


class DragToMove:
    """Mixin: hold the left mouse button anywhere on a frameless window to move it."""
    _grab = None    # cursor offset from the window corner while a drag is active

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        self._grab = event.globalPos() - self.pos()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._grab is None or not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)
        self.move(event.globalPos() - self._grab)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._grab = None
        super().mouseReleaseEvent(event)


class NeonWindow(DragToMove, QMainWindow):
    """Base for the app's panels. Subclasses add their widgets to `self.body`."""

    def __init__(self, title, width, height):
        super().__init__(windowTitle=title)
        self.setFixedSize(width, height)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        holder = QWidget(self)
        self.body = QVBoxLayout(holder)
        self.body.setContentsMargins(16, 12, 16, 16)
        self.body.setSpacing(8)
        self.body.addLayout(self._header())
        self.setCentralWidget(holder)
        self._centre_on_screen()

    def _header(self):
        """App name in the middle, a small x button on the right."""
        self.title_label = QLabel('WHISPERWRITER')
        self.title_label.setFont(QFont(FONTS['family'], FONTS['size_title'], QFont.Bold))
        self.title_label.setStyleSheet(get_label_style('title'))
        self.title_label.setAlignment(Qt.AlignCenter)

        x_btn = QPushButton('\u2715')
        x_btn.setFixedSize(28, 28)
        x_btn.setStyleSheet(get_button_style('close'))
        x_btn.setCursor(Qt.PointingHandCursor)
        x_btn.clicked.connect(self.close)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 8)
        for item in (None, self.title_label, None):
            row.addStretch(1) if item is None else row.addWidget(item)
        row.addWidget(x_btn, alignment=Qt.AlignRight)
        return row

    def _centre_on_screen(self):
        area = QApplication.desktop().availableGeometry()
        self.move(area.center() - QPoint(self.width() // 2, self.height() // 2))

    def paintEvent(self, event):
        """Soft drop shadow, then the panel (vertical gradient) and its neon outline."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        def rounded(dx1, dy1, dx2, dy2):
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()).adjusted(dx1, dy1, dx2, dy2), CORNER, CORNER)
            return path

        p.fillPath(rounded(4, 4, -2, -2), QColor(0, 0, 0, 80))

        panel = rounded(2, 2, -2, -2)
        fill = QLinearGradient(0, 0, 0, self.height())
        fill.setColorAt(0, QColor(COLORS['terminal_bg_lighter']))
        fill.setColorAt(1, QColor(COLORS['terminal_bg']))
        p.fillPath(panel, fill)

        p.setPen(QColor(COLORS['border']))
        p.drawPath(panel)
