import sys
import os
import platform
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout, QWidget

# Windows-specific imports for forcing always-on-top
if platform.system() == 'Windows':
    import ctypes
    from ctypes import wintypes

    # Windows API constants
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.styles import COLORS, FONTS
from ui.base_window import DragToMove


class PulsingDot(QWidget):
    """Animated pulsing dot indicator for recording status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._opacity = 1.0
        self._color = QColor(COLORS['recording'])

        # Animation for pulsing effect
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.3)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.setLoopCount(-1)  # Infinite loop

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    def setColor(self, color):
        self._color = QColor(color)
        self.update()

    def startPulsing(self):
        self.animation.setDirection(QPropertyAnimation.Forward)
        self.animation.start()

    def stopPulsing(self):
        self.animation.stop()
        self._opacity = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(self._color)
        color.setAlphaF(self._opacity)

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 8, 8)


class StatusWindow(DragToMove, QWidget):
    """Compact pill-shaped status indicator."""
    statusSignal = pyqtSignal(str)
    closeSignal = pyqtSignal()

    MARGIN = 80

    POSITIONS = {
        'top_left': lambda sw, sh, w, h, m: (m, m),
        'top_center': lambda sw, sh, w, h, m: ((sw - w) // 2, m),
        'top_right': lambda sw, sh, w, h, m: (sw - w - m, m),
        'bottom_left': lambda sw, sh, w, h, m: (m, sh - h - m),
        'bottom_center': lambda sw, sh, w, h, m: ((sw - w) // 2, sh - h - m),
        'bottom_right': lambda sw, sh, w, h, m: (sw - w - m, sh - h - m),
    }

    def __init__(self, config=None):
        """
        Initialize the compact status window.
        """
        super().__init__()
        self.current_status = 'idle'
        self.position = (config or {}).get('misc', {}).get('status_window_position') or 'bottom_center'
        self._build_pill()
        self.statusSignal.connect(self.updateStatus)

    def _build_pill(self):
        # Use multiple flags to ensure always-on-top behavior
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(140, 36)

        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Pulsing dot indicator
        self.pulsing_dot = PulsingDot()
        layout.addWidget(self.pulsing_dot)

        # Status label
        self.status_label = QLabel('Recording...')
        self.status_label.setFont(QFont(FONTS['family'], FONTS['size_normal'], QFont.Bold))
        self.status_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.status_label)

    def paintEvent(self, event):
        """
        Draw the compact pill-shaped background.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw pill-shaped background
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, 18, 18)

        # Background fill
        painter.setBrush(QBrush(QColor(COLORS['terminal_bg'])))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Border
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor(COLORS['border']))
        painter.drawPath(path)

    def show(self):
        """
        Position the window per the configured screen corner/edge and show it.
        Forces always-on-top on Windows using native API.
        """
        screen_geometry = QApplication.primaryScreen().geometry()
        place = self.POSITIONS.get(self.position, self.POSITIONS['bottom_center'])
        x, y = place(
            screen_geometry.width(),
            screen_geometry.height(),
            self.width(),
            self.height(),
            self.MARGIN,
        )

        self.move(screen_geometry.x() + x, screen_geometry.y() + y)
        super().show()

        # Force always-on-top on Windows using native API
        self._force_topmost()

    def _force_topmost(self):
        """Use Windows API to force window to stay on top of all windows."""
        if platform.system() == 'Windows':
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                )
            except Exception:
                pass  # Fallback to Qt's WindowStaysOnTopHint

    def closeEvent(self, event):
        # Whoever owns the recording is told the pill went away, so it can stop too.
        self.pulsing_dot.stopPulsing()
        self.closeSignal.emit()
        event.accept()

    # status -> (label, dot colour key, pulse?)
    LOOKS = {
        'recording': ('Listening...', 'recording', True),
        'transcribing': ('Transcribing...', 'primary', True),
        'done': ('Done!', 'success', False),
    }

    @pyqtSlot(str)
    def updateStatus(self, status):
        """Recorder states: recording -> transcribing -> done; idle/error/cancel hide the pill."""
        self.current_status = status
        look = self.LOOKS.get(status)
        if look is None:
            if status in ('idle', 'error', 'cancel'):
                self.pulsing_dot.stopPulsing()
                self.close()
            return

        text, colour, pulse = look
        self.status_label.setText(text)
        self.pulsing_dot.setColor(COLORS[colour])
        self.pulsing_dot.startPulsing() if pulse else self.pulsing_dot.stopPulsing()
        if status == 'recording':
            self.show()
        else:
            self._force_topmost()   # other apps may have stacked above us since it appeared
        if status == 'done':
            QTimer.singleShot(800, self.close)


if __name__ == '__main__':
    # Quick visual check: python src/ui/status_window.py
    demo = QApplication(sys.argv)
    pill = StatusWindow()
    for delay, state in ((0, 'recording'), (2500, 'transcribing'), (5000, 'done'), (6500, 'idle')):
        QTimer.singleShot(delay, lambda st=state: pill.updateStatus(st))
    QTimer.singleShot(7000, demo.quit)
    sys.exit(demo.exec_())
