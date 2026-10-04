#!/usr/bin/env python3
"""
Setup script for the WhisperWriter speech models.

Downloads Hugging Face models and converts them to CTranslate2 format
for use with faster-whisper.

Requirements:
    pip install transformers ctranslate2

Usage:
    python setup_models.py                          # convert every model
    python setup_models.py indian_english           # convert one model
    python setup_models.py hinglish-small hinglish-medium
"""

import os
import subprocess
import sys

MODELS = {
    "indian_english": ("Tejveer12/Indian-Accent-English-Whisper-Finetuned", "indian-accent-english-whisper"),
    "hinglish-small": ("vasista22/whisper-hindi-small", "whisper-hindi-small"),
    "hinglish-medium": ("vasista22/whisper-hindi-medium", "whisper-hindi-medium"),
    "hinglish-large": ("vasista22/whisper-hindi-large-v2", "whisper-hindi-large-v2"),
    "hinglish-roman": ("Oriserve/Whisper-Hindi2Hinglish-Apex", "whisper-hindi2hinglish-apex"),
    "hinglish-roman-large": ("Oriserve/Whisper-Hindi2Hinglish-Prime", "whisper-hindi2hinglish-prime"),
    # Hindi->English translator used by hinglish mode (see src/transcription.py)
    "translator": ("Helsinki-NLP/opus-mt-hi-en", "opus-mt-hi-en"),
}


def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    try:
        import transformers
    except ImportError:
        missing.append("transformers")

    try:
        import ctranslate2
    except ImportError:
        missing.append("ctranslate2")

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True


def convert_model(key):
    """Download one model and convert it to CTranslate2 format."""
    model_id, dir_name = MODELS[key]
    output_dir = os.path.join(os.path.dirname(__file__), dir_name)

    if os.path.exists(output_dir):
        print(f"[{key}] Model already exists at {output_dir}")
        response = input("Do you want to re-download and convert? (y/N): ")
        if response.lower() != 'y':
            print(f"[{key}] Skipping.")
            return True

    print(f"[{key}] Downloading and converting {model_id}...")
    print("This may take a while depending on your internet connection...")
    print()

    # The translator uses sentencepiece models; the Whisper repos ship only slow-tokenizer
    # files, so tokenizer.json is built below instead of copied.
    copy_files = ["source.spm", "target.spm"] if key == "translator" else ["preprocessor_config.json"]

    cmd = [
        sys.executable, "-m", "ctranslate2.converters.transformers",
        "--model", model_id,
        "--output_dir", output_dir,
        "--quantization", "int8_float16",
        "--copy_files", *copy_files,
        "--force",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[{key}] Error converting model: {e}")
        return False

    if key != "translator":
        print(f"[{key}] Building tokenizer.json...")
        try:
            from transformers import WhisperTokenizerFast
            WhisperTokenizerFast.from_pretrained(model_id).save_pretrained(output_dir)
        except Exception as e:
            print(f"[{key}] Error building tokenizer: {e}")
            return False

    print()
    print(f"[{key}] Converted successfully to: {output_dir}")
    return True


def main():
    keys = sys.argv[1:] or list(MODELS)
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        print(f"Unknown model(s): {', '.join(unknown)}")
        print(f"Valid models: {', '.join(MODELS)}")
        sys.exit(1)

    print("=" * 60)
    print("WhisperWriter Model Setup")
    print("=" * 60)
    print()
    print(f"Models: {', '.join(keys)}")
    print()

    if not check_dependencies():
        sys.exit(1)

    if not all(convert_model(key) for key in keys):
        print()
        print("Setup failed. Please check the errors above.")
        sys.exit(1)

    print()
    print("Setup complete!")


if __name__ == "__main__":
    main()
