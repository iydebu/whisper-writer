# WhisperWriter

**Talk, and it types.** A speech-to-text app for Windows. Hold **F4**, speak, let go — your words are typed into whatever app you are using: chat, email, a code editor, a document.

- Runs fully on your own PC. No cloud, no account, no monthly fee.
- Fast on NVIDIA GPUs (CUDA, via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)); also works on the CPU.
- Built for Indian speakers: Indian-accent English, Hinglish to English, and Hinglish written in Roman letters ("main theek hoon").
- Five ways to record: hold to talk, press to start/stop, voice activity, continuous, or a spoken wake word.
- Settings window, two themes, and a small status bar while you speak.

## Get the installer

The source code is free and open here under the MIT license.
The official, ready-to-use Windows installer (.exe, about 2.5 GB, speech models included) is only for people who buy it:
**[whisperwriter.iydebu.com](https://whisperwriter.iydebu.com)** — pay what you want, from $3.

Buying the installer supports the project. Official builds are not posted on GitHub Releases.
If you prefer, you can build it yourself from source for free (see [Build the installer](#build-the-installer) below).

## Language modes

| Mode | You speak | You get |
|---|---|---|
| `indian_english` | English with an Indian accent | English |
| `hinglish` | Mixed Hindi + English | English (translated) |
| `hinglish_roman` | Hindi or Hinglish | Hindi in English letters, no translation |

`model_quality` (small / medium / large) trades speed for accuracy in the Hinglish modes.

## Run from source

Needs Windows 10/11, Python 3.10–3.12. An NVIDIA GPU is suggested.

```bat
py -3.12 -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python models\setup_models.py   :: downloads + converts the speech models
venv\Scripts\python run.py
```

`install.bat` does the same with checks for your GPU, RAM and disk space. Settings are saved to `src/config.yaml` (created from `src/default_config.yaml`).

## Build the installer

Needs [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```bat
build\build.bat
```

Output: `dist\installer\WhisperWriter_Setup_<version>.exe`.

## Models

All models are downloaded from Hugging Face by `models/setup_models.py` and converted to CTranslate2 format:

| Model | License |
|---|---|
| [Tejveer12/Indian-Accent-English-Whisper-Finetuned](https://huggingface.co/Tejveer12/Indian-Accent-English-Whisper-Finetuned) | MIT |
| [vasista22/whisper-hindi-small / medium / large-v2](https://huggingface.co/vasista22) | Apache-2.0 |
| [Oriserve/Whisper-Hindi2Hinglish-Apex / Prime](https://huggingface.co/Oriserve) | Apache-2.0 |
| [Helsinki-NLP/opus-mt-hi-en](https://huggingface.co/Helsinki-NLP/opus-mt-hi-en) | Apache-2.0 |
| [Vosk small English](https://alphacephei.com/vosk/models) (wake word) | Apache-2.0 |

## Credits

Written by **Devashish Tiwari** ([iydebu](https://iydebu.com)).
Inspired by [savbell/whisper-writer](https://github.com/savbell/whisper-writer), the original "press a hotkey, speak, it types" Whisper app. Early versions of this project followed its structure; those parts have since been rewritten, and no code from it remains here.

## License

[MIT](LICENSE)
