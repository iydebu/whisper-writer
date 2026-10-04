"""
Where things live, for both the source checkout and the installed (PyInstaller) build.

Source checkout:  everything under the repo; config stays in src/config.yaml.
Installed build:  code + assets inside the exe's _internal folder (read-only),
                  models next to the exe in {app}/models (installed by the setup),
                  config + log in %APPDATA%/WhisperWriter (writable, survives upgrades).
"""
import os
import sys

FROZEN = getattr(sys, 'frozen', False)

if FROZEN:
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = sys._MEIPASS
    SRC_DIR = BUNDLE_DIR
    USER_DIR = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'WhisperWriter')
else:
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    BUNDLE_DIR = APP_DIR
    SRC_DIR = os.path.join(APP_DIR, 'src')
    USER_DIR = SRC_DIR

MODELS_DIR = os.path.join(APP_DIR, 'models')
ASSETS_DIR = os.path.join(BUNDLE_DIR, 'assets')
ICON_PATH = os.path.join(BUNDLE_DIR, 'logo.ico')
SCHEMA_PATH = os.path.join(SRC_DIR, 'config_schema.yaml')
DEFAULT_CONFIG_PATH = os.path.join(SRC_DIR, 'default_config.yaml')
CONFIG_PATH = os.path.join(USER_DIR, 'config.yaml')
LOG_PATH = os.path.join(USER_DIR, 'whisperwriter.log')
