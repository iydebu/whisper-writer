"""
One dictation: play the "listening" cue, capture the mic until the user (or silence) ends it,
transcribe the clip, and hand the text back. Runs off the UI thread.

Signals
  stateChanged(str)  'recording' -> 'transcribing' -> 'idle'  (or 'error')
  textReady(str)     the transcribed text ('' when nothing was heard or something failed)
"""
import os
import queue
import tempfile
import threading
import traceback
import wave

import numpy as np
import sounddevice as sd
import webrtcvad
from PyQt5.QtCore import QThread, pyqtSignal
from pygame import mixer as pygame_mixer

from transcription import transcribe

FRAME_MS = 30            # webrtcvad accepts 10, 20 or 30 ms frames
MIN_CLIP_SECONDS = 0.3   # shorter than this is a tap/key bounce; Whisper would invent words from the hiss
SILENCE_ENDS = ('voice_activity_detection', 'continuous', 'wake_word')   # modes that stop on silence


class SpeechGate:
    """Decides if one frame is speech: WebRTC VAD *and* a loudness floor must both agree.

    One knob, voice_threshold 0..1, drives both: VAD aggressiveness 0..3 and an RMS floor
    from -60 dB (hears everything) to -20 dB (only clear, close speech).
    """

    def __init__(self, threshold, sample_rate):
        threshold = min(1.0, max(0.0, float(threshold)))
        self.vad = webrtcvad.Vad(min(3, int(threshold * 3)))
        self.floor_db = -60 + 40 * threshold
        self.rate = sample_rate

    def is_speech(self, frame):
        loud = 20 * np.log10(np.sqrt(np.mean((frame / 32768.0) ** 2)) + 1e-10) > self.floor_db
        return loud and self.vad.is_speech(frame.tobytes(), self.rate)


class DictationThread(QThread):
    stateChanged = pyqtSignal(str)
    textReady = pyqtSignal(str)

    def __init__(self, config, local_model=None, project_root=None):
        super().__init__()
        self.config = config
        self.local_model = local_model
        self.project_root = project_root
        self._listening = threading.Event()   # cleared = stop capturing, keep what we have
        self._listening.set()
        self._cancelled = threading.Event()   # set = drop everything, emit nothing
        self._cue = None                      # pygame Sound must outlive play()

    # -- control (called from the UI thread) ---------------------------------------------
    def finish_recording(self):
        """Stop the mic now and transcribe what was said so far."""
        self._listening.clear()

    def cancel(self):
        """Abandon this dictation and wait until the thread has exited."""
        self._cancelled.set()
        self._listening.clear()
        self.stateChanged.emit('idle')
        self.wait()

    # -- worker ---------------------------------------------------------------------------
    def _log(self, *msg):
        if self.config['misc']['print_to_terminal']:
            print(*msg)

    def run(self):
        clip = None
        try:
            self.stateChanged.emit('recording')
            self._play_cue('Listening.mp3')
            self._log('Recording...')
            samples, rate = self._capture()
            if self._cancelled.is_set():
                return

            text = ''
            if samples.size >= rate * MIN_CLIP_SECONDS:
                self.stateChanged.emit('transcribing')
                self._log('Transcribing...')
                clip = self._to_wav(samples, rate)
                text = transcribe(self.config, clip, self.local_model)
            if self._cancelled.is_set():
                return
            self.stateChanged.emit('idle')
            self.textReady.emit(text)
        except Exception:
            traceback.print_exc()
            self.stateChanged.emit('error')
            self.textReady.emit('')
        finally:
            self._listening.clear()
            if clip:
                try:
                    os.remove(clip)
                except OSError:
                    pass

    def _play_cue(self, name):
        path = os.path.join(self.project_root or '', 'assets', name)
        if self.project_root and os.path.exists(path):
            pygame_mixer.init()
            self._cue = pygame_mixer.Sound(path)
            self._cue.set_volume(0.2)
            self._cue.play()

    def _capture(self):
        """Read the mic in FRAME_MS frames until told to stop or, in silence modes, until the
        speaker has been quiet for silence_duration ms after saying something."""
        opts = self.config['recording_options']
        rate = opts['sample_rate'] or 16000
        mode = opts['recording_mode'] or 'voice_activity_detection'
        quiet_limit = (opts['silence_duration'] or 900) // FRAME_MS
        gate = SpeechGate(opts.get('voice_threshold', 0.5), rate) if mode in SILENCE_ENDS else None
        per_frame = rate * FRAME_MS // 1000

        frames = queue.Queue()
        kept, pending = [], np.empty(0, dtype=np.int16)
        quiet = 0

        # sound_device may be 0 (a real mic index), so it is passed through as-is, never `or None`.
        with sd.InputStream(samplerate=rate, channels=1, dtype='int16', blocksize=per_frame,
                            device=opts.get('sound_device'),
                            callback=lambda data, n, t, status: frames.put(data[:, 0].copy())):
            while self._listening.is_set() and not self._cancelled.is_set():
                try:
                    pending = np.concatenate((pending, frames.get(timeout=0.1)))
                except queue.Empty:
                    continue
                while pending.size >= per_frame:
                    frame, pending = pending[:per_frame], pending[per_frame:]
                    if gate is None or gate.is_speech(frame):
                        kept.append(frame)
                        quiet = 0
                    elif kept:
                        quiet += 1
                        if quiet >= quiet_limit:
                            self._listening.clear()
                            break

        samples = np.concatenate(kept) if kept else np.empty(0, dtype=np.int16)
        self._log('Recording finished. Size:', samples.size)
        return samples, rate

    @staticmethod
    def _to_wav(samples, rate):
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        with wave.open(path, 'wb') as out:
            out.setnchannels(1)
            out.setsampwidth(2)   # int16
            out.setframerate(rate)
            out.writeframes(samples.tobytes())
        return path
