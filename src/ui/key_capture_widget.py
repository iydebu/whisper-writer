"""
KeyCaptureWidget - Interactive keyboard shortcut capture widget.
Allows users to record key combinations for hotkeys.
"""

import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.styles import (
    FONTS, COLORS, get_button_style,
    get_key_display_style, get_key_display_recording_style
)


class KeyCaptureWidget(QWidget):
    """
    Widget for capturing keyboard shortcuts interactively.

    Features:
    - "Record" button to start listening
    - Visual display of captured keys
    - "Clear" button to reset
    - Validation of key combinations
    - Timeout after 5 seconds of no input
    """

    keysCaptured = pyqtSignal(str)  # Emits "ctrl+shift+space" format

    # Modifier key mappings
    MODIFIER_MAP = {
        Qt.Key_Control: 'ctrl',
        Qt.Key_Shift: 'shift',
        Qt.Key_Alt: 'alt',
        Qt.Key_Meta: 'win',  # Windows/Super key
    }

    # Special key mappings
    SPECIAL_KEY_MAP = {
        Qt.Key_Space: 'space',
        Qt.Key_Return: 'enter',
        Qt.Key_Enter: 'enter',
        Qt.Key_Tab: 'tab',
        Qt.Key_Backspace: 'backspace',
        Qt.Key_Delete: 'delete',
        Qt.Key_Escape: 'escape',
        Qt.Key_Insert: 'insert',
        Qt.Key_Home: 'home',
        Qt.Key_End: 'end',
        Qt.Key_PageUp: 'pageup',
        Qt.Key_PageDown: 'pagedown',
        Qt.Key_Up: 'up',
        Qt.Key_Down: 'down',
        Qt.Key_Left: 'left',
        Qt.Key_Right: 'right',
        Qt.Key_F1: 'f1',
        Qt.Key_F2: 'f2',
        Qt.Key_F3: 'f3',
        Qt.Key_F4: 'f4',
        Qt.Key_F5: 'f5',
        Qt.Key_F6: 'f6',
        Qt.Key_F7: 'f7',
        Qt.Key_F8: 'f8',
        Qt.Key_F9: 'f9',
        Qt.Key_F10: 'f10',
        Qt.Key_F11: 'f11',
        Qt.Key_F12: 'f12',
        Qt.Key_CapsLock: 'capslock',
        Qt.Key_NumLock: 'numlock',
        Qt.Key_ScrollLock: 'scrolllock',
        Qt.Key_Pause: 'pause',
        Qt.Key_Print: 'print',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.captured_modifiers = set()
        self.captured_key = None
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.stopRecording)

        self.initUI()

    def initUI(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Key display label
        self.key_display = QLabel('No hotkey set')
        self.key_display.setStyleSheet(get_key_display_style())
        self.key_display.setAlignment(Qt.AlignCenter)
        self.key_display.setMinimumWidth(160)

        # Record button
        self.record_btn = QPushButton('Record')
        self.record_btn.setStyleSheet(get_button_style('record'))
        self.record_btn.setCheckable(True)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setFixedWidth(90)
        self.record_btn.clicked.connect(self.toggleRecording)

        # Clear button
        self.clear_btn = QPushButton('Clear')
        self.clear_btn.setStyleSheet(get_button_style('success'))
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedWidth(100)
        self.clear_btn.clicked.connect(self.clearHotkey)

        layout.addWidget(self.key_display)
        layout.addWidget(self.record_btn)
        layout.addWidget(self.clear_btn)

    def setHotkey(self, hotkey_str):
        """Set the current hotkey from a string like 'ctrl+shift+space'."""
        if hotkey_str:
            self.key_display.setText(hotkey_str)
        else:
            self.key_display.setText('No hotkey set')

    def getHotkey(self):
        """Get the current hotkey string."""
        text = self.key_display.text()
        if text == 'No hotkey set' or text == 'Press keys...':
            return ''
        return text

    def toggleRecording(self):
        """Toggle recording state."""
        if self.is_recording:
            self.stopRecording()
        else:
            self.startRecording()

    def startRecording(self):
        """Start listening for key combinations."""
        self.is_recording = True
        self.captured_modifiers = set()
        self.captured_key = None
        self.record_btn.setChecked(True)
        self.record_btn.setText('Stop')
        self.key_display.setText('Press keys...')
        self.key_display.setStyleSheet(get_key_display_recording_style())

        # Set focus to capture key events
        self.setFocus()

        # Start timeout timer (5 seconds)
        self.timeout_timer.start(5000)

    def stopRecording(self):
        """Stop listening and finalize the captured keys."""
        self.is_recording = False
        self.timeout_timer.stop()
        self.record_btn.setChecked(False)
        self.record_btn.setText('Record')
        self.key_display.setStyleSheet(get_key_display_style())

        # Build the hotkey string
        hotkey = self.buildHotkeyString()
        if hotkey:
            self.key_display.setText(hotkey)
            self.keysCaptured.emit(hotkey)
        elif self.key_display.text() == 'Press keys...':
            self.key_display.setText('No hotkey set')

    def buildHotkeyString(self):
        """Build the hotkey string from captured modifiers and key."""
        if not self.captured_key:
            return ''

        parts = []
        # Add modifiers in standard order
        if 'ctrl' in self.captured_modifiers:
            parts.append('ctrl')
        if 'alt' in self.captured_modifiers:
            parts.append('alt')
        if 'shift' in self.captured_modifiers:
            parts.append('shift')
        if 'win' in self.captured_modifiers:
            parts.append('win')

        parts.append(self.captured_key)
        return '+'.join(parts)

    def clearHotkey(self):
        """Clear the current hotkey."""
        if self.is_recording:
            self.stopRecording()
        self.captured_modifiers = set()
        self.captured_key = None
        self.key_display.setText('No hotkey set')
        self.keysCaptured.emit('')

    def keyPressEvent(self, event):
        """Handle key press events when recording."""
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Handle modifier keys
        if key in self.MODIFIER_MAP:
            self.captured_modifiers.add(self.MODIFIER_MAP[key])
            self.updateDisplayDuringRecording()
            return

        # Handle special keys
        if key in self.SPECIAL_KEY_MAP:
            self.captured_key = self.SPECIAL_KEY_MAP[key]
            self.updateDisplayDuringRecording()
            self.stopRecording()
            return

        # Handle regular alphanumeric keys
        if key >= Qt.Key_A and key <= Qt.Key_Z:
            self.captured_key = chr(key).lower()
            self.updateDisplayDuringRecording()
            self.stopRecording()
            return

        if key >= Qt.Key_0 and key <= Qt.Key_9:
            self.captured_key = chr(key)
            self.updateDisplayDuringRecording()
            self.stopRecording()
            return

        # Ignore unknown keys
        event.accept()

    def keyReleaseEvent(self, event):
        """Handle key release events."""
        if not self.is_recording:
            super().keyReleaseEvent(event)
            return

        # If a modifier is released and we have a key, finalize
        key = event.key()
        if key in self.MODIFIER_MAP and self.captured_key:
            self.stopRecording()

        event.accept()

    def updateDisplayDuringRecording(self):
        """Update the display while recording keys."""
        parts = []
        if 'ctrl' in self.captured_modifiers:
            parts.append('ctrl')
        if 'alt' in self.captured_modifiers:
            parts.append('alt')
        if 'shift' in self.captured_modifiers:
            parts.append('shift')
        if 'win' in self.captured_modifiers:
            parts.append('win')

        if self.captured_key:
            parts.append(self.captured_key)

        if parts:
            self.key_display.setText('+'.join(parts))
        else:
            self.key_display.setText('Press keys...')

    def focusOutEvent(self, event):
        """Handle focus loss - stop recording."""
        if self.is_recording:
            self.stopRecording()
        super().focusOutEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Test widget
    widget = QWidget()
    layout = QHBoxLayout(widget)

    capture = KeyCaptureWidget()
    capture.setHotkey('ctrl+shift+space')
    capture.keysCaptured.connect(lambda k: print(f'Captured: {k}'))

    layout.addWidget(QLabel('Activation Key:'))
    layout.addWidget(capture)

    widget.setWindowTitle('KeyCaptureWidget Test')
    widget.show()

    sys.exit(app.exec_())
