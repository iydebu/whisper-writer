"""
Centralized stylesheet system for WhisperWriter UI.
Mac Terminal Dark Theme with neon accents.
"""

# Mac Terminal Dark Color Palette - Ultra Dark Edition
_NEON_GREEN = {
    # Primary terminal colors - deeper blacks
    'terminal_bg': '#0D0D0D',  # Main background (near black)
    'terminal_bg_lighter': '#141414',  # Lighter panels
    'terminal_bg_darker': '#080808',  # Darker borders
    'terminal_surface': '#1A1A1A',  # Surface elements

    # Neon accent colors
    'neon_green': '#00FFC8',  # Primary accent
    'neon_green_dim': '#00D9AE',  # Dimmed accent
    'neon_green_glow': 'rgba(0, 255, 200, 0.5)',  # Glow effect
    'neon_blue': '#00D9FF',  # Secondary accent
    'neon_red': '#FF0055',  # Error/recording
    'neon_yellow': '#FFD700',  # Warning

    # Status colors
    'success': '#00FFC8',
    'success_glow': 'rgba(0, 255, 200, 0.3)',
    'warning': '#FFD700',
    'warning_glow': 'rgba(255, 215, 0, 0.3)',
    'error': '#FF0055',
    'error_glow': 'rgba(255, 0, 85, 0.3)',

    # Recording indicator
    'recording': '#FF0055',
    'recording_glow': 'rgba(255, 0, 85, 0.5)',

    # Primary accent (alias for neon_green)
    'primary': '#00FFC8',

    # Text colors
    'text_primary': '#E0E0E0',  # Main text
    'text_secondary': '#A0A0A0',  # Secondary text
    'text_muted': '#6A6A6A',  # Muted text
    'text_bright': '#FFFFFF',  # Bright text
    'text_neon': '#00FFC8',  # Accent text

    # Borders & Lines
    'border': '#3E3E42',
    'border_focus': '#00FFC8',
    'border_active': '#00D9FF',

    # Input backgrounds - darker for ultra dark theme
    'input_bg': '#1A1A1A',
    'input_focus': '#222222',
    'input_hover': '#1E1E1E',

    # Button states - darker
    'button_bg': '#1A1A1A',
    'button_hover': '#222222',
    'button_active': '#00FFC8',
    'button_active_text': '#000000',

    # Shadows & Glows (for programmatic use, not CSS)
    'shadow': 'rgba(0, 0, 0, 0.5)',

    # Legacy color names for compatibility
    'bg_gradient_start': '#252526',
    'bg_gradient_end': '#1E1E1E',
    'bg_window': '#1E1E1E',
    'bg_input': '#2D2D30',
    'bg_hover': '#37373D',
    'bg_section': '#2D2D30',
}

# Neon Blue variant - same ultra dark base, cyan/blue accents
_NEON_BLUE = dict(_NEON_GREEN, **{
    'neon_green': '#00A6FF',
    'neon_green_dim': '#0086D9',
    'neon_green_glow': 'rgba(0, 166, 255, 0.5)',
    'neon_blue': '#00D9FF',
    'success': '#00A6FF',
    'success_glow': 'rgba(0, 166, 255, 0.3)',
    'primary': '#00A6FF',
    'text_neon': '#00A6FF',
    'border_focus': '#00A6FF',
    'border_active': '#00D9FF',
    'button_active': '#00A6FF',
    'button_active_text': '#000000',
})

THEMES = {
    'neon_green': _NEON_GREEN,
    'neon_blue': _NEON_BLUE,
}

# Active palette. Every UI module does `from ui.styles import COLORS`, which binds
# this dict object at import time, so set_theme mutates it in place - rebinding
# the name here would not reach those modules.
COLORS = dict(_NEON_GREEN)


def set_theme(name):
    """Swap the active palette in place. Call before building any widgets."""
    COLORS.clear()
    COLORS.update(THEMES.get(name, _NEON_GREEN))


# Terminal Fonts
FONTS = {
    'family': 'Consolas',
    'family_sans': 'Segoe UI',
    'family_alt': 'Consolas',
    'size_small': 9,
    'size_normal': 10,
    'size_medium': 11,
    'size_large': 13,
    'size_title': 16,
    'size_huge': 20,
    'weight_normal': 400,
    'weight_medium': 500,
    'weight_bold': 700,
}

# Spacing
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
}

# Width of the settings vertical tab rail. Shared so the tab stylesheet and the
# window width stay in sync when tab labels change.
TAB_RAIL_WIDTH = 150

# Width of the leading label column in settings/audio rows, so labels, inputs
# and slider hints all align to the same gutter.
LABEL_COLUMN_WIDTH = 180

# Width of the trailing value column (dB / threshold readouts). Shared with the
# audio panel stylesheet so the slider hint row can derive its alignment.
VALUE_COLUMN_WIDTH = 45


def get_button_style(button_type='default'):
    """Get button stylesheet based on type."""
    styles = {
        'default': f"""
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 10px 20px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}pt;
                font-weight: {FONTS['weight_medium']};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_hover']};
                border-color: {COLORS['neon_green_dim']};
                color: {COLORS['neon_green']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['terminal_bg_darker']};
                border-color: {COLORS['neon_green']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['terminal_bg']};
                color: {COLORS['text_muted']};
                border-color: {COLORS['border']};
            }}
        """,
        'primary': f"""
            QPushButton {{
                background-color: {COLORS['neon_green']};
                color: {COLORS['terminal_bg']};
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_medium']}pt;
                font-weight: {FONTS['weight_bold']};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['neon_green_dim']};
            }}
            QPushButton:pressed {{
                background-color: #00B38F;
            }}
        """,
        'success': f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['neon_green']};
                border: 2px solid {COLORS['neon_green']};
                border-radius: 4px;
                padding: 10px 20px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}pt;
                font-weight: {FONTS['weight_bold']};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['neon_green']};
                color: {COLORS['terminal_bg']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['neon_green_dim']};
            }}
        """,
        'danger': f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['neon_red']};
                border: 2px solid {COLORS['neon_red']};
                border-radius: 4px;
                padding: 10px 20px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}pt;
                font-weight: {FONTS['weight_bold']};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['neon_red']};
                color: {COLORS['text_bright']};
            }}
        """,
        'close': f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 3px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_large']}pt;
                font-weight: {FONTS['weight_bold']};
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['neon_red']};
                color: {COLORS['text_bright']};
            }}
            QPushButton:pressed {{
                background-color: #CC0044;
            }}
        """,
        'record': f"""
            QPushButton {{
                background-color: {COLORS['terminal_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                padding: 6px 12px;
                font-family: {FONTS['family']};
                font-size: {FONTS['size_small']}pt;
                font-weight: {FONTS['weight_medium']};
            }}
            QPushButton:hover {{
                border-color: {COLORS['neon_red']};
                color: {COLORS['neon_red']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['terminal_bg']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['neon_red']};
                color: {COLORS['text_bright']};
                border-color: {COLORS['neon_red']};
            }}
        """,
    }
    return styles.get(button_type, styles['default'])


def get_input_style():
    """Get input field stylesheet."""
    return f"""
        QLineEdit {{
            background-color: {COLORS['input_bg']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px 12px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            selection-background-color: {COLORS['neon_green']};
            selection-color: {COLORS['terminal_bg']};
        }}
        QLineEdit:focus {{
            border-color: {COLORS['neon_green']};
            background-color: {COLORS['input_focus']};
        }}
        QLineEdit:hover {{
            background-color: {COLORS['input_hover']};
        }}
        QLineEdit:disabled {{
            background-color: {COLORS['terminal_bg']};
            color: {COLORS['text_muted']};
            border-color: {COLORS['terminal_bg_darker']};
        }}
    """


def get_combobox_style():
    """Get combobox stylesheet."""
    return f"""
        QComboBox {{
            background-color: {COLORS['input_bg']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px 12px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
        }}
        QComboBox:hover {{
            border-color: {COLORS['neon_green_dim']};
            background-color: {COLORS['input_hover']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['neon_green']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['terminal_surface']};
            color: {COLORS['text_primary']};
            selection-background-color: {COLORS['neon_green']};
            selection-color: {COLORS['terminal_bg']};
            border: 1px solid {COLORS['border']};
            outline: none;
        }}
    """


def get_checkbox_style():
    """Get checkbox stylesheet."""
    return f"""
        QCheckBox {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {COLORS['border']};
            border-radius: 2px;
            background-color: {COLORS['input_bg']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {COLORS['neon_green_dim']};
            background-color: {COLORS['input_hover']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLORS['neon_green']};
            border-color: {COLORS['neon_green']};
            image: none;
        }}
    """


def get_label_style(label_type='default'):
    """Get label stylesheet based on type."""
    styles = {
        'default': f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}pt;
            }}
        """,
        'title': f"""
            QLabel {{
                color: {COLORS['neon_green']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_title']}pt;
                font-weight: {FONTS['weight_bold']};
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """,
        'section': f"""
            QLabel {{
                color: {COLORS['neon_green']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_medium']}pt;
                font-weight: {FONTS['weight_bold']};
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 8px 0px;
                border-bottom: 1px solid {COLORS['neon_green']};
                margin: 8px 0px;
            }}
        """,
        'muted': f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_small']}pt;
            }}
        """,
        'status': f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_large']}pt;
                font-weight: {FONTS['weight_medium']};
            }}
        """,
        'hotkey': f"""
            QLabel {{
                color: {COLORS['neon_green']};
                font-family: {FONTS['family']};
                font-size: {FONTS['size_normal']}pt;
                background-color: {COLORS['terminal_surface']};
                border: 1px solid {COLORS['neon_green']};
                border-radius: 3px;
                padding: 6px 12px;
            }}
        """,
    }
    return styles.get(label_type, styles['default'])


def get_tab_style():
    """Get tab widget stylesheet (horizontal tabs)."""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['terminal_bg_lighter']};
            padding: 12px;
        }}
        QTabBar::tab {{
            background-color: {COLORS['terminal_surface']};
            color: {COLORS['text_secondary']};
            border: 1px solid {COLORS['border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 10px 20px;
            margin-right: 2px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        QTabBar::tab:selected {{
            background-color: {COLORS['terminal_bg_lighter']};
            color: {COLORS['neon_green']};
            font-weight: {FONTS['weight_bold']};
            border-bottom: 2px solid {COLORS['neon_green']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['button_hover']};
            color: {COLORS['text_primary']};
        }}
    """


def get_vertical_tab_style():
    """Get tab widget stylesheet (top horizontal tabs)."""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['terminal_bg']};
            padding: {SPACING['lg']}px;
        }}
        QTabBar {{
            background-color: transparent;
        }}
        QTabBar::tab {{
            background-color: {COLORS['terminal_bg_darker']};
            color: {COLORS['text_muted']};
            border: 1px solid {COLORS['border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 10px 20px;
            margin-right: 4px;
            font-family: {FONTS['family_sans']};
            font-size: {FONTS['size_medium']}pt;
            font-weight: {FONTS['weight_medium']};
            min-width: 140px;
        }}
        QTabBar::tab:selected {{
            background-color: {COLORS['terminal_bg']};
            color: {COLORS['neon_green']};
            border-top: 2px solid {COLORS['neon_green']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['terminal_surface']};
            color: {COLORS['text_primary']};
        }}
    """


def get_tooltip_style():
    """Get tooltip stylesheet."""
    return f"""
        QToolTip {{
            background-color: {COLORS['terminal_surface']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['neon_green']};
            border-radius: 3px;
            padding: 8px 12px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_small']}pt;
        }}
    """


def get_scrollbar_style():
    """Get scrollbar stylesheet."""
    return f"""
        QScrollBar:vertical {{
            background-color: {COLORS['terminal_bg']};
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['neon_green_dim']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {COLORS['terminal_bg']};
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['neon_green_dim']};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """


def get_message_box_style():
    """Get message box stylesheet."""
    return f"""
        QMessageBox {{
            background-color: {COLORS['terminal_bg_lighter']};
        }}
        QMessageBox QLabel {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
        }}
        QMessageBox QPushButton {{
            background-color: {COLORS['button_bg']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 8px 18px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            font-weight: {FONTS['weight_medium']};
        }}
        QMessageBox QPushButton:hover {{
            background-color: {COLORS['button_hover']};
            border-color: {COLORS['neon_green_dim']};
            color: {COLORS['neon_green']};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {COLORS['terminal_bg_darker']};
            border-color: {COLORS['neon_green']};
        }}
        QMessageBox QPushButton:default {{
            background-color: {COLORS['neon_green']};
            color: {COLORS['terminal_bg']};
            border: none;
        }}
    """


def get_key_display_style():
    """Get key display stylesheet for hotkey capture."""
    return f"""
        QLabel {{
            background-color: {COLORS['input_bg']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px 12px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_medium']}pt;
            font-weight: {FONTS['weight_medium']};
            min-width: 150px;
        }}
    """


def get_key_display_recording_style():
    """Get key display stylesheet when recording."""
    return f"""
        QLabel {{
            background-color: {COLORS['terminal_bg_darker']};
            color: {COLORS['neon_red']};
            border: 2px solid {COLORS['neon_red']};
            border-radius: 3px;
            padding: 8px 12px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_medium']}pt;
            font-weight: {FONTS['weight_bold']};
            min-width: 150px;
        }}
    """


def get_global_stylesheet():
    """Get global application stylesheet."""
    return f"""
        * {{
            font-family: {FONTS['family']};
        }}
        QWidget {{
            background-color: {COLORS['terminal_bg']};
            color: {COLORS['text_primary']};
        }}
        {get_tooltip_style()}
        {get_message_box_style()}
        {get_scrollbar_style()}
    """


def get_section_frame_style():
    """Get section frame stylesheet for grouping settings."""
    return f"""
        QFrame {{
            background-color: {COLORS['terminal_surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 12px;
            margin: 4px 0px;
        }}
    """


def get_slider_style():
    """Get modern slider stylesheet with neon accent."""
    return f"""
        QSlider::groove:horizontal {{
            border: 1px solid {COLORS['border']};
            height: 6px;
            background: {COLORS['input_bg']};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {COLORS['neon_green']};
            border: 2px solid {COLORS['neon_green_dim']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {COLORS['neon_green']};
            border: 2px solid {COLORS['text_bright']};
        }}
        QSlider::sub-page:horizontal {{
            background: {COLORS['neon_green_dim']};
            border-radius: 3px;
        }}
        QSlider::add-page:horizontal {{
            background: {COLORS['terminal_bg_darker']};
            border-radius: 3px;
        }}
    """


def get_level_meter_style():
    """Get audio level meter progress bar stylesheet with gradient."""
    return f"""
        QProgressBar {{
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            background-color: {COLORS['terminal_bg_darker']};
            height: 12px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['neon_green']},
                stop:0.6 {COLORS['neon_yellow']},
                stop:1 {COLORS['neon_red']}
            );
            border-radius: 2px;
        }}
    """


def get_audio_panel_style():
    """Get audio panel container frame style."""
    return f"""
        QFrame#AudioPanel {{
            background-color: {COLORS['terminal_surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: {SPACING['lg']}px;
        }}
        QFrame#AudioPanel QLabel {{
            color: {COLORS['text_primary']};
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
        }}
        QFrame#AudioPanel QLabel#SectionTitle {{
            color: {COLORS['neon_green']};
            font-size: {FONTS['size_medium']}pt;
            font-weight: {FONTS['weight_bold']};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        QFrame#AudioPanel QLabel#ValueLabel {{
            color: {COLORS['neon_green']};
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            font-weight: {FONTS['weight_medium']};
            min-width: {VALUE_COLUMN_WIDTH}px;
        }}
        QFrame#AudioPanel QLabel#SubLabel {{
            color: {COLORS['text_muted']};
            font-size: {FONTS['size_small']}pt;
        }}
    """


def get_device_combobox_style():
    """Get wider combobox style for audio device names."""
    return f"""
        QComboBox {{
            background-color: {COLORS['input_bg']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 10px 14px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            min-width: 200px;
        }}
        QComboBox:hover {{
            border-color: {COLORS['neon_green_dim']};
            background-color: {COLORS['input_hover']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['neon_green']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 35px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 7px solid {COLORS['text_secondary']};
            margin-right: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['terminal_surface']};
            color: {COLORS['text_primary']};
            selection-background-color: {COLORS['neon_green']};
            selection-color: {COLORS['terminal_bg']};
            border: 1px solid {COLORS['border']};
            outline: none;
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            min-height: 24px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLORS['input_hover']};
        }}
    """


def get_test_button_style():
    """Get test microphone button style."""
    return f"""
        QPushButton {{
            background-color: {COLORS['button_hover']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['neon_green']};
            border-radius: 4px;
            padding: 8px 16px;
            font-family: {FONTS['family']};
            font-size: {FONTS['size_normal']}pt;
            font-weight: {FONTS['weight_medium']};
        }}
        QPushButton:hover {{
            border-color: {COLORS['neon_green']};
            color: {COLORS['neon_green']};
            background-color: {COLORS['terminal_bg_darker']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['terminal_bg_darker']};
            border-color: {COLORS['neon_green']};
        }}
        QPushButton:disabled {{
            color: {COLORS['text_muted']};
            border-color: {COLORS['terminal_bg_darker']};
        }}
    """
