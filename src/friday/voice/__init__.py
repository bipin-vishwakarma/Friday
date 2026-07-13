"""
FRIDAY Voice Package

Exports main voice processing components.
"""

from src.friday.voice.config import config, VoiceConfig
from src.friday.voice.audio_stream import streamer, AudioStreamer
from src.friday.voice.wake_word import wake_detector, OpenWakeWordDetector
from src.friday.voice.stt import stt, WhisperSTT, transcribe_audio
from src.friday.voice.tts import tts_engine, PiperTTS, speak_text, speak_text_sync
from src.friday.voice.pipeline import pipeline, VoicePipeline, start_voice_pipeline, stop_voice_pipeline

__all__ = [
    "config",
    "VoiceConfig",
    "streamer",
    "AudioStreamer",
    "wake_detector",
    "OpenWakeWordDetector",
    "stt",
    "WhisperSTT",
    "transcribe_audio",
    "tts_engine",
    "PiperTTS",
    "speak_text",
    "speak_text_sync",
    "pipeline",
    "VoicePipeline",
    "start_voice_pipeline",
    "stop_voice_pipeline",
]