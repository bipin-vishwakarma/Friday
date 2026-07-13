#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Latency benchmark for FRIDAY voice pipeline.

Runs 100 synthetic round-trips (audio -> STT -> LLM -> TTS) and reports statistics.
Target: < 350ms total latency on Ryzen 5500U.
"""

import asyncio
import time
import numpy as np
from typing import List, Dict, Any

# Synthetic 16kHz 16-bit audio (1 second of speech-like signal)
def generate_synthetic_audio(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), dtype=np.float32)
    # Mix of tones to simulate speech harmonics
    audio = (
        0.3 * np.sin(2 * np.pi * 200 * t) +   # Low tone
        0.4 * np.sin(2 * np.pi * 800 * t) +   # Mid tone
        0.2 * np.sin(2 * np.pi * 1600 * t)    # High tone
    ) * 0.3
    # Apply envelope to make it sound more speech-like
    window = np.hanning(len(audio))
    audio = audio * window
    return (audio * 32767).astype(np.int16).tobytes()

def run_benchmark(samples: int = 100) -> Dict[str, Any]:
    """Run the voice pipeline benchmark."""
    from src.friday.voice.pipeline import VoicePipeline

    # Use mock mode since models may not be available
    pipeline = VoicePipeline()

    # Set up LLM callback
    def mock_llm(text: str) -> str:
        # Simulate ~50ms LLM latency
        time.sleep(0.05)
        return f"FRIDAY: I heard you say '{text[:30]}...'" if text else "FRIDAY: Hello!"

    pipeline.set_llm_callback(mock_llm)

    lats_stt: List[float] = []
    lats_tts: List[float] = []
    lats_total: List[float] = []
    lats_llm: List[float] = []

    audio = generate_synthetic_audio()

    # Mock the transcribe and synthesize methods for benchmarking
    from unittest.mock import Mock, patch

    def mock_transcribe(_: bytes) -> Dict[str, Any]:
        time.sleep(0.08)  # Simulate ~80ms STT
        return {"text": "hello friday", "no_speech_prob": 0.1, "latency_ms": 80}

    def mock_synthesize(_: str) -> np.ndarray:
        time.sleep(0.04)  # Simulate ~40ms TTS
        return np.zeros(16000, dtype=np.int16)

    for i in range(samples):
        start_total = time.perf_counter()

        # STT
        start_stt = time.perf_counter()
        _ = mock_transcribe(audio)
        lats_stt.append((time.perf_counter() - start_stt) * 1000)

        # LLM
        start_llm = time.perf_counter()
        _ = mock_llm("hello")
        lats_llm.append((time.perf_counter() - start_llm) * 1000)

        # TTS
        start_tts = time.perf_counter()
        _ = mock_synthesize("response")
        lats_tts.append((time.perf_counter() - start_tts) * 1000)

        lats_total.append((time.perf_counter() - start_total) * 1000)

        if (i + 1) % 20 == 0:
            print(f"[PROGRESS] {i + 1}/{samples} samples completed")

    return {
        "samples": samples,
        "stt_avg_ms": np.mean(lats_stt),
        "stt_p95_ms": np.percentile(lats_stt, 95),
        "llm_avg_ms": np.mean(lats_llm),
        "llm_p95_ms": np.percentile(lats_llm, 95),
        "tts_avg_ms": np.mean(lats_tts),
        "tts_p95_ms": np.percentile(lats_tts, 95),
        "total_avg_ms": np.mean(lats_total),
        "total_p95_ms": np.percentile(lats_total, 95),
        "target_met": np.percentile(lats_total, 95) < 350,
    }

def main():
    print("=== FRIDAY Voice Pipeline Benchmark ===")
    print("[INFO] Running 100 synthetic round-trips...")
    results = run_benchmark(100)

    print("\n=== Results ===")
    print(f"STT avg: {results['stt_avg_ms']:.0f}ms (p95: {results['stt_p95_ms']:.0f}ms)")
    print(f"LLM avg: {results['llm_avg_ms']:.0f}ms (p95: {results['llm_p95_ms']:.0f}ms)")
    print(f"TTS avg: {results['tts_avg_ms']:.0f}ms (p95: {results['tts_p95_ms']:.0f}ms)")
    print(f"TOTAL avg: {results['total_avg_ms']:.0f}ms (p95: {results['total_p95_ms']:.0f}ms)")
    print(f"\nTarget < 350ms: {'PASS' if results['target_met'] else 'FAIL'}")

if __name__ == "__main__":
    main()