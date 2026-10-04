import copy, os, sys

from dotenv import load_dotenv, set_key
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QMessageBox, QTabWidget, QWidget, QSizePolicy, QSpacerItem, QToolButton, QStyle, QScrollArea
)
from PyQt5.QtCore import Qt, QCoreApplication, QProcess, pyqtSignal
from PyQt5.QtGui import QFont

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import NeonWindow
from ui.key_capture_widget import KeyCaptureWidget
from ui.styles import (
    FONTS, COLORS, SPACING, LABEL_COLUMN_WIDTH, TAB_RAIL_WIDTH,
    get_button_style, get_input_style, get_combobox_style,
    get_checkbox_style, get_label_style, get_vertical_tab_style, get_global_stylesheet
)
from ui.audio_panel import AudioPanelWidget
from utils import load_config_schema, load_config_values, save_config

load_dotenv()


class SettingsWindow(NeonWindow):
    settingsClosed = pyqtSignal()

    # Clean text tab labels
    TAB_LABELS = {
        'model_options': 'Model',
        'recording_options': 'Recording',
        'post_processing': 'Output',
        'misc': 'General',
    }

    # Section headers for better organization
    SECTION_HEADERS = {
        'model_options': {
            'language_mode': 'Language & Model',
            'device': 'Performance Settings',
            'condition_on_previous_text': 'Advanced Options',
        },
        'recording_options': {
            'activation_key': 'Activation',
            'recording_mode': 'Recording Behavior',
            'wake_word_phrase': 'Wake Word',
        },
        'post_processing': {
            'writing_key_press_delay': 'Output Settings',
        },
        'misc': {
            'print_to_terminal': 'Debug Options',
            'status_window_position': 'Appearance',
        },
    }

    def __init__(self, schema):
        """
        Initialize the settings window.
        """
        self.schema = schema
        self.config = load_config_values(schema)
        self.initial_config = copy.deepcopy(self.config)
        self.default_config = load_config_values(schema, config_path=None)
        self.key_capture_widget = None
        self.audio_panel_widget = None
        self.current_sections = {}
        # Wider than the old icon-only rail: the tab labels now take real width.
        super().__init__('Settings', 900, 720)
        self.initSettingsUI()
        self.initial_config = self.get_current_config()

    def initSettingsUI(self):
        """
        Initialize the settings user interface with vertical icon tabs.
        """
        # Apply global dark theme
        self.setStyleSheet(get_global_stylesheet())

        # Create tab widget across top (North position)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setStyleSheet(get_vertical_tab_style())
        self.body.addWidget(self.tabs)

        for category, settings in self.schema.items():
            # Create scrollable tab content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background-color: {COLORS['terminal_bg']};
                }}
                QWidget {{
                    background-color: {COLORS['terminal_bg']};
                }}
            """)

            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.setSpacing(SPACING['md'])
            tab_layout.setContentsMargins(
                SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg']
            )
            tab.setLayout(tab_layout)

            self.current_sections[category] = set()

            # Add settings for this category
            for key, meta in settings.items():
                if isinstance(meta, dict) and 'value' in meta:
                    # Skip audio settings that will be in the AudioPanel
                    if category == 'recording_options' and key in ('sound_device', 'voice_threshold'):
                        continue
                    self.add_section_header_if_needed(tab_layout, category, key)
                    self.add_setting_widget(tab_layout, key, meta, category)

            # Add AudioPanelWidget for recording_options tab
            if category == 'recording_options':
                tab_layout.addSpacing(SPACING['lg'])
                self.audio_panel_widget = AudioPanelWidget()
                self.audio_panel_widget.deviceChanged.connect(
                    lambda d: self.onAudioDeviceChanged(d, 'recording_options', 'sound_device')
                )
                self.audio_panel_widget.thresholdChanged.connect(
                    lambda t: self.onThresholdChanged(t, 'recording_options', 'voice_threshold')
                )
                # Set initial values
                sound_device = self.config.get('recording_options', {}).get('sound_device')
                voice_threshold = self.config.get('recording_options', {}).get('voice_threshold', 0.5)
                self.audio_panel_widget.setSelectedDevice(sound_device)
                self.audio_panel_widget.setThreshold(voice_threshold)
                tab_layout.addWidget(self.audio_panel_widget)

            tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

            scroll_area.setWidget(tab)

            label = self.TAB_LABELS.get(category, category.replace('_', ' ').title())
            index = self.tabs.addTab(scroll_area, label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING['md'])

        reset_button = QPushButton('Reset to Default')
        reset_button.setStyleSheet(get_button_style('default'))
        reset_button.setCursor(Qt.PointingHandCursor)
        reset_button.clicked.connect(self.resetSettings)

        save_button = QPushButton('Save Settings')
        save_button.setStyleSheet(get_button_style('success'))
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.saveSettings)

        button_layout.addStretch()
        button_layout.addWidget(reset_button)
        button_layout.addWidget(save_button)

        self.body.addLayout(button_layout)

    def add_section_header_if_needed(self, layout, category, key):
        """Add a section header if this is a new section."""
        section_headers = self.SECTION_HEADERS.get(category, {})
        header_text = section_headers.get(key)

        if header_text and header_text not in self.current_sections[category]:
            self.current_sections[category].add(header_text)

            # Add spacing before header (except for first)
            if len(self.current_sections[category]) > 1:
                layout.addSpacing(SPACING['md'])

            header_label = QLabel(header_text)
            header_label.setStyleSheet(get_label_style('section'))
            layout.addWidget(header_label)

    def add_setting_widget(self, layout, key, meta, category):
        """
        Add a setting widget to the layout.
        """
        item_layout = QHBoxLayout()
        item_layout.setSpacing(SPACING['sm'])

        label = QLabel(f"{key.replace('_', ' ').title()}:")
        label.setStyleSheet(get_label_style('default'))
        # Fixed label gutter: an expanding label steals width from the input and
        # makes each row's control start at a different x.
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        label.setFixedWidth(LABEL_COLUMN_WIDTH)
        label.setWordWrap(True)
        meta_type = meta.get('type')

        # Retrieve the current value from the loaded config
        current_value = self.config.get(category, {}).get(key, meta['value'])

        # Special handling for activation_key - use KeyCaptureWidget
        if key == 'activation_key':
            widget = KeyCaptureWidget()
            widget.setHotkey(current_value or '')
            widget.keysCaptured.connect(lambda k: self.onHotkeyCaptured(k, category, key))
            self.key_capture_widget = widget
        elif meta_type == 'bool':
            widget = QCheckBox()
            widget.setStyleSheet(get_checkbox_style())
            widget.setChecked(current_value)
        elif meta_type == 'str' and 'options' in meta:
            widget = QComboBox()
            widget.setStyleSheet(get_combobox_style())
            widget.addItems(meta['options'])
            widget.setCurrentText(current_value if current_value else meta['options'][0])
        elif meta_type == 'str':
            widget = QLineEdit(current_value or '')
            widget.setStyleSheet(get_input_style())
        elif meta_type == 'int':
            widget = QLineEdit(str(current_value) if current_value is not None else '')
            widget.setStyleSheet(get_input_style())
        elif meta_type == 'float':
            widget = QLineEdit(str(current_value) if current_value is not None else '')
            widget.setStyleSheet(get_input_style())
        else:
            return

        widget.setToolTip(meta.get('description', ''))
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        help_button = QToolButton(autoRaise=True, toolTip=meta.get('description', ''))
        help_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        help_button.setCursor(Qt.PointingHandCursor)
        help_button.setFocusPolicy(Qt.TabFocus)
        help_button.clicked.connect(lambda: self.show_description(meta.get('description', '')))

        item_layout.addWidget(label)
        item_layout.addWidget(widget)
        item_layout.addWidget(help_button)
        layout.addLayout(item_layout)

        # Store widget reference
        setattr(self, f"{category}_{key}_input", widget)

    def onHotkeyCaptured(self, hotkey, category, key):
        """Handle when a new hotkey is captured."""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = hotkey

    def onAudioDeviceChanged(self, device, category, key):
        """Handle when audio device selection changes."""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = device

    def onThresholdChanged(self, threshold, category, key):
        """Handle when voice threshold slider changes."""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = threshold

    def show_description(self, description):
        """
        Show a description dialog.
        """
        QMessageBox.information(self, 'Description', description)

    def saveSettings(self):
        """
        Save the settings to the config.yaml file.
        """
        for category, settings in self.schema.items():
            for key, meta in settings.items():
                if not isinstance(meta, dict) or 'value' not in meta:
                    continue

                widget = getattr(self, f"{category}_{key}_input", None)
                if widget is None:
                    continue

                if category not in self.config:
                    self.config[category] = {}

                self.config[category][key] = self.get_widget_value(widget, meta.get('type'))

        save_config(self.config)
        QMessageBox.information(self, 'Settings Saved', 'Settings have been saved. Restarting application...')
        self.restart_application()

    def restart_application(self):
        """
        Restart the application to apply the new settings.
        """
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, 'release_instance_lock'):
            main_module.release_instance_lock()
        QCoreApplication.quit()
        # Frozen: sys.executable IS the app, and argv[0] is its own path.
        args = sys.argv[1:] if getattr(sys, 'frozen', False) else sys.argv
        QProcess.startDetached(sys.executable, args)

    def resetSettings(self):
        """
        Reset the settings to the default values.
        """
        self.reset_to_initial_settings(self.default_config)

    def reset_to_initial_settings(self, config_source):
        """
        Reset the settings to the initial values when the window was opened.
        """
        for category, settings in self.schema.items():
            for key, meta in settings.items():
                if not isinstance(meta, dict) or 'value' not in meta:
                    continue

                # Handle audio panel settings separately
                if category == 'recording_options' and key in ('sound_device', 'voice_threshold'):
                    if self.audio_panel_widget:
                        initial_value = config_source.get(category, {}).get(key, meta['value'])
                        if key == 'sound_device':
                            self.audio_panel_widget.setSelectedDevice(initial_value)
                            self.config[category][key] = initial_value
                        elif key == 'voice_threshold':
                            self.audio_panel_widget.setThreshold(initial_value if initial_value else 0.5)
                            self.config[category][key] = initial_value
                    continue

                widget = getattr(self, f"{category}_{key}_input", None)
                if widget is None:
                    continue

                initial_value = config_source.get(category, {}).get(key, meta['value'])
                self.set_widget_value(widget, initial_value, meta.get('type'))

    def set_widget_value(self, widget, value, value_type):
        """
        Set the value of the widget.
        """
        if isinstance(widget, KeyCaptureWidget):
            widget.setHotkey(value or '')
        elif isinstance(widget, QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value) if value else '')
        elif isinstance(widget, QLineEdit):
            if value_type == 'int' or value_type == 'float':
                widget.setText(str(value) if value is not None else '')
            else:
                widget.setText(value or '')

    def get_widget_value(self, widget, value_type):
        """
        Get the value of the widget.
        """
        if isinstance(widget, KeyCaptureWidget):
            return widget.getHotkey() or None
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            value = widget.currentText()
            return value if value else None
        elif isinstance(widget, QLineEdit):
            raw = widget.text()
            if not raw:
                return None
            return {'int': int, 'float': float}.get(value_type, str)(raw)

    def showEvent(self, event):
        """
        Refresh initial_config snapshot whenever the window is shown.
        """
        super().showEvent(event)
        self.config = load_config_values(self.schema)
        self.reset_to_initial_settings(self.config)
        self.initial_config = self.get_current_config()

    def get_current_config(self):
        """
        Get current configuration values from UI controls.
        """
        current = {}
        for category, settings in self.schema.items():
            current[category] = {}
            for key, meta in settings.items():
                if not isinstance(meta, dict) or 'value' not in meta:
                    continue

                if category == 'recording_options' and key in ('sound_device', 'voice_threshold'):
                    if self.audio_panel_widget:
                        if key == 'sound_device':
                            current[category][key] = self.audio_panel_widget.getSelectedDevice()
                        elif key == 'voice_threshold':
                            current[category][key] = self.audio_panel_widget.getThreshold()
                    else:
                        current[category][key] = self.config.get(category, {}).get(key, meta.get('value'))
                    continue

                widget = getattr(self, f"{category}_{key}_input", None)
                if widget is None:
                    current[category][key] = self.config.get(category, {}).get(key, meta.get('value'))
                else:
                    current[category][key] = self.get_widget_value(widget, meta.get('type'))
        return current

    def has_changes(self):
        """
        Check if any UI values differ from initial_config when window was opened.
        """
        return self.get_current_config() != self.initial_config

    def closeEvent(self, event):
        """
        Confirm before closing the settings window only if settings were changed.
        """
        if self.has_changes():
            answer = QMessageBox.question(self, 'Unsaved changes',
                                          'You changed some settings. Close and throw those changes away?',
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return

        # Stop audio monitoring before closing
        if self.audio_panel_widget:
            self.audio_panel_widget.stopLevelMonitor()
        self.reset_to_initial_settings(self.initial_config)
        self.settingsClosed.emit()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    schema = load_config_schema()
    settings_window = SettingsWindow(schema)
    settings_window.show()

    sys.exit(app.exec_())
