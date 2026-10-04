import os

import paths

_MODELS_DIR = paths.MODELS_DIR

# Path for custom Indian English model (CTranslate2 converted, see models/setup_models.py)
INDIAN_ENGLISH_MODEL_PATH = os.path.join(_MODELS_DIR, 'indian-accent-english-whisper')

# Hindi fine-tuned models per size (CTranslate2 converted, see models/setup_models.py).
# Fallback is the stock multilingual model faster-whisper downloads on demand.
HINGLISH_MODELS = {
    'small': (os.path.join(_MODELS_DIR, 'whisper-hindi-small'), 'small'),
    'medium': (os.path.join(_MODELS_DIR, 'whisper-hindi-medium'), 'medium'),
    'large': (os.path.join(_MODELS_DIR, 'whisper-hindi-large-v2'), 'large-v2'),
}

# Oriserve Hindi2Hinglish family (CTranslate2 converted, see models/setup_models.py). These
# models output roman-letter Hinglish text directly from Hindi speech, with no translation step.
HINGLISH_ROMAN_MODELS = {
    'small': (os.path.join(_MODELS_DIR, 'whisper-hindi2hinglish-apex'), 'small'),
    'medium': (os.path.join(_MODELS_DIR, 'whisper-hindi2hinglish-apex'), 'medium'),
    'large': (os.path.join(_MODELS_DIR, 'whisper-hindi2hinglish-prime'), 'large-v2'),
}

# Hindi->English text translator (opus-mt-hi-en, CTranslate2). The vasista22 models are
# fine-tuned for Hindi transcription and ignore task='translate', so English output needs
# this second step.
TRANSLATOR_PATH = os.path.join(_MODELS_DIR, 'opus-mt-hi-en')
_translator = None


def _translate_hi_to_en(text):
    """Translate Hindi text to English. Returns text unchanged if the model is missing."""
    global _translator

    if not text.strip():
        return text

    if _translator is None:
        if not os.path.exists(TRANSLATOR_PATH):
            print(f'Translation model not found at {TRANSLATOR_PATH}')
            print('Run models/setup_models.py translator to install it. Returning Hindi text.')
            return text

        import ctranslate2
        import sentencepiece as spm

        try:
            device = 'cuda' if ctranslate2.get_supported_compute_types('cuda') else 'cpu'
        except Exception:
            device = 'cpu'

        _translator = (
            ctranslate2.Translator(
                TRANSLATOR_PATH,
                device=device,
                compute_type='int8_float16' if device == 'cuda' else 'int8',
            ),
            spm.SentencePieceProcessor(os.path.join(TRANSLATOR_PATH, 'source.spm')),
            spm.SentencePieceProcessor(os.path.join(TRANSLATOR_PATH, 'target.spm')),
        )

    translator, source_sp, target_sp = _translator
    tokens = source_sp.encode(text, out_type=str) + ['</s>']
    result = translator.translate_batch([tokens])
    return target_sp.decode(result[0].hypotheses[0])


def _missing(local_path, fallback, hint):
    """A configured local model is not on disk: say so, then fall back (source) or stop (installed)."""
    if paths.FROZEN:
        # The installed app runs offline, so downloading the stock model would just hang/fail.
        raise RuntimeError(
            f'The speech model for this setting is not installed ({os.path.basename(local_path)}).\n'
            'Run the WhisperWriter setup again and tick it under Components, '
            'or pick another Language Mode / Model Quality in Settings.')
    print(f'Model not found at {local_path}')
    print(f'Falling back to {fallback}. {hint}')
    return fallback


def get_model_name(model_quality, language_mode):
    """
    Get the Whisper model based on quality setting and language mode.

    Args:
        model_quality: 'small', 'medium', or 'large' (hinglish mode only)
        language_mode: 'indian_english' or 'hinglish'

    Returns:
        Model name string or path to custom model
    """
    if language_mode == 'hinglish_roman':
        local_path, fallback = HINGLISH_ROMAN_MODELS.get(model_quality, HINGLISH_ROMAN_MODELS['medium'])
        if os.path.exists(local_path):
            return local_path
        return _missing(local_path, fallback, 'Run python models/setup_models.py hinglish-roman to install the fine-tuned model.')

    if language_mode == 'hinglish':
        local_path, fallback = HINGLISH_MODELS.get(model_quality, HINGLISH_MODELS['medium'])
        if os.path.exists(local_path):
            return local_path
        return _missing(local_path, fallback, 'Run python models/setup_models.py hinglish-small (or -medium/-large) to install it.')

    # indian_english: single fixed fine-tuned model, model_quality does not apply
    if os.path.exists(INDIAN_ENGLISH_MODEL_PATH):
        return INDIAN_ENGLISH_MODEL_PATH
    return _missing(INDIAN_ENGLISH_MODEL_PATH, 'large-v3', 'Run python models/setup_models.py indian_english to install the fine-tuned model.')


def create_local_model(config):
    """
    Create a local model using the faster-whisper library.
    Auto-selects model based on language_mode setting.
    Uses lazy import to improve startup time.
    """
    from faster_whisper import WhisperModel
    import ctranslate2

    print('Creating local model...') if config['misc']['print_to_terminal'] else ''
    model_options = config['model_options']

    # Select model based on quality and language settings
    model_quality = model_options.get('model_quality', 'medium')
    language_mode = model_options.get('language_mode', 'indian_english')
    model_name = get_model_name(model_quality, language_mode)
    print(f'Model: {model_name} (quality={model_quality}, lang={language_mode})') if config['misc']['print_to_terminal'] else ''

    # Check CUDA availability via ctranslate2 (no torch needed)
    try:
        cuda_supported = len(ctranslate2.get_supported_compute_types('cuda')) > 0
    except Exception:
        cuda_supported = False

    # CPU-compatible compute type (float16/int8_float16 only work on GPU)
    cpu_compute_type = 'int8' if model_options['compute_type'] in ('float16', 'int8_float16', 'bfloat16', 'int8_bfloat16') else model_options['compute_type']

    if cuda_supported and model_options['device'] != 'cpu':
        try:
            model = WhisperModel(
                model_name,
                device='cuda',
                compute_type=model_options['compute_type']
            )
            print('Using CUDA GPU.') if config['misc']['print_to_terminal'] else ''
        except Exception as e:
            print(f'Error initializing WhisperModel with CUDA: {e}') if config['misc']['print_to_terminal'] else ''
            print(f'Falling back to CPU with compute_type={cpu_compute_type}.') if config['misc']['print_to_terminal'] else ''
            model = WhisperModel(
                model_name,
                device='cpu',
                compute_type=cpu_compute_type
            )
    else:
        print(f'CUDA not available, using CPU with compute_type={cpu_compute_type}.') if config['misc']['print_to_terminal'] else ''
        model = WhisperModel(
            model_name,
            device='cpu',
            compute_type=cpu_compute_type
        )

    print('Local model created.') if config['misc']['print_to_terminal'] else ''
    return model


def transcribe_local(config, temp_audio_file, local_model=None):
    """
    Transcribe an audio file using a local Whisper model.
    Auto-configures language based on language_mode.
    """
    if not local_model:
        local_model = create_local_model(config)

    model_options = config['model_options']

    # Set language and task based on language_mode
    language_mode = model_options.get('language_mode', 'indian_english')
    if language_mode == 'hinglish':
        # Hindi speech -> Hindi text; translated to English in transcribe()
        language = 'hi'
        task = 'transcribe'
    elif language_mode == 'hinglish_roman':
        # Hindi speech -> roman-letter Hinglish text directly, no translation step
        language = 'en'
        task = 'transcribe'
    else:
        # Indian-accented English -> English text
        language = 'en'
        task = 'transcribe'

    response = local_model.transcribe(
        audio=temp_audio_file,
        language=language,
        task=task,
        initial_prompt=model_options['initial_prompt'],
        condition_on_previous_text=model_options['condition_on_previous_text'],
        temperature=model_options['temperature'],
        vad_filter=model_options['vad_filter'],
    )

    return ''.join([segment.text for segment in list(response[0])])


def post_process_transcription(transcription, config=None):
    """
    Apply post-processing to the transcription.
    """
    transcription = transcription.strip()
    if config:
        if config['post_processing']['remove_trailing_period'] and transcription.endswith('.'):
            transcription = transcription[:-1]
        if config['post_processing']['add_trailing_space']:
            transcription += ' '
        if config['post_processing']['remove_capitalization']:
            transcription = transcription.lower()

    print('Post-processed transcription:', transcription) if config['misc']['print_to_terminal'] else ''
    return transcription


def transcribe(config, audio_file, local_model=None):
    """
    Transcribe an audio file using a local Whisper model.
    In hinglish mode the Hindi transcription is then translated to English.
    """
    if not audio_file:
        return ''

    transcription = transcribe_local(config, audio_file, local_model)

    print('Transcription:', transcription) if config['misc']['print_to_terminal'] else ''

    if config['model_options'].get('language_mode') == 'hinglish':
        transcription = _translate_hi_to_en(transcription)
        print('Translated:', transcription) if config['misc']['print_to_terminal'] else ''

    return post_process_transcription(transcription, config)
