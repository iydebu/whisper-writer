import json
import os
import traceback

import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal

import paths

MODEL_PATH = os.path.join(paths.MODELS_DIR, 'vosk-model-small-en-us-0.15')
SAMPLE_RATE = 16000
BLOCK_SIZE = 4000


# A wake word said in isolation or with accent is short/varied, so confidence can be low.
# We set confidence threshold to 0.0 and filter by phonetic / accent word variants.
MIN_CONFIDENCE = 0.0

ACCENT_WHISPER_VARIANTS = (
    'whisper', 'whispers', 'whispering', 'whispered', 'whisperer',
    'wisper', 'wispers', 'wispering', 'wispered',
    'visper', 'vispers', 'vispering', 'vispered',
    'wesper', 'wespers', 'wesp',
    'vesper', 'vespers',
    'whasper', 'wasper', 'vysper', 'worsper'
)

SPLIT_WHISPER_VARIANTS = (
    'was per', 'is per', 'west per', 'which per', 'with per', 'whis per', 'mr per', 'as per'
)


def phrase_heard(result, phrase):
    """
    True if the wake phrase appears in a Vosk final or partial result.

    The final/partial word matches exact prefix, common accent/phonetic variants (including
    Indian English pronunciations like 'visper', 'wisper', 'wesper', etc.), or
    split-word recognitions (like 'was per', 'is per').
    """
    target = phrase.lower().strip()
    if not target:
        return False

    text = (result.get('text') or result.get('partial') or '').lower()
    if target == 'whisper':
        if any(v in text for v in ACCENT_WHISPER_VARIANTS) or any(s in text for s in SPLIT_WHISPER_VARIANTS):
            return True

    heard = [w['word'].lower() for w in result.get('result', [])
             if w.get('conf', 0) >= MIN_CONFIDENCE]
    target_words = target.split()

    def is_target_variant(word, target_word):
        word = word.lower()
        target_word = target_word.lower()
        if word.startswith(target_word):
            return True
        if target_word == 'whisper':
            return any(word.startswith(v) for v in ACCENT_WHISPER_VARIANTS)
        return False

    def matches(window):
        if len(window) != len(target_words) or window[:-1] != target_words[:-1]:
            return False
        return is_target_variant(window[-1], target_words[-1])

    return any(matches(heard[i:i + len(target_words)])
               for i in range(len(heard) - len(target_words) + 1))


class WakeWordListener(QThread):
    wakeWordDetected = pyqtSignal()
    errorSignal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        options = config['recording_options']
        self.phrase = (options.get('wake_word_phrase') or 'whisper').strip()
        # ponytail: `or None` would drop device index 0, a valid mic, back to system default
        self.sound_device = options.get('sound_device')
        self._running = False
        self._paused = False

    def pause(self):
        """Ignore audio while dictation is recording, so it can't hear itself."""
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self._paused = False
        self.wait(3000)

    def run(self):
        try:
            from vosk import Model, KaldiRecognizer, SetLogLevel
        except ImportError as e:
            self.errorSignal.emit(f'vosk not installed: {e}')
            return

        if not os.path.isdir(MODEL_PATH):
            self.errorSignal.emit(f'Vosk model missing at {MODEL_PATH}')
            return

        try:
            SetLogLevel(-1)
            model = Model(MODEL_PATH)
            # Full vocabulary on purpose: restricting the grammar to the wake phrase
            # forces every noise to decode as the wake word (measured 4 false
            # positives in 30s of silence, versus 0 with the full vocabulary).
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)
            recognizer.SetWords(True)
        except Exception as e:
            traceback.print_exc()
            self.errorSignal.emit(str(e))
            return

        self._running = True
        while self._running:
            # The stream must be released while paused: ResultThread opens its own
            # stream on the same device, and two concurrent streams break both.
            if self._paused:
                self.msleep(50)
                continue

            detected = False
            try:
                with sd.RawInputStream(
                    samplerate=SAMPLE_RATE,
                    blocksize=BLOCK_SIZE,
                    dtype='int16',
                    channels=1,
                    device=self.sound_device,
                ) as stream:
                    recognizer.Reset()
                    while self._running and not self._paused:
                        data, _ = stream.read(BLOCK_SIZE)
                        if recognizer.AcceptWaveform(bytes(data)):
                            res = json.loads(recognizer.Result())
                        else:
                            res = json.loads(recognizer.PartialResult())
                        if phrase_heard(res, self.phrase):
                            self._paused = True
                            detected = True
            except Exception as e:
                # The device is transiently unavailable while the recorder holds it,
                # or during shutdown. Back off and retry instead of killing the thread.
                if self._running:
                    traceback.print_exc()
                    self.msleep(500)
                continue

            # Signal only once the mic is released, so the recorder can claim it.
            if detected:
                self.wakeWordDetected.emit()


def _self_check():
    def res(*pairs):
        return {'result': [{'word': w, 'conf': c} for w, c in pairs]}

    assert phrase_heard(res(('hey', 1.0), ('whisper', 1.0)), 'whisper')
    assert phrase_heard(res(('whisper', 1.0)), 'whisper')
    # inflected forms and accent variations (e.g. Indian English visper/wisper) still count
    assert phrase_heard(res(('whispers', 1.0)), 'whisper')
    assert phrase_heard(res(('whispering', 1.0)), 'whisper')
    assert phrase_heard(res(('whispered', 1.0)), 'whisper')
    assert phrase_heard(res(('visper', 0.5)), 'whisper')
    assert phrase_heard(res(('wisper', 0.5)), 'whisper')
    assert phrase_heard(res(('wesper', 0.5)), 'whisper')
    # split-word recognitions for accent pronunciations
    assert phrase_heard({'text': 'was per', 'result': [{'word': 'was'}, {'word': 'per'}]}, 'whisper')
    assert phrase_heard({'text': 'is per', 'result': [{'word': 'is'}, {'word': 'per'}]}, 'whisper')
    # partial results for instant recognition
    assert phrase_heard({'partial': 'whisper'}, 'whisper')
    assert phrase_heard({'partial': 'visper'}, 'whisper')
    assert phrase_heard({'partial': 'was per'}, 'whisper')
    # a real, clearly-spoken wake word scores around 0.55 and must fire
    assert phrase_heard(res(('whisper', 0.55)), 'whisper')
    # a quiet or accent utterance scores far lower and must still fire
    assert phrase_heard(res(('whisper', 0.05)), 'whisper')
    assert not phrase_heard(res(('computer', 1.0)), 'whisper')
    # a word merely containing the phrase must not fire
    assert not phrase_heard(res(('crisp', 1.0)), 'whisper')
    assert not phrase_heard({}, 'whisper')
    # unrelated words must not fire
    assert not phrase_heard(res(('the', 1.0), ('quick', 1.0), ('fox', 1.0)), 'whisper')
    # multi-word phrases must match in order and adjacently
    assert phrase_heard(res(('hey', 1.0), ('whisper', 1.0)), 'hey whisper')
    assert not phrase_heard(res(('hey', 1.0), ('there', 1.0), ('whisper', 1.0)), 'hey whisper')
    # leading words of a phrase are matched exactly, not by suffix
    assert not phrase_heard(res(('heys', 1.0), ('whisper', 1.0)), 'hey whisper')
    print('wake_word_listener self-check OK')


if __name__ == '__main__':
    _self_check()
