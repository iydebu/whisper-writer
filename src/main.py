"""
WhisperWriter app: tray icon, global hotkey, optional wake word, and the dictation loop
(hotkey -> DictationThread -> text typed at the cursor).
"""
import os, sys, time

import paths

SOUND_VOLUME = 0.2


def main():
    """Load config, then the Whisper model, and only THEN Qt: CUDA must initialise before
    Qt's OpenGL stack or the two clash."""
    from utils import load_config_schema, load_config_values
    schema = load_config_schema()
    config = load_config_values(schema)

    model = None
    if os.path.exists(paths.CONFIG_PATH):
        print('Loading Whisper model...')
        from transcription import create_local_model
        model = create_local_model(config)

    from ui.styles import set_theme
    set_theme(config['misc'].get('theme', 'neon_green'))

    # Qt and everything that pulls it in, imported late on purpose (see above).
    import pygame.mixer
    import pynput.keyboard
    from PyQt5 import QtGui, QtWidgets
    from key_listener import KeyListener
    from result_thread import DictationThread
    from wake_word_listener import WakeWordListener
    from ui.main_window import HomeWindow
    from ui.settings_window import SettingsWindow
    from ui.status_window import StatusWindow

    kit = {
        'pygame_mixer': pygame.mixer, 'Controller': pynput.keyboard.Controller,
        'QIcon': QtGui.QIcon, 'QApplication': QtWidgets.QApplication,
        'QSystemTrayIcon': QtWidgets.QSystemTrayIcon, 'QMenu': QtWidgets.QMenu,
        'QAction': QtWidgets.QAction, 'QMessageBox': QtWidgets.QMessageBox,
        'KeyListener': KeyListener, 'DictationThread': DictationThread,
        'WakeWordListener': WakeWordListener, 'HomeWindow': HomeWindow,
        'SettingsWindow': SettingsWindow, 'StatusWindow': StatusWindow,
    }
    WhisperWriterApp(paths.BUNDLE_DIR, schema, config, model, kit).run()


class WhisperWriterApp:
    def __init__(self, project_root, schema, config, local_model, modules):
        # project_root = bundle dir: read-only files (logo, sounds, VERSION) live there.
        self.project_root = project_root
        self.config = config
        self.local_model = local_model
        self.m = modules
        self.wake_word_listener = None
        self.dictation = None

        self.app = self.m['QApplication'](sys.argv)
        self.app.setQuitOnLastWindowClosed(False)   # tray app: hidden windows are normal
        # Every quit path must stop the audio threads first. Otherwise sounddevice's
        # atexit handler terminates PortAudio while they still hold a stream, and they
        # spin forever on 'PortAudio not initialized'.
        self.app.aboutToQuit.connect(self.stop_audio_threads)
        self.app.setWindowIcon(self._icon())

        self.settings_window = self.m['SettingsWindow'](schema)
        self.settings_window.settingsClosed.connect(self.on_settings_closed)

        if os.path.exists(paths.CONFIG_PATH):
            self.start_up()
        else:
            print('First run: no config yet, opening Settings...')
            self.settings_window.show()

    @property
    def _mode(self):
        return self.config['recording_options']['recording_mode']

    def _icon(self):
        return self.m['QIcon'](os.path.join(self.project_root, 'logo.ico'))

    def _play(self, sound_name):
        path = os.path.join(self.project_root, 'assets', sound_name)
        if os.path.exists(path):
            self._sound = self.m['pygame_mixer'].Sound(path)   # keep a ref or it is cut off
            self._sound.set_volume(SOUND_VOLUME)
            self._sound.play()

    # -- start-up --------------------------------------------------------------------------
    def start_up(self):
        self.keyboard = self.m['Controller']()

        self.hotkey = self.m['KeyListener'](self.config)
        self.hotkey.activationKeyPressed.connect(self.on_hotkey_down)
        self.hotkey.activationKeyReleased.connect(self.on_hotkey_up)

        self.home = self.m['HomeWindow']()
        self.home.settingsRequested.connect(self.settings_window.show)
        self.home.listenRequested.connect(self.hotkey.start_listening)

        self.status_window = None
        if not self.config['misc']['hide_status_window']:
            self.status_window = self.m['StatusWindow'](self.config)
            # Closing the pill by hand cancels the dictation it belongs to.
            self.status_window.closeSignal.connect(self.end_dictation)

        self.hotkey.start_listening()   # global hotkey is live from launch
        self._start_wake_word()
        self._build_tray()

    def _start_wake_word(self):
        if self._mode != 'wake_word':
            return
        self.wake_word_listener = self.m['WakeWordListener'](self.config)
        self.wake_word_listener.wakeWordDetected.connect(self.on_hotkey_down)
        self.wake_word_listener.errorSignal.connect(lambda msg: print(f'Wake word listener error: {msg}'))
        self.wake_word_listener.start()

    def _build_tray(self):
        menu = self.m['QMenu']()
        for label, handler in (('Show Main Menu', self.show_home), ('Open Settings', self.settings_window.show),
                               ('About', self.show_about), ('Exit', self.m['QApplication'].quit)):
            action = self.m['QAction'](label, self.app)
            action.triggered.connect(handler)
            menu.addAction(action)
        self.tray_icon = self.m['QSystemTrayIcon'](self._icon(), self.app)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def on_settings_closed(self):
        """First run and Settings was closed without saving: carry on with the defaults."""
        if os.path.exists(paths.CONFIG_PATH):
            return
        self.m['QMessageBox'].information(
            self.settings_window, 'Default settings',
            'Nothing was saved, so WhisperWriter will start with its default settings. '
            'You can change them any time from the tray icon.')
        if self.local_model is None:
            print('Loading Whisper model...')
            from transcription import create_local_model
            self.local_model = create_local_model(self.config)
        self.start_up()

    # -- windows ---------------------------------------------------------------------------
    def _bring_up(self, window):
        window.show()
        window.raise_()
        window.activateWindow()

    def show_home(self):
        self._bring_up(self.home)

    def show_about(self):
        try:
            with open(os.path.join(self.project_root, 'VERSION'), encoding='utf-8') as f:
                version = f.read().strip()
        except OSError:
            version = 'dev'
        from ui.about_window import AboutWindow
        self.about_window = AboutWindow(self.project_root, version)
        self._bring_up(self.about_window)

    # -- dictation -------------------------------------------------------------------------
    def _busy(self):
        return self.dictation is not None and self.dictation.isRunning()

    def on_hotkey_down(self):
        """Idle: start a dictation. Busy: toggle mode finishes it, continuous mode cancels the loop."""
        if not self._busy():
            self.begin_dictation()
        elif self._mode == 'press_to_toggle':
            self.dictation.finish_recording()
        elif self._mode == 'continuous':
            self.end_dictation()

    def on_hotkey_up(self):
        if self._mode == 'hold_to_record' and self._busy():
            self.dictation.finish_recording()

    def begin_dictation(self):
        if self._busy():
            return
        if self.dictation is not None:
            self.dictation.wait()   # let the finished thread fully unwind before replacing it
        if self.wake_word_listener:
            self.wake_word_listener.pause()   # it must not hear the dictation it triggered

        job = self.m['DictationThread'](self.config, self.local_model, self.project_root)
        if self.status_window is not None:
            job.stateChanged.connect(self.status_window.updateStatus)
        job.textReady.connect(self.on_text_ready)
        self.dictation = job
        job.start()

    def end_dictation(self):
        if self._busy():
            self.dictation.cancel()
        if self.wake_word_listener:
            self.wake_word_listener.resume()

    def on_text_ready(self, text):
        self.type_text(text, self.config['post_processing']['writing_key_press_delay'])
        self._play('Complete.mp3')
        self.hotkey.start_listening()   # re-arm: some apps swallow the global hook while we type
        if self._mode == 'continuous':
            self.begin_dictation()
        elif self.wake_word_listener:
            self.wake_word_listener.resume()

    def type_text(self, text, delay):
        for ch in text:
            self.keyboard.press(ch)
            self.keyboard.release(ch)
            time.sleep(delay)

    # -- shutdown --------------------------------------------------------------------------
    def stop_audio_threads(self):
        """Stop every thread that holds an audio stream. Safe to call more than once."""
        if self.wake_word_listener:
            self.wake_word_listener.stop()
            self.wake_word_listener = None
        if self._busy():
            self.dictation.cancel()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    main()
