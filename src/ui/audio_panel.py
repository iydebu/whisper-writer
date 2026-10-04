"""
AudioPanelWidget - Custom widget for audio settings with live level monitoring.
Includes: microphone dropdown, input level meter, sensitivity slider.
"""
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QProgressBar, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from ui.styles import (
    COLORS, FONTS, SPACING, LABEL_COLUMN_WIDTH, VALUE_COLUMN_WIDTH,
    get_device_combobox_style, get_slider_style, get_level_meter_style,
    get_audio_panel_style
)


class AudioPanelWidget(QFrame):
    """
    Custom widget for audio settings with:
    - Microphone device selection dropdown
    - Real-time input level meter
    - Voice detection sensitivity slider
    """
    deviceChanged = pyqtSignal(object)      # Emits device index (int or None)
    thresholdChanged = pyqtSignal(float)    # Emits 0.0-1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AudioPanel")
        self.setStyleSheet(get_audio_panel_style())

        # Audio monitoring state
        self._stream = None
        self._current_level = 0.0
        self._is_monitoring = False

        self._init_ui()
        self._connect_signals()

        # Start level monitoring timer
        self._level_timer = QTimer(self)
        self._level_timer.timeout.connect(self._update_level_meter)
        self._level_timer.start(50)  # Update every 50ms

    def _row_label(self, text):
        """Label in the shared left gutter, so every row's control lines up."""
        label = QLabel(text)
        label.setFixedWidth(LABEL_COLUMN_WIDTH)
        return label

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['lg'])
        layout.setContentsMargins(
            SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg']
        )

        # Section title
        title_label = QLabel("AUDIO SETTINGS")
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        # Microphone selection row
        mic_layout = QHBoxLayout()
        mic_layout.setSpacing(SPACING['md'])

        mic_label = self._row_label("Microphone:")
        self._device_combo = QComboBox()
        self._device_combo.setStyleSheet(get_device_combobox_style())
        # AdjustToContents lets a long device name push the combo wider than the
        # panel; elide inside a fixed cell instead.
        self._device_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
        self._device_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mic_layout.addWidget(mic_label)
        mic_layout.addWidget(self._device_combo, 1)
        layout.addLayout(mic_layout)

        # Populate devices
        self._populate_devices()

        # Input level meter row
        level_layout = QHBoxLayout()
        level_layout.setSpacing(SPACING['md'])

        level_label = self._row_label("Input Level:")
        self._level_meter = QProgressBar()
        self._level_meter.setStyleSheet(get_level_meter_style())
        self._level_meter.setRange(0, 100)
        self._level_meter.setValue(0)
        self._level_meter.setTextVisible(False)
        self._level_meter.setFixedHeight(16)

        self._db_label = QLabel("-∞ dB")
        self._db_label.setObjectName("ValueLabel")
        self._db_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        level_layout.addWidget(level_label)
        level_layout.addWidget(self._level_meter, 1)
        level_layout.addWidget(self._db_label)
        layout.addLayout(level_layout)

        # Sensitivity slider row
        sens_layout = QHBoxLayout()
        sens_layout.setSpacing(SPACING['md'])

        sens_label = self._row_label("Sensitivity:")

        self._threshold_slider = QSlider(Qt.Horizontal)
        self._threshold_slider.setStyleSheet(get_slider_style())
        self._threshold_slider.setRange(0, 100)
        self._threshold_slider.setValue(50)
        self._threshold_slider.setTickPosition(QSlider.NoTicks)

        self._threshold_value_label = QLabel("0.50")
        self._threshold_value_label.setObjectName("ValueLabel")
        self._threshold_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self._threshold_slider, 1)
        sens_layout.addWidget(self._threshold_value_label)
        layout.addLayout(sens_layout)

        # Slider hint labels. Mirrors the sensitivity row's own columns (empty
        # gutter, stretch, value cell) so Low/High track the slider instead of
        # being nudged into place with hand-tuned margins.
        hint_layout = QHBoxLayout()
        hint_layout.setContentsMargins(0, 0, 0, 0)
        hint_layout.setSpacing(SPACING['md'])

        low_label = QLabel("Low")
        low_label.setObjectName("SubLabel")
        high_label = QLabel("High")
        high_label.setObjectName("SubLabel")
        high_label.setAlignment(Qt.AlignRight)

        hint_layout.addWidget(self._row_label(""))
        hint_layout.addWidget(low_label)
        hint_layout.addStretch()
        hint_layout.addWidget(high_label)
        hint_layout.addSpacing(VALUE_COLUMN_WIDTH)
        layout.addLayout(hint_layout)

    def _connect_signals(self):
        """Connect widget signals."""
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)
        self._threshold_slider.valueChanged.connect(self._on_threshold_changed)

    def _populate_devices(self):
        """Populate the device dropdown with available input devices."""
        self._device_combo.clear()
        self._device_combo.addItem("Default Microphone", None)

        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                # Only show input devices (max_input_channels > 0)
                if device.get('max_input_channels', 0) > 0:
                    name = device.get('name', f'Device {idx}')
                    host_api = sd.query_hostapis(device.get('hostapi', 0)).get('name', '')
                    display_name = f"{name} ({host_api})" if host_api else name
                    self._device_combo.addItem(display_name, idx)
        except Exception as e:
            print(f"Error querying audio devices: {e}")

    def _on_device_changed(self, index):
        """Handle device selection change."""
        device_idx = self._device_combo.currentData()
        self.deviceChanged.emit(device_idx)
        # Restart level monitoring with new device
        self._restart_monitoring()

    def _on_threshold_changed(self, value):
        """Handle threshold slider change."""
        threshold = value / 100.0
        self._threshold_value_label.setText(f"{threshold:.2f}")
        self.thresholdChanged.emit(threshold)

    def _restart_monitoring(self):
        """Restart the audio level monitoring with current device."""
        self.stopLevelMonitor()
        self.startLevelMonitor()

    def startLevelMonitor(self):
        """Start audio stream for level monitoring."""
        if self._is_monitoring:
            return

        try:
            device_idx = self._device_combo.currentData()
            self._stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=16000,
                blocksize=1024,
                dtype='float32',
                callback=self._audio_callback
            )
            self._stream.start()
            self._is_monitoring = True
        except Exception as e:
            print(f"Error starting audio monitoring: {e}")

    def stopLevelMonitor(self):
        """Stop audio stream."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._is_monitoring = False
        self._current_level = 0.0

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream - calculates RMS level."""
        if status:
            print(f"Audio status: {status}")
        # Calculate RMS (root mean square) for level
        rms = np.sqrt(np.mean(indata ** 2))
        self._current_level = rms

    def _update_level_meter(self):
        """Update the level meter display."""
        if not self._is_monitoring:
            return

        rms = self._current_level

        # Convert to dB scale (with floor at -60dB)
        if rms > 0:
            db = 20 * np.log10(rms + 1e-10)
            db = max(-60, min(0, db))  # Clamp between -60 and 0 dB
        else:
            db = -60

        # Map dB to percentage (0-100)
        # -60dB = 0%, 0dB = 100%
        percent = int(((db + 60) / 60) * 100)
        percent = max(0, min(100, percent))

        self._level_meter.setValue(percent)

        # Update dB label
        if db <= -60:
            self._db_label.setText("-∞ dB")
        else:
            self._db_label.setText(f"{db:.0f} dB")

    def getSelectedDevice(self):
        """Return the selected device index or None for default."""
        return self._device_combo.currentData()

    def setSelectedDevice(self, device):
        """Set the dropdown selection by device index."""
        if device is None:
            self._device_combo.setCurrentIndex(0)
        else:
            # Find index by device data
            for i in range(self._device_combo.count()):
                if self._device_combo.itemData(i) == device:
                    self._device_combo.setCurrentIndex(i)
                    return
            # If not found, default to first item
            self._device_combo.setCurrentIndex(0)

    def getThreshold(self):
        """Return the threshold value (0.0-1.0)."""
        return self._threshold_slider.value() / 100.0

    def setThreshold(self, value):
        """Set the slider position (accepts 0.0-1.0)."""
        int_value = int(value * 100)
        int_value = max(0, min(100, int_value))
        self._threshold_slider.setValue(int_value)
        self._threshold_value_label.setText(f"{value:.2f}")

    def showEvent(self, event):
        """Start monitoring when widget becomes visible."""
        super().showEvent(event)
        self.startLevelMonitor()

    def hideEvent(self, event):
        """Stop monitoring when widget is hidden."""
        super().hideEvent(event)
        self.stopLevelMonitor()

    def closeEvent(self, event):
        """Clean up on close."""
        self.stopLevelMonitor()
        super().closeEvent(event)
