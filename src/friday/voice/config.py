"""
Voice Pipeline Configuration

Lightweight config module — no heavy imports at module load so that
importing this module never fails due to missing optional dependencies.
"""

from pathlib import Path
from typing import Callable, Optional

logger = None  # set lazily to avoid circular import

# --------------------------
# Audio settings
# --------------------------
SAMPLERATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 30  # VAD frame size (ms)

# VAD / energy thresholds (used by audio_stream.py + pipeline.py)
VAD_THRESHOLD = 0.01          # RMS energy below this = silence
MIN_SPEECH_THRESHOLD = 0.02   # RMS energy above this = speech
SILENCE_FRAMES_END = 15       # ~0.45s of silence ends a recording
MIN_SPEECH_FRAMES = 10        # minimum frames of speech before accepting
MIN_SPEECH_BYTES = 3200       # ~0.1s of 16kHz int16 audio minimum

# --------------------------
# STT settings
# --------------------------
WHISPER_MODEL_SIZE = "tiny.en"  # Small model for low latency on CPU
BEAM_SEARCH_WIDTH = 1           # greedy = fastest (pipeline uses 1; config default shown)

# --------------------------
# Wake word settings
# --------------------------
WAKEWORD = "friday"
WAKEWORD_CONFIDENCE = 0.6
WAKEWORD_MODEL = "tiny_en_v1.onnx"

# --------------------------
# Streaming settings
# --------------------------
MAX_BUFFERED_FRAMES = 10
MIN_SPEECH_DURATION = 0.5      # Minimum speech duration to process (s)
MAX_SPEECH_DURATION = 15.0     # Maximum speech duration before truncation (s)

# --------------------------
# Event callbacks (optional hooks)
# --------------------------
on_wake_word: Optional[Callable] = None
on_speech_start: Optional[Callable] = None
on_speech_end: Optional[Callable] = None
on_transcript: Optional[Callable] = None
on_tts_play: Optional[Callable] = None


class VoiceConfig:
    """Backwards-compatible config object exposing the module-level constants."""

    SAMPLERATE = SAMPLERATE
    CHANNELS = CHANNELS
    FRAME_DURATION_MS = FRAME_DURATION_MS
    VAD_THRESHOLD = VAD_THRESHOLD
    MIN_SPEECH_THRESHOLD = MIN_SPEECH_THRESHOLD
    SILENCE_FRAMES_END = SILENCE_FRAMES_END
    MIN_SPEECH_FRAMES = MIN_SPEECH_FRAMES
    MIN_SPEECH_BYTES = MIN_SPEECH_BYTES
    WHISPER_MODEL_SIZE = WHISPER_MODEL_SIZE
    BEAM_SEARCH_WIDTH = BEAM_SEARCH_WIDTH
    WAKEWORD = WAKEWORD
    WAKEWORD_CONFIDENCE = WAKEWORD_CONFIDENCE
    WAKEWORD_MODEL = WAKEWORD_MODEL
    MAX_BUFFERED_FRAMES = MAX_BUFFERED_FRAMES
    MIN_SPEECH_DURATION = MIN_SPEECH_DURATION
    MAX_SPEECH_DURATION = MAX_SPEECH_DURATION
    on_wake_word = on_wake_word
    on_speech_start = on_speech_start
    on_speech_end = on_speech_end
    on_transcript = on_transcript
    on_tts_play = on_tts_play


# Module-level singleton used across the voice package
config = VoiceConfig()
