"""
Home panel shown from the tray ("Show Main Menu"): a Start button, a Settings button
and a reminder of the current hotkey. Closing it only hides it -- the app keeps running in the tray.
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel

from ui.base_window import NeonWindow
from ui.styles import FONTS, get_button_style, get_label_style
from utils import load_config_schema, load_config_values

DEFAULT_HOTKEY = 'ctrl+shift+space'


def current_hotkey():
    try:
        return load_config_values(load_config_schema())['recording_options'].get('activation_key') or DEFAULT_HOTKEY
    except Exception:
        return DEFAULT_HOTKEY


class HomeWindow(NeonWindow):
    settingsRequested = pyqtSignal()
    listenRequested = pyqtSignal()

    BUTTON_SIZE = (130, 55)

    def __init__(self):
        super().__init__('WhisperWriter', 340, 200)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch(1)
        row.addWidget(self._button('Start', 'primary', bold=True, on_click=self._on_start))
        row.addWidget(self._button('Settings', 'default', bold=False, on_click=self.settingsRequested.emit))
        row.addStretch(1)

        hint = QLabel(f'Hotkey: {current_hotkey()}')
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(get_label_style('hotkey'))

        for part in (1, row, 1, hint):
            if part == 1:
                self.body.addStretch(1)
            elif isinstance(part, QLabel):
                self.body.addWidget(part, alignment=Qt.AlignCenter)
            else:
                self.body.addLayout(part)

    def _button(self, text, style, bold, on_click):
        b = QPushButton(text)
        b.setFont(QFont(FONTS['family'], FONTS['size_normal'], QFont.Bold if bold else QFont.Normal))
        b.setFixedSize(*self.BUTTON_SIZE)
        b.setStyleSheet(get_button_style(style))
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(on_click)
        return b

    def _on_start(self):
        self.listenRequested.emit()
        self.hide()

    def closeEvent(self, event):
        # Tray app: the x button tucks the panel away instead of quitting.
        event.ignore()
        self.hide()
