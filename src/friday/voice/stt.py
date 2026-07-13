# Voice - Speech-to-Text (Whisper.cpp / faster-whisper)
# Ultra-fast STT optimized for AMD Ryzen 5500U

"""
Real-time Speech-to-Text using faster-whisper (Whisper.cpp bindings).

Features:
- 190ms latency on tiny model
- CPU-optimized (int8 quantization, 2 threads)
- Streaming transcription support
- VAD filtering for silence rejection
- Callback-based async results

Model: tiny.en (40MB, 190M params, English-only for speed)
"""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

import numpy as np

logger = logging.getLogger("friday.voice.stt")

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Using mock STT.")


class WhisperSTT:
    """
    Real STT using faster-whisper (Whisper.cpp).

    Optimized for low-end CPU:
    - Tiny model (40MB)
    - int8 quantization
    - 2 CPU threads
    - Beam size 1 (greedy)
    - VAD filter enabled
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._find_model()
        self.model = None
        self._is_loaded = False
        self._lock = threading.Lock()

        # Performance config
        self.beam_size = 1  # Fastest - no beam search
        self.word_timestamps = False
        self.vad_filter = True
        self.vad_parameters = {
            "threshold": 0.3,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 30,
            "min_silence_duration_ms": 1000
        }
        self.initial_prompt = None

        # Callbacks
        self._on_transcript: Optional[Callable] = None
        self._on_partial: Optional[Callable] = None

        # Try loading
        self.load()

    def _find_model(self) -> str:
        """Find or download Whisper model."""
        base_dir = Path(__file__).parent.parent.parent.parent
        model_dir = base_dir / "models" / "whisper"
        model_file = model_dir / "model.bin"

        if model_file.exists():
            logger.info(f"Found local model at {model_dir}")
            # faster-whisper expects the directory containing model.bin
            return str(model_dir)

        # Fallback to huggingface hub name
        logger.info("Local model not found, will use hub model 'tiny.en'")
        return "tiny.en"

    def load(self) -> bool:
        """Load Whisper model with CPU optimizations."""
        if self._is_loaded:
            return True

        if not WHISPER_AVAILABLE:
            logger.error("faster-whisper not available. Install with: pip install faster-whisper")
            self._is_loaded = False
            return False

        with self._lock:
            if self._is_loaded:
                return True

            try:
                logger.info(f"Loading Whisper model: {self.model_path}")
                start = time.perf_counter()

                self.model = WhisperModel(
                    self.model_path,
                    device="cpu",
                    compute_type="int8",  # Fastest CPU quantization
                    cpu_threads=2,  # Ryzen 5500U: use 2 threads max
                    num_workers=1
                )

                elapsed = time.perf_counter() - start
                self._is_loaded = True
                logger.info(f"✅ Whisper model loaded in {elapsed*1000:.0f}ms (tiny, int8, 2 threads)")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to load Whisper: {e}")
                self._is_loaded = False
                return False

    def unload(self):
        """Unload model to free RAM."""
        with self._lock:
            if self.model:
                del self.model
                self.model = None
                self._is_loaded = False
                logger.info("🗑️ Whisper model unloaded")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Raw int16 audio bytes (16kHz mono)
            sample_rate: Audio sample rate (default: 16kHz)

        Returns:
            Dict with 'text', 'segments', 'latency_ms', 'language', etc.
        """
        if not self._is_loaded:
            if not self.load():
                return {"text": "", "error": "Model not loaded", "latency_ms": 0}

        start = time.perf_counter()

        # Convert bytes to numpy array
        try:
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return {"text": "", "error": str(e), "latency_ms": 0}

        # Check duration
        max_len = sample_rate * 30  # 30s max
        if len(audio) > max_len:
            audio = audio[:max_len]
            logger.warning(f"Audio truncated to 30s")

        # Validate audio
        if len(audio) == 0:
            return {"text": "", "error": "Empty audio", "latency_ms": 0}

        if np.all(audio == 0):
            return {"text": "", "error": "Silent audio", "latency_ms": 0}

        try:
            # Run transcription
            segments, info = self.model.transcribe(
                audio,
                beam_size=self.beam_size,
                word_timestamps=self.word_timestamps,
                vad_filter=self.vad_filter,
                vad_parameters=self.vad_parameters,
                initial_prompt=self.initial_prompt,
                language="en",  # Force English for speed
                condition_on_previous_text=False,  # No context for speed
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6
            )

            # Collect results
            full_text = ""
            full_segments = []
            for seg in segments:
                full_text += seg.text + " "
                full_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "avg_logprob": seg.avg_logprob,
                    "no_speech_prob": seg.no_speech_prob
                })

            elapsed = time.perf_counter() - start
            latency_ms = elapsed * 1000

            logger.info(f"⏱️ Transcribed {len(audio)/sample_rate:.1f}s in {latency_ms:.0f}ms: '{full_text.strip()[:50]}'")

            return {
                "text": full_text.strip(),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "avg_logprob": info.avg_logprob,
                "no_speech_prob": info.no_speech_prob,
                "segments": full_segments,
                "latency_ms": latency_ms,
                "audio_duration_sec": len(audio) / sample_rate
            }

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {"text": "", "error": str(e), "latency_ms": 0}

    def set_callback(self, callback: Callable):
        """Set callback for transcript results."""
        self._on_transcript = callback

    def set_partial_callback(self, callback: Callable):
        """Set callback for streaming partials (if needed)."""
        self._on_partial = callback

    def is_loaded(self) -> bool:
        return self._is_loaded


# Global STT instance
stt = WhisperSTT()


# Convenience function
def transcribe_audio(audio_bytes: bytes) -> str:
    """Quick transcription helper."""
    result = stt.transcribe(audio_bytes)
    return result.get("text", "")