# Voice - Wake Word Detection with OpenWakeWord
# Full implementation with three-tier fallback:
#   1. openwakeword library (preferred, ONNX backend)
#   2. Raw onnxruntime with local .onnx file
#   3. Mock detector for testing
# CPU-optimized for AMD Ryzen 5500U

"""
Wake word detection for the FRIDAY voice pipeline.

Falls back gracefully through:
  openwakeword library -> raw onnxruntime -> mock detector

Designed for low-latency operation on consumer hardware.
"""

import logging
import time
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from src.friday.voice.config import config

logger = logging.getLogger("friday.voice.wake_word")

# ---------------------------------------------------------------------------
# Detection backend: openwakeword library
# ---------------------------------------------------------------------------

class OpenWakeWordDetector:
    """
    Wake word detector with automatic fallback:

    1. openwakeword library (Model class, ONNX backend)
    2. Raw onnxruntime with a local ONNX model file
    3. Mock detector that fires every ~30 seconds (testing only)
    """

    def __init__(self, wake_word: str = "friday", threshold: float = 0.5):
        self.wake_word = wake_word.lower()
        self.threshold = threshold
        self._model = None          # openwakeword Model or None
        self._ort_session = None    # raw onnxruntime session (fallback)
        self._backend = "none"      # "openwakeword" | "onnxruntime" | "mock"
        self._is_running = False
        self._stop_event = threading.Event()
        self.detection_thread: Optional[threading.Thread] = None

        # Mock state
        self._mock_next_fire = time.time() + 30.0

        self._init_model()

    # ------------------------------------------------------------------
    # Model initialisation (three tiers)
    # ------------------------------------------------------------------

    def _init_model(self):
        """Try each backend in order until one succeeds."""
        self._try_openwakeword()
        if self._model is not None:
            return

        self._try_onnxruntime()
        if self._ort_session is not None:
            return

        self._init_mock()

    def _try_openwakeword(self):
        """Tier 1: use the openwakeword library if available."""
        try:
            from openwakeword.model import Model as OWWModel  # type: ignore

            # Pick a pre-trained model that is available; prefer hey_jarvis
            # since it is closest to conversational assistant wake words.
            candidate_models = [
                "hey_jarvis",
                "hey_mycroft",
                "alexa",
            ]
            self._model = OWWModel(
                wakeword_models=candidate_models,
                inference_framework="onnx",
                vad_threshold=0,
            )
            self._backend = "openwakeword"
            model_names = list(self._model.models.keys())
            logger.info(
                "openwakeword loaded successfully (backend=%s, models=%s)",
                self._backend,
                model_names,
            )
        except Exception as exc:
            logger.warning("openwakeword backend unavailable: %s", exc)
            self._model = None

    def _try_onnxruntime(self):
        """Tier 2: load a local ONNX file with onnxruntime directly."""
        try:
            import onnxruntime as ort  # type: ignore
        except ImportError:
            logger.warning("onnxruntime not installed, skipping fallback")
            return

        # Search for an ONNX model in several likely locations
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        search_dirs = [
            project_root / "models" / "openwakeword",
            project_root / "models" / "wakeword",
        ]

        onnx_file: Optional[Path] = None
        for d in search_dirs:
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.onnx")):
                # Skip files that are clearly corrupt (very small = likely error page)
                if f.stat().st_size < 10_000:
                    logger.warning(
                        "Skipping tiny/corrupt model file: %s (%d bytes)",
                        f,
                        f.stat().st_size,
                    )
                    continue
                onnx_file = f
                break
            if onnx_file is not None:
                break

        # Also check the openwakeword package's own resources directory
        if onnx_file is None:
            try:
                import openwakeword as oww_pkg  # type: ignore
                oww_model_dir = (
                    Path(oww_pkg.__file__).resolve().parent / "resources" / "models"
                )
                if oww_model_dir.is_dir():
                    for f in sorted(oww_model_dir.glob("*.onnx")):
                        if f.stat().st_size > 10_000:
                            onnx_file = f
                            break
            except Exception:
                pass

        if onnx_file is None:
            logger.warning("No valid ONNX model file found")
            return

        try:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
            )
            self._ort_session = ort.InferenceSession(
                str(onnx_file), sess_options=opts, providers=["CPUExecutionProvider"]
            )
            self._backend = "onnxruntime"
            inputs = self._ort_session.get_inputs()
            outputs = self._ort_session.get_outputs()
            logger.info(
                "Loaded ONNX model from %s  (inputs=%d, outputs=%d)",
                onnx_file.name,
                len(inputs),
                len(outputs),
            )
        except Exception as exc:
            logger.warning("Failed to load ONNX model %s: %s", onnx_file, exc)
            self._ort_session = None

    def _init_mock(self):
        """Tier 3: mock detector for testing without any real model."""
        self._backend = "mock"
        self._mock_next_fire = time.time() + 30.0
        logger.info(
            "Using mock wake-word detector (fires every ~30 s for testing)"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, audio_bytes: bytes) -> bool:
        """Return True if the wake word is detected in *audio_bytes*.

        *audio_bytes* should be raw 16 kHz mono int16 PCM data.
        """
        if self._backend == "openwakeword":
            return self._detect_openwakeword(audio_bytes)
        if self._backend == "onnxruntime":
            return self._detect_onnxruntime(audio_bytes)
        return self._detect_mock()

    def start(self):
        """Start the background detection thread."""
        if self._is_running:
            return
        logger.info("Starting wake-word detection (backend=%s)", self._backend)
        self._is_running = True
        self._stop_event.clear()
        self.detection_thread = threading.Thread(
            target=self._detection_loop, daemon=True
        )
        self.detection_thread.start()

    def stop(self):
        """Stop the background detection thread."""
        self._is_running = False
        self._stop_event.set()
        if self.detection_thread is not None:
            self.detection_thread.join(timeout=1.0)
            self.detection_thread = None

    # ------------------------------------------------------------------
    # Backend-specific detection
    # ------------------------------------------------------------------

    def _detect_openwakeword(self, audio_bytes: bytes) -> bool:
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            if len(audio_np) == 0:
                return False

            # openwakeword expects 16kHz audio.  Each predict() call
            # processes one 80 ms chunk (1280 samples).  Feed whatever
            # we receive; the library handles internal buffering.
            # For very short buffers (<1280 samples) pad to 1280.
            expected = 1280
            if len(audio_np) < expected:
                padded = np.zeros(expected, dtype=np.float32)
                padded[: len(audio_np)] = audio_np
                audio_np = padded
            elif len(audio_np) > expected:
                # Process the most recent chunk
                audio_np = audio_np[-expected:]

            predictions = self._model.predict(audio_np)

            # predictions is a dict like {"hey_jarvis": 0.92}
            for name, score in predictions.items():
                if score >= self.threshold:
                    logger.info(
                        "Wake word '%s' detected (score=%.3f)", name, score
                    )
                    return True
            return False
        except Exception as exc:
            logger.error("openwakeword detection error: %s", exc)
            return False

    def _detect_onnxruntime(self, audio_bytes: bytes) -> bool:
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            if len(audio_np) == 0:
                return False

            audio_np = audio_np / 32768.0  # normalise to [-1, 1]

            # The feature extraction pipeline used by openwakeword expects
            # mel-spectrogram pre-processing.  Since we are running the
            # raw wake-word model directly we feed the normalised samples.
            # Pad / trim to expected frame size (1280 samples = 80 ms @16kHz).
            expected = 1280
            if len(audio_np) < expected:
                padded = np.zeros(expected, dtype=np.float32)
                padded[: len(audio_np)] = audio_np
                audio_np = padded
            elif len(audio_np) > expected:
                audio_np = audio_np[-expected:]

            input_name = self._ort_session.get_inputs()[0].name
            feed = {input_name: audio_np.reshape(1, -1).astype(np.float32)}
            outputs = self._ort_session.run(None, feed)

            prediction = float(outputs[0].flat[0])
            return prediction > self.threshold
        except Exception as exc:
            logger.error("onnxruntime detection error: %s", exc)
            return False

    def _detect_mock(self) -> bool:
        """Fire every ~30 seconds for testing purposes."""
        now = time.time()
        if now >= self._mock_next_fire:
            self._mock_next_fire = now + 30.0
            logger.info("[mock] Simulated wake-word detection")
            return True
        return False

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def _detection_loop(self):
        """Main processing loop consumed by the background thread."""
        logger.info("Wake-word detection loop started (backend=%s)", self._backend)
        while self._is_running and not self._stop_event.is_set():
            try:
                # Lazy import to avoid circular import at module level
                from src.friday.voice.audio_stream import streamer  # type: ignore

                try:
                    chunk = streamer.get_audio_queue().get(timeout=0.1)
                except Exception:
                    # No audio chunk available yet; for mock, still tick
                    if self._backend == "mock" and self._detect_mock():
                        self._fire_wake_event()
                    continue

                audio_data = chunk["data"]  # numpy int16 array from audio_stream

                # Convert numpy array to raw bytes for detect()
                audio_bytes = audio_data.tobytes()

                if self.detect(audio_bytes):
                    self._fire_wake_event()

            except Exception as exc:
                logger.error("Error in detection loop: %s", exc)
                if self._is_running:
                    time.sleep(0.1)

    def _fire_wake_event(self):
        """Notify listeners that the wake word was detected."""
        logger.info("WAKE WORD DETECTED!")

        # Fire the configured callback
        if config.on_wake_word is not None:
            try:
                config.on_wake_word()
            except Exception as exc:
                logger.error("Error in wake word callback: %s", exc)

        # Fire the event bus
        try:
            from src.friday.events import fire_event  # type: ignore

            fire_event(
                "wake_detected",
                {"timestamp": time.time(), "backend": self._backend},
            )
        except Exception as exc:
            logger.error("Error firing wake event: %s", exc)

        # Debounce: small pause so we don't re-fire immediately
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# Module-level singleton (imported by __init__.py)
# ---------------------------------------------------------------------------
wake_detector = OpenWakeWordDetector()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def setup_wake_word_handler(callback):
    """Set the wake-word detection callback."""
    if callback:
        config.on_wake_word = callback
        logger.info("Wake-word callback configured")


def is_wake_listening() -> bool:
    """Check whether wake-word detection is currently running."""
    return wake_detector._is_running


def stop_wake_detection():
    """Stop wake-word detection."""
    wake_detector.stop()
