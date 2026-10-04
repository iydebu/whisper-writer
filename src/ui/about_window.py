"""
About window: app identity, what it does, the device it runs on, and the developer credit.
Uses the same frameless dark window and theme colours as the rest of the app.
"""
import os
import subprocess

from PyQt5.QtCore import Qt, QUrl, QRectF
from PyQt5.QtGui import QFont, QDesktopServices, QPainter, QColor, QPen
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QGridLayout

from ui.base_window import NeonWindow
from ui.styles import COLORS, FONTS, get_button_style

DEVELOPER = 'iydebu'
DEVELOPER_NAME = 'Devashish Tiwari'
WEBSITE = 'https://iydebu.com'
GITHUB = 'https://github.com/iydebu'
FEATURES = [
    ('\u2328', 'Hotkey dictation'),
    ('\u25C9', 'Wake word "whisper"'),
    ('\u0905', 'Hindi \u2192 Hinglish'),
    ('\u26A1', 'Runs offline'),
]


def detect_device():
    """Return (label, detail) for what transcription runs on. Never raises."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            name = 'NVIDIA GPU'
            try:
                out = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=3,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                name = out.stdout.strip().splitlines()[0] or name
            except Exception:
                pass
            return 'GPU', name
    except Exception:
        pass
    return 'CPU', 'Processor (no usable NVIDIA GPU)'


class _Card(QWidget):
    """Rounded panel with a thin accent border (stylesheets do not paint borders on plain QWidget)."""

    def __init__(self, accent=False, parent=None):
        super().__init__(parent)
        self.accent = accent

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(COLORS['neon_green'] if self.accent else COLORS['border'])
        if self.accent:
            color.setAlpha(140)
        p.setPen(QPen(color, 1))
        p.setBrush(QColor(COLORS['terminal_surface']))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)


class _Emblem(QWidget):
    """Glowing ring with a sound-wave inside, drawn in the theme accent (logo.ico is only 32 px)."""

    BARS = (0.30, 0.55, 0.85, 1.0, 0.70, 0.45, 0.80, 0.55, 0.30)

    def __init__(self, size=96, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self.width()
        accent = QColor(COLORS['neon_green'])
        for i, alpha in enumerate((25, 45, 70)):          # soft outer glow
            glow = QColor(accent)
            glow.setAlpha(alpha)
            p.setPen(QPen(glow, 6 - i * 2))
            p.setBrush(Qt.NoBrush)
            m = 4 + i * 2
            p.drawEllipse(m, m, s - 2 * m, s - 2 * m)
        p.setPen(QPen(accent, 2))
        p.setBrush(QColor(COLORS['terminal_surface']))
        p.drawEllipse(10, 10, s - 20, s - 20)
        n = len(self.BARS)
        bar_w, gap = 4, 3
        total = n * bar_w + (n - 1) * gap
        x = (s - total) / 2
        max_h = s * 0.42
        p.setPen(Qt.NoPen)
        p.setBrush(accent)
        for h in self.BARS:
            bh = max_h * h
            p.drawRoundedRect(QRectF(x, (s - bh) / 2, bar_w, bh), 2, 2)
            x += bar_w + gap


def _label(text, size, color, bold=False, align=Qt.AlignCenter, spacing=0):
    lbl = QLabel(text)
    font = QFont(FONTS['family'], size, QFont.Bold if bold else QFont.Normal)
    if spacing:
        font.setLetterSpacing(QFont.AbsoluteSpacing, spacing)
    lbl.setFont(font)
    lbl.setStyleSheet(f'color: {color}; background: transparent;')
    lbl.setAlignment(align)
    lbl.setWordWrap(True)
    return lbl


class AboutWindow(NeonWindow):
    def __init__(self, project_root, version):
        self.project_root = project_root
        self.version = version
        super().__init__('About WhisperWriter', 460, 660)
        self.build()

    def build(self):
        c = COLORS
        lay = self.body
        lay.setSpacing(10)

        # The shared header says WHISPERWRITER -- on this page it is the page title instead.
        self.title_label.setText('ABOUT')

        # Emblem + name + version pill
        emblem_row = QHBoxLayout()
        emblem_row.addStretch(1)
        emblem_row.addWidget(_Emblem(96))
        emblem_row.addStretch(1)
        lay.addLayout(emblem_row)

        lay.addWidget(_label('WhisperWriter', FONTS['size_huge'], c['text_bright'], bold=True))

        pill_row = QHBoxLayout()
        pill = _label(f'v{self.version}', FONTS['size_small'], c['neon_green'], bold=True)
        pill.setStyleSheet(f"color: {c['neon_green']}; background: {c['terminal_surface']};"
                           f"border: 1px solid {c['neon_green']}; border-radius: 9px; padding: 2px 10px;")
        pill_row.addStretch(1)
        pill_row.addWidget(pill)
        pill_row.addStretch(1)
        lay.addLayout(pill_row)

        lay.addWidget(_label('Speak, and it types for you.\nPrivate speech-to-text on your own PC.',
                             FONTS['size_normal'], c['text_secondary']))

        # Feature chips, 2 x 2
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (icon, text) in enumerate(FEATURES):
            chip = _label(f'{icon}  {text}', FONTS['size_small'], c['text_primary'])
            chip.setStyleSheet(f"color: {c['text_primary']}; background: {c['terminal_bg_lighter']};"
                               f"border: 1px solid {c['border']}; border-radius: 6px; padding: 6px;")
            grid.addWidget(chip, i // 2, i % 2)
        lay.addLayout(grid)

        # Device card
        kind, detail = detect_device()
        dev = _Card()
        dl = QHBoxLayout(dev)
        dl.setContentsMargins(14, 10, 14, 10)
        badge_color = c['neon_green'] if kind == 'GPU' else c['neon_yellow']
        badge = _label(kind, FONTS['size_small'], badge_color, bold=True)
        badge.setFixedWidth(46)
        badge.setStyleSheet(f'color: {badge_color}; background: transparent;'
                            f'border: 1px solid {badge_color}; border-radius: 5px; padding: 3px;')
        dl.addWidget(badge)
        dtext = QVBoxLayout()
        dtext.setSpacing(1)
        dtext.addWidget(_label('Running on', FONTS['size_small'], c['text_muted'], align=Qt.AlignLeft))
        dtext.addWidget(_label(detail, FONTS['size_normal'], c['text_primary'], align=Qt.AlignLeft))
        dl.addLayout(dtext, 1)
        lay.addWidget(dev)

        # Developer card
        credit = _Card(accent=True)
        cl = QVBoxLayout(credit)
        cl.setContentsMargins(16, 12, 16, 14)
        cl.setSpacing(4)
        cl.addWidget(_label('DEVELOPED BY', FONTS['size_small'], c['text_muted'], spacing=2))
        cl.addWidget(_label(DEVELOPER, FONTS['size_title'] + 2, c['neon_green'], bold=True))
        cl.addWidget(_label(DEVELOPER_NAME, FONTS['size_normal'], c['text_secondary']))
        links = QHBoxLayout()
        links.setSpacing(8)
        links.setContentsMargins(0, 8, 0, 0)
        for text, url, kind_ in (('iydebu.com', WEBSITE, 'primary'), ('GitHub', GITHUB, 'default')):
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(get_button_style(kind_) + 'QPushButton { padding: 6px 12px; }')
            b.setMinimumHeight(38)
            b.setToolTip(url)
            b.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(b)
        cl.addLayout(links)
        lay.addWidget(credit)

        lay.addStretch(1)
        lay.addWidget(_label(f'\u00A9 2026 {DEVELOPER} ({DEVELOPER_NAME})', FONTS['size_small'], c['text_muted']))
