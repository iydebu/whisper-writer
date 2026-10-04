"""
`WhisperWriter.exe --selftest [clip.wav]` -- checks an install without touching the UI.

Imports Qt first (as the real app does; that order once broke onnxruntime), loads the
model from the user's config, transcribes one clip with the VAD filter on, and prints
the device and text. Exit code 0 = everything loaded and ran.
"""
import os
import time
import traceback

import paths


def run(args):
    try:
        clip = args[0] if args else os.path.join(paths.ASSETS_DIR, 'selftest.wav')
        print(f'app dir:    {paths.APP_DIR}')
        print(f'config:     {paths.CONFIG_PATH} (exists: {os.path.exists(paths.CONFIG_PATH)})')
        print(f'models dir: {paths.MODELS_DIR} -> {sorted(os.listdir(paths.MODELS_DIR)) if os.path.isdir(paths.MODELS_DIR) else "MISSING"}')

        from PyQt5.QtWidgets import QApplication  # noqa: F401  (load Qt before onnxruntime)
        import onnxruntime
        print(f'onnxruntime {onnxruntime.__version__} ok')

        from utils import load_config_schema, load_config_values
        from transcription import create_local_model, get_model_name
        config = load_config_values(load_config_schema())
        config['misc']['print_to_terminal'] = True
        mo = config['model_options']
        print(f"settings:   language_mode={mo['language_mode']} model_quality={mo['model_quality']} device={mo['device']}")
        print(f"model:      {get_model_name(mo['model_quality'], mo['language_mode'])}")

        t = time.time()
        model = create_local_model(config)
        print(f'model load: {time.time() - t:.1f}s on {model.model.device}')

        t = time.time()
        from transcription import transcribe_local
        mo['vad_filter'] = True  # exercise onnxruntime (silero VAD) too
        text = transcribe_local(config, clip, model).strip()
        print(f'transcribe: {time.time() - t:.1f}s  clip={os.path.basename(clip)}')
        print(f'TEXT: {text!r}')

        # About window must import and render in the frozen build (it is lazy-imported by the tray).
        from PyQt5.QtWidgets import QApplication as _QApp
        _app = _QApp.instance() or _QApp([])
        from ui.about_window import AboutWindow, detect_device
        about = AboutWindow(paths.BUNDLE_DIR, 'selftest')
        shot = paths.LOG_PATH.replace('.log', '-about.png')
        about.grab().save(shot)
        print(f'about:      rendered {about.width()}x{about.height()}, device={detect_device()} -> {shot}')
        print('SELFTEST PASSED')
        return 0
    except Exception:
        traceback.print_exc()
        print('SELFTEST FAILED')
        return 1
