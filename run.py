"""
WhisperWriter entry point -- used both from source (python run.py) and by the
PyInstaller build (build/WhisperWriter.spec). run_frozen.py is gone.
"""
import ctypes
import os
import sys

# --selftest [file.wav]: load the model, transcribe one clip, write the result to
# whisperwriter-selftest.log, exit 0/1. No UI, no hotkeys, runs next to a live instance.
SELFTEST = '--selftest' in sys.argv

# ponytail: OS mutex auto-releases on crash; no stale pid-file cleanup needed.
# The installer also uses this name (AppMutex) to close the app before upgrade/uninstall.
_mutex = None if SELFTEST else ctypes.windll.kernel32.CreateMutexW(None, False, 'WhisperWriterSingleInstanceMutex')
if _mutex and ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(0, 'WhisperWriter is already running.', 'WhisperWriter', 0x40)
    sys.exit(0)


def release_instance_lock():
    """Release the single-instance mutex so a restart can re-acquire it."""
    global _mutex
    if _mutex:
        ctypes.windll.kernel32.CloseHandle(_mutex)
        _mutex = None


FROZEN = getattr(sys, 'frozen', False)
ROOT = os.path.dirname(os.path.abspath(sys.executable if FROZEN else __file__))
if not FROZEN:
    sys.path.insert(0, os.path.join(ROOT, 'src'))

import paths  # noqa: E402  (needs src on sys.path first)

os.makedirs(paths.USER_DIR, exist_ok=True)

if FROZEN:
    # Windowed build has no console: sys.stdout/stderr are None and any library
    # that writes to them would crash. Send everything to a log file instead.
    _log_path = paths.LOG_PATH.replace('.log', '-selftest.log') if SELFTEST else paths.LOG_PATH
    _log = open(_log_path, 'w', encoding='utf-8', errors='replace', buffering=1)
    sys.stdout = sys.stderr = _log

    # ctranslate2 loads cuBLAS by name at first GPU use. The setup ships the two
    # DLLs in _internal/cuda; preloading them by full path makes that lookup hit
    # without needing a CUDA toolkit or PATH changes. No NVIDIA driver -> the load
    # fails and the app falls back to CPU.
    _cuda_dir = os.path.join(paths.BUNDLE_DIR, 'cuda')
    for _dll in ('cublasLt64_12.dll', 'cublas64_12.dll'):
        try:
            ctypes.WinDLL(os.path.join(_cuda_dir, _dll))
        except OSError as _e:
            print(f'GPU library not loaded ({_dll}): {_e}')

    # First run: start from the shipped defaults instead of an empty settings window.
    if not os.path.exists(paths.CONFIG_PATH) and os.path.exists(paths.DEFAULT_CONFIG_PATH):
        with open(paths.DEFAULT_CONFIG_PATH, encoding='utf-8') as _f:
            _cfg = _f.read()
        # Default is the medium model (usable on CPU). With an NVIDIA driver and the
        # large model installed, start on large -- it is the most accurate.
        _has_gpu = os.path.exists(os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'nvcuda.dll'))
        if _has_gpu and os.path.isdir(os.path.join(paths.MODELS_DIR, 'whisper-hindi2hinglish-prime')):
            _cfg = _cfg.replace('model_quality: medium', 'model_quality: large')
        with open(paths.CONFIG_PATH, 'w', encoding='utf-8') as _f:
            _f.write(_cfg)
        print(f'First run: wrote {paths.CONFIG_PATH} (GPU driver found: {_has_gpu})')
else:
    # ponytail: transcriptions can contain non-ASCII; Windows console defaults to cp1252 and raises.
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, 'reconfigure'):
            _stream.reconfigure(encoding='utf-8', errors='replace')

print('Starting WhisperWriter...')
os.chdir(paths.APP_DIR)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(paths.USER_DIR, '.env') if FROZEN else None)

# ponytail: models are pre-downloaded; skip HF Hub network check (it hangs for minutes).
# Set HF_HUB_OFFLINE=0 in .env when downloading a new model.
os.environ.setdefault('HF_HUB_OFFLINE', '1')

if SELFTEST:
    import selftest
    sys.exit(selftest.run(sys.argv[sys.argv.index('--selftest') + 1:]))

from main import main  # noqa: E402

try:
    main()
except SystemExit:
    raise
except BaseException as e:
    import traceback
    traceback.print_exc()
    if FROZEN:
        ctypes.windll.user32.MessageBoxW(
            0, f'WhisperWriter stopped because of an error:\n\n{e}\n\nFull details are in:\n{paths.LOG_PATH}',
            'WhisperWriter', 0x10)
    raise
