"""
Audio streaming for FRIDAY voice pipeline.

Manages microphone capture via sounddevice, VAD-based speech/silence
detection, and an audio queue consumed by the wake-word detector and
the voice pipeline.
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from .config import config

logger = logging.getLogger("friday.voice.audio_stream")


class AudioStreamer:
    """Real-time microphone capture with VAD and a shared audio queue."""

    def __init__(self, device_index: Optional[int] = None):
        self.device_index = device_index
        self.stream = None
        self.audio_queue: "queue.Queue" = queue.Queue(maxsize=100)
        self.is_running = False
        self.current_device = None

        # Event callbacks
        self._on_audio_received: Optional[Callable] = None
        self._on_voice_start: Optional[Callable] = None
        self._on_voice_end: Optional[Callable] = None
        self._on_buffer_overflow: Optional[Callable] = None

        # VAD state
        self._silence_detected = True
        self._frames_silent = 0
        self._frames_speech = 0

        # Statistics
        self.samples_processed = 0
        self.dropped_samples = 0

    def set_audio_callback(self, callback: Callable):
        self._on_audio_received = callback

    def set_voice_start_callback(self, callback: Callable):
        self._on_voice_start = callback

    def set_voice_end_callback(self, callback: Callable):
        self._on_voice_end = callback

    def set_buffer_overflow_callback(self, callback: Callable):
        self._on_buffer_overflow = callback

    def start_streaming(self, device_index: Optional[int] = None) -> bool:
        """Start capturing audio from the microphone."""
        try:
            devices = sd.query_devices()
            logger.info("Available audio devices: %d", len(devices))

            if device_index is not None and 0 <= device_index < len(devices):
                self.device_index = device_index

            samplerate = config.SAMPLERATE
            channels = config.CHANNELS
            blocksize = int(samplerate * config.FRAME_DURATION_MS / 1000)

            self.stream = sd.InputStream(
                samplerate=samplerate,
                channels=channels,
                dtype="int16",
                blocksize=blocksize,
                device=self.device_index,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.is_running = True

            idx = self.device_index if self.device_index is not None else 0
            self.current_device = devices[idx]["name"]
            logger.info("✅ Audio streaming started on device: %s", self.current_device)
            return True

        except Exception as e:
            logger.error("❌ Failed to start audio streaming: %s", e)
            self.is_running = False
            return False

    def stop_streaming(self):
        """Stop capturing and release the audio device."""
        if self.stream and self.is_running:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error("Error while stopping audio stream: %s", e)
            self.stream = None
            self.is_running = False
            logger.info("🛑 Audio streaming stopped")

    def _audio_callback(self, indata, frames, callback_time, status):
        """sounddevice callback — runs on the audio thread. Must not block."""
        if status:
            logger.warning("Audio status: %s", status)

        # Mono int16 -> float for processing
        audio_data = indata.squeeze().astype(np.int16)

        # Backpressure: drop oldest frames if the queue is nearly full
        if self.audio_queue.qsize() >= self.audio_queue.maxsize - 5:
            for _ in range(5):
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            if self._on_buffer_overflow:
                try:
                    self._on_buffer_overflow()
                except Exception:
                    pass

        try:
            self.audio_queue.put_nowait(
                {
                    "data": audio_data,
                    "timestamp": time.time(),
                    "frames": frames,
                    "device": self.current_device,
                }
            )
        except queue.Full:
            self.dropped_samples += 1

        self.samples_processed += 1

        # Lightweight energy-based VAD
        energy = float(np.sqrt(np.mean(audio_data.astype(float) ** 2)))
        if energy > config.MIN_SPEECH_THRESHOLD:
            if self._silence_detected and self._frames_silent > 10:
                if self._on_voice_start:
                    try:
                        self._on_voice_start()
                    except Exception:
                        pass
                self._silence_detected = False
                self._frames_speech = 0
            self._frames_speech += 1
            if self._frames_speech > 20:
                self._silence_detected = False
        else:
            if not self._silence_detected:
                if self._on_voice_end:
                    try:
                        self._on_voice_end()
                    except Exception:
                        pass
                self._silence_detected = True
                self._frames_speech = 0
                self._frames_silent = 0
            self._frames_silent += 1

        # Forward raw frame to the pipeline
        if self._on_audio_received:
            try:
                self._on_audio_received(audio_data)
            except Exception as e:
                logger.error("Audio callback handler error: %s", e)

    def get_audio_queue(self) -> "queue.Queue":
        return self.audio_queue

    def get_statistics(self) -> dict:
        return {
            "is_running": self.is_running,
            "device": self.current_device,
            "samples_processed": self.samples_processed,
            "dropped_samples": self.dropped_samples,
            "queue_size": self.audio_queue.qsize(),
            "max_queue_size": self.audio_queue.maxsize,
        }


# Global audio streamer instance
streamer = AudioStreamer()


def setup_voice_callbacks(
    on_audio: Optional[Callable] = None,
    on_wake: Optional[Callable] = None,
    on_speech: Optional[Callable] = None,
):
    """Configure voice callbacks in one call."""
    if on_audio:
        streamer.set_audio_callback(on_audio)
    if on_wake:
        streamer.set_voice_start_callback(on_wake)
    if on_speech:
        streamer.set_voice_end_callback(on_speech)
    logger.info("🎙️ Voice callbacks configured")
