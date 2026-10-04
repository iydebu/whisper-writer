"""
Automated check proving the hinglish_roman models (Whisper-Hindi2Hinglish-Apex
and Whisper-Hindi2Hinglish-Prime, converted to CTranslate2) output Latin-script
(roman) Hinglish text rather than Devanagari script.

Downloads 3 short sample clips from the Oriserve/Whisper-Hindi2Hinglish-Apex
HF repo's audios/ folder, transcribes each with both converted models using
language='en' and language='hi', and asserts that every language='en' output
is non-empty and contains no Devanagari codepoints.

Run with: D:/Personal/whisper-writer/venv/Scripts/python.exe models/test_hinglish_roman.py
"""

import os
import re
import sys

from huggingface_hub import hf_hub_download
from faster_whisper import WhisperModel

REPO_ID = "Oriserve/Whisper-Hindi2Hinglish-Apex"

# Filenames discovered ahead of time via huggingface_hub.list_repo_files()
# against the audios/ folder of REPO_ID. Picking 3 short .wav clips.
SAMPLE_FILENAMES = [
    "audios/663eb653-d6b5-4fda-b5f2-9ef98adc0a61_0_1098400_1118688.wav",
    "audios/c0637211-7384-4abc-af69-5aacf7549824_1_2417088_2444224.wav",
    "audios/f5e0178c-354c-40c9-b3a7-687c86240a77_1_1152496_1175488.wav",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(SCRIPT_DIR, "_samples")

MODEL_PATHS = {
    "apex": os.path.join(SCRIPT_DIR, "whisper-hindi2hinglish-apex"),
    "prime": os.path.join(SCRIPT_DIR, "whisper-hindi2hinglish-prime"),
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"


def download_samples():
    """Download the 3 sample clips into models/_samples/, skipping if present."""
    local_paths = []
    for filename in SAMPLE_FILENAMES:
        base_name = os.path.basename(filename)
        expected_local = os.path.join(SAMPLES_DIR, filename)
        if os.path.exists(expected_local):
            print(f"[download] already present: {base_name}")
            local_paths.append(expected_local)
            continue
        print(f"[download] fetching: {base_name}")
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=SAMPLES_DIR,
        )
        local_paths.append(path)
    return local_paths


def transcribe(model, audio_path, language):
    segments, info = model.transcribe(
        audio_path, language=language, task="transcribe"
    )
    text = "".join(s.text for s in segments)
    return text


def main():
    sample_paths = download_samples()

    print()
    print(f"Loading models on device={DEVICE}, compute_type={COMPUTE_TYPE} ...")
    models = {}
    for model_name, model_path in MODEL_PATHS.items():
        print(f"  loading {model_name} from {model_path}")
        models[model_name] = WhisperModel(
            model_path, device=DEVICE, compute_type=COMPUTE_TYPE
        )

    results = []  # (model_name, clip_name, language, text)

    print()
    print("Transcribing...")
    for model_name, model in models.items():
        for audio_path in sample_paths:
            clip_name = os.path.basename(audio_path)
            for language in ("en", "hi"):
                text = transcribe(model, audio_path, language)
                results.append((model_name, clip_name, language, text))

    # Print table
    print()
    header = f"{'model':6} | {'clip':60} | {'lang':4} | text"
    print(header)
    print("-" * len(header))
    for model_name, clip_name, language, text in results:
        print(f"{model_name:6} | {clip_name:60} | {language:4} | {text}")

    # Informational: does the hi variant contain Devanagari?
    print()
    print("Informational: Devanagari presence in language='hi' outputs:")
    for model_name, clip_name, language, text in results:
        if language != "hi":
            continue
        has_deva = bool(DEVANAGARI_RE.search(text))
        print(
            f"  {model_name} | {clip_name} | hi | contains_devanagari={has_deva}"
        )

    # Assertion: every language='en' result must be non-empty roman text,
    # with no Devanagari codepoints.
    print()
    failures = []
    for model_name, clip_name, language, text in results:
        if language != "en":
            continue
        stripped = text.strip()
        is_nonempty = len(stripped) > 0
        has_deva = bool(DEVANAGARI_RE.search(text))
        ok = is_nonempty and not has_deva
        status = "OK" if ok else "FAIL"
        print(
            f"  [{status}] {model_name} | {clip_name} | en | "
            f"nonempty={is_nonempty} devanagari={has_deva}"
        )
        if not ok:
            failures.append((model_name, clip_name, text))

    print()
    if failures:
        print("FAILURES:")
        for model_name, clip_name, text in failures:
            print(f"  {model_name} | {clip_name} -> {text!r}")
        print("FAIL: one or more language=en outputs were empty or contained Devanagari script")
        sys.exit(1)

    print("PASS: all language=en outputs are Latin-script roman Hinglish")
    sys.exit(0)


if __name__ == "__main__":
    main()
