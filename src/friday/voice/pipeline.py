# Voice - Main Pipeline Orchestrator
# Complete voice pipeline: Wake → VAD → Record → STT → LLM → TTS → Play

"""
FRIDAY Voice Pipeline - Production Ready

Architecture:
1. Audio Stream (16kHz mono) → WebRTC VAD
2. OpenWakeWord → Wake word detection ("friday")
3. VAD → Speech recording until silence
4. faster-whisper (tiny.en, int8) → Transcript
5. LLM callback → Response text
6. Piper (en_US-amy-low) → Audio
7. sounddevice → Playback

Target latency: < 350ms round-trip on Ryzen 5500U
"""

import asyncio
import logging
import threading
import time
import queue
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from src.friday.voice.config import config
from src.friday.voice.audio_stream import streamer
from src.friday.voice.wake_word import wake_detector
from src.friday.voice.stt import stt
from src.friday.voice.tts import tts_engine
from src.friday.events import fire_event, Events
from src.friday.memory import log_voice_interaction

logger = logging.getLogger("friday.voice.pipeline")


class PipelineState(Enum):
    IDLE = "idle"
    LISTENING_WAKE = "listening_wake"
    RECORDING_SPEECH = "recording_speech"
    PROCESSING_STT = "processing_stt"
    GENERATING_RESPONSE = "generating_response"
    SYNTHESIZING_TTS = "synthesizing_tts"
    PLAYING_TTS = "playing_tts"
    ERROR = "error"


@dataclass
class VoiceInteraction:
    """Complete record of a voice interaction."""
    interaction_id: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    wake_timestamp: float = 0
    transcript: str = ""
    response: str = ""
    total_latency_ms: float = 0
    stt_latency_ms: float = 0
    tts_latency_ms: float = 0
    llm_latency_ms: float = 0
    audio_duration_sec: float = 0
    confidence: float = 0
    wake_word: str = "friday"
    is_successful: bool = True
    error: str = ""


class VoicePipeline:
    """
    Complete voice pipeline orchestrator.

    Manages state transitions, coordinates components,
    and provides callback hooks for external systems.
    """

    def __init__(self):
        self.state = PipelineState.IDLE
        self._is_running = False
        self._stop_event = threading.Event()
        self._pipeline_thread = None

        # Audio buffering
        self._speech_buffer = bytearray()
        self._recording = False
        self._silence_frames = 0
        self._speech_frames = 0
        self._vad_warmed = False  # Wait for VAD to stabilize

        # Callbacks
        self._llm_callback: Optional[Callable[[str], str]] = None
        self._on_state_change: Optional[Callable[[str, str], None]] = None
        self._on_wake: Optional[Callable] = None
        self._on_transcript: Optional[Callable[[str], None]] = None
        self._on_response: Optional[Callable[[str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

        # Stats
        self.interactions = 0
        self.total_latency = 0.0
        self._current_interaction: Optional[VoiceInteraction] = None

        # Event loop for async operations
        self._async_loop = None

    def set_llm_callback(self, callback: Callable[[str], str]):
        """Set the LLM callback for response generation."""
        self._llm_callback = callback
        logger.info("🧠 LLM callback registered")

    def set_callbacks(self, **callbacks):
        """Set multiple callbacks at once."""
        for key, value in callbacks.items():
            if hasattr(self, f"_{key}"):
                setattr(self, f"_{key}", value)

    def _change_state(self, new_state: PipelineState):
        """Change pipeline state and notify."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.info(f"🔄 Pipeline: {old_state.value} → {new_state.value}")
            if self._on_state_change:
                try:
                    self._on_state_change(old_state.value, new_state.value)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")
            asyncio.run_coroutine_threadsafe(
                fire_event("pipeline_state_change", {"old": old_state.value, "new": new_state.value}),
                self._async_loop
            ) if self._async_loop else None

    def _on_audio_received(self, audio_data):
        """Handle incoming audio from streamer."""
        if self.state == PipelineState.LISTENING_WAKE:
            # Check for wake word
            if wake_detector.detect(audio_data.tobytes()):
                self._handle_wake_detected()

        elif self.state == PipelineState.RECORDING_SPEECH:
            # Buffer speech audio
            self._speech_buffer.extend(audio_data.tobytes())
            self._speech_frames += 1

            # Check for silence (end of speech)
            energy = self._calculate_energy(audio_data)
            if energy < config.VAD_THRESHOLD:
                self._silence_frames += 1
                if self._silence_frames >= config.SILENCE_FRAMES_END and self._speech_frames > config.MIN_SPEECH_FRAMES:
                    self._end_speech_recording()
            else:
                self._silence_frames = 0
                self._vad_warmed = True

    def _calculate_energy(self, audio_data) -> float:
        """Calculate RMS energy of audio frame."""
        import numpy as np
        if len(audio_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio_data.astype(float) ** 2)))

    def _handle_wake_detected(self):
        """Handle wake word detection."""
        logger.info("🔥 WAKE WORD DETECTED!")
        self._change_state(PipelineState.RECORDING_SPEECH)
        self._recording = True
        self._speech_buffer.clear()
        self._speech_frames = 0
        self._silence_frames = 0
        self._vad_warmed = False
        self._current_interaction = VoiceInteraction(
            wake_timestamp=time.time(),
            wake_word=config.WAKE_WORD
        )

        if self._on_wake:
            try:
                self._on_wake()
            except Exception as e:
                logger.error(f"Wake callback error: {e}")

        asyncio.run_coroutine_threadsafe(
            fire_event(Events.WAKE_DETECTED, {"timestamp": time.time(), "word": config.WAKE_WORD}),
            self._async_loop
        ) if self._async_loop else None

    def _end_speech_recording(self):
        """End speech recording and start STT."""
        if len(self._speech_buffer) < config.MIN_SPEECH_BYTES:
            logger.warning("Speech too short, ignoring")
            self._change_state(PipelineState.LISTENING_WAKE)
            return

        logger.info(f"📝 Speech recorded ({len(self._speech_buffer)} bytes), starting STT...")
        self._change_state(PipelineState.PROCESSING_STT)
        self._recording = False

        # Process in background thread
        threading.Thread(target=self._process_stt, daemon=True).start()

    def _process_stt(self):
        """Process speech-to-text."""
        start = time.perf_counter()
        audio_bytes = bytes(self._speech_buffer)
        self._speech_buffer.clear()

        # Transcribe
        result = stt.transcribe(audio_bytes)
        stt_latency = (time.perf_counter() - start) * 1000

        transcript = result.get("text", "").strip()

        if self._current_interaction:
            self._current_interaction.transcript = transcript
            self._current_interaction.stt_latency_ms = stt_latency
            self._current_interaction.audio_duration_sec = result.get("audio_duration_sec", 0)
            self._current_interaction.confidence = 1.0 - result.get("no_speech_prob", 1.0)

        if not transcript:
            logger.warning("Empty transcript, returning to wake listening")
            self._change_state(PipelineState.LISTENING_WAKE)
            self._current_interaction = None
            return

        logger.info(f"📝 Transcript: '{transcript}' ({stt_latency:.0f}ms)")

        if self._on_transcript:
            try:
                self._on_transcript(transcript)
            except Exception as e:
                logger.error(f"Transcript callback error: {e}")

        asyncio.run_coroutine_threadsafe(
            fire_event(Events.TRANSCRIPT_RECEIVED, {"text": transcript, "latency_ms": stt_latency}),
            self._async_loop
        ) if self._async_loop else None

        # Generate response
        self._generate_response(transcript, stt_latency)

    def _generate_response(self, transcript: str, stt_latency: float):
        """Generate LLM response and synthesize TTS."""
        self._change_state(PipelineState.GENERATING_RESPONSE)

        llm_start = time.perf_counter()

        if self._llm_callback:
            try:
                response = self._llm_callback(transcript)
            except Exception as e:
                logger.error(f"LLM callback error: {e}")
                response = "I'm having trouble thinking right now."
        else:
            # Fallback: simple echo
            response = f"You said: {transcript}"

        llm_latency = (time.perf_counter() - llm_start) * 1000

        if self._current_interaction:
            self._current_interaction.response = response
            self._current_interaction.llm_latency_ms = llm_latency

        logger.info(f"💬 Response: '{response}' ({llm_latency:.0f}ms)")

        if self._on_response:
            try:
                self._on_response(response)
            except Exception as e:
                logger.error(f"Response callback error: {e}")

        asyncio.run_coroutine_threadsafe(
            fire_event(Events.RESPONSE_GENERATED, {"text": response, "latency_ms": llm_latency}),
            self._async_loop
        ) if self._async_loop else None

        # Synthesize and play TTS
        self._synthesize_and_play(response, stt_latency, llm_latency)

    def _synthesize_and_play(self, response: str, stt_latency: float, llm_latency: float):
        """Synthesize TTS and play audio."""
        self._change_state(PipelineState.SYNTHESIZING_TTS)

        tts_start = time.perf_counter()

        try:
            # Synthesize
            audio = tts_engine.synthesize(response)
            tts_latency = (time.perf_counter() - tts_start) * 1000

            if audio is None:
                logger.error("TTS synthesis failed")
                self._change_state(PipelineState.ERROR)
                return

            if self._current_interaction:
                self._current_interaction.tts_latency_ms = tts_latency

            logger.info(f"🔊 TTS synthesized ({tts_latency:.0f}ms), playing...")

            # Play audio
            self._change_state(PipelineState.PLAYING_TTS)

            asyncio.run_coroutine_threadsafe(
                fire_event(Events.TTS_STARTED, {"latency_ms": tts_latency}),
                self._async_loop
            ) if self._async_loop else None

            # Play synchronously
            import sounddevice as sd
            sd.play(audio, tts_engine.sample_rate)
            sd.wait()

            if self._current_interaction:
                total_latency = stt_latency + llm_latency + tts_latency
                self._current_interaction.total_latency_ms = total_latency

                # Log to memory
                log_voice_interaction(
                    transcript=self._current_interaction.transcript,
                    response=self._current_interaction.response,
                    wake_timestamp=self._current_interaction.wake_timestamp,
                    total_latency_ms=self._current_interaction.total_latency_ms,
                    stt_latency_ms=self._current_interaction.stt_latency_ms,
                    tts_latency_ms=self._current_interaction.tts_latency_ms,
                    llm_latency_ms=self._current_interaction.llm_latency_ms,
                    audio_duration_sec=self._current_interaction.audio_duration_sec,
                    confidence=self._current_interaction.confidence,
                    wake_word=self._current_interaction.wake_word,
                    is_successful=True
                )

                self.interactions += 1
                self.total_latency += total_latency

                logger.info(f"✅ Interaction complete: {total_latency:.0f}ms total "
                          f"(STT: {stt_latency:.0f}, LLM: {llm_latency:.0f}, TTS: {tts_latency:.0f})")

                asyncio.run_coroutine_threadsafe(
                    fire_event(Events.TTS_ENDED, {
                        "total_latency_ms": total_latency,
                        "stt_ms": stt_latency,
                        "llm_ms": llm_latency,
                        "tts_ms": tts_latency
                    }),
                    self._async_loop
                ) if self._async_loop else None

                self._current_interaction = None

        except Exception as e:
            logger.error(f"❌ TTS/Playback error: {e}")
            if self._current_interaction:
                self._current_interaction.is_successful = False
                self._current_interaction.error = str(e)
            self._change_state(PipelineState.ERROR)

        # Return to listening
        self._change_state(PipelineState.LISTENING_WAKE)

    def start(self) -> bool:
        """Start the voice pipeline."""
        if self._is_running:
            return True

        logger.info("🚀 Starting FRIDAY Voice Pipeline...")

        # Initialize components
        if not stt.is_loaded():
            if not stt.load():
                logger.error("Failed to load STT model")
                return False

        if not tts_engine.is_loaded():
            if not tts_engine.load():
                logger.error("Failed to load TTS model")
                return False

        # Wake word detector should be ready
        if not wake_detector._model:
            logger.warning("Wake word model not loaded, detection may not work")

        # Get event loop for async operations
        try:
            self._async_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, we'll create one if needed
            pass

        # Set up audio streamer callbacks
        streamer.set_audio_callback(self._on_audio_received)

        # Start audio streaming
        if not streamer.start_streaming():
            logger.error("Failed to start audio streaming")
            return False

        # Start wake word detector
        wake_detector.start()

        # Start TTS playback loop
        tts_engine.start_background_playback()

        self._is_running = True
        self._change_state(PipelineState.LISTENING_WAKE)

        logger.info("✅ Voice Pipeline RUNNING - Say 'Friday' to activate")
        return True

    def stop(self):
        """Stop the voice pipeline."""
        logger.info("🛑 Stopping Voice Pipeline...")

        self._is_running = False
        self._stop_event.set()

        streamer.stop_streaming()
        wake_detector.stop()
        tts_engine.stop_background_playback()

        stt.unload()
        tts_engine.unload()

        logger.info("✅ Voice Pipeline stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        avg_latency = self.total_latency / max(1, self.interactions)
        return {
            "state": self.state.value,
            "is_running": self._is_running,
            "interactions": self.interactions,
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency,
            "stt_loaded": stt.is_loaded(),
            "tts_loaded": tts_engine.is_loaded(),
            "wake_word_ready": getattr(wake_detector, '_model', None) is not None,
            "audio_streaming": streamer.is_running if hasattr(streamer, 'is_running') else True
        }


# Global pipeline instance
pipeline = VoicePipeline()


# Convenience functions
def start_voice_pipeline(llm_callback: Optional[Callable] = None) -> bool:
    """Start the voice pipeline with optional LLM callback."""
    if llm_callback:
        pipeline.set_llm_callback(llm_callback)
    return pipeline.start()

def stop_voice_pipeline():
    """Stop the voice pipeline."""
    pipeline.stop()

def get_pipeline_stats() -> Dict[str, Any]:
    """Get pipeline statistics."""
    return pipeline.get_stats()