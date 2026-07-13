#!/usr/bin/env python
"""Test script to verify FRIDAY voice pipeline imports and basic initialization."""

import sys
import traceback

def test_imports():
    """Test that all required modules can be imported."""
    modules_to_test = [
        ('src.friday.config.settings', 'settings'),
        ('src.friday.events', 'events'),
        ('src.friday.memory', 'memory'),
        ('src.friday.voice.config', 'voice config'),
        ('src.friday.voice.audio_stream', 'audio stream'),
        ('src.friday.voice.wake_word', 'wake word'),
        ('src.friday.voice.stt', 'stt'),
        ('src.friday.voice.tts', 'tts'),
        ('src.friday.voice.pipeline', 'pipeline'),
        ('src.friday.vision', 'vision'),
        ('src.friday.api.main', 'api main'),
    ]

    failed = []
    for module_path, display_name in modules_to_test:
        try:
            __import__(module_path)
            print(f"[OK] Imported {display_name}")
        except Exception as e:
            print(f"[FAIL] Failed to import {display_name}: {e}")
            traceback.print_exc()
            failed.append((display_name, e))

    return failed

def test_voice_pipeline_init():
    """Test initializing the voice pipeline."""
    try:
        from src.friday.voice.pipeline import VoicePipeline
        pipeline = VoicePipeline()
        print("[OK] VoicePipeline instantiated")

        # Test setting a dummy LLM callback
        def dummy_llm(text):
            return f"You said: {text}"

        pipeline.set_llm_callback(dummy_llm)
        print("[OK] LLM callback set")

        # Check that components are initialized
        stats = pipeline.get_stats()
        print(f"[OK] Pipeline stats: {stats}")

        return True
    except Exception as e:
        print(f"[FAIL] Failed to initialize VoicePipeline: {e}")
        traceback.print_exc()
        return False

def test_event_system():
    """Test the event system."""
    try:
        from src.friday.events import subscribe, fire_event, Events
        import asyncio

        received = []
        async def test_handler(event_type, data):
            received.append((event_type, data))

        # Subscribe to a test event
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(subscribe('test_event', test_handler))

        # Fire an event
        loop.run_until_complete(fire_event('test_event', {'test': 'data'}))

        if received and received[0][0] == 'test_event':
            print("[OK] Event system working")
        else:
            print("[FAIL] Event system not receiving events")

        loop.close()
        return True
    except Exception as e:
        print(f"✗ Failed to test event system: {e}")
        traceback.print_exc()
        return False

def main():
    print("=== FRIDAY System Test ===")

    # Test imports
    print("\n1. Testing imports...")
    failed_imports = test_imports()

    # Test event system
    print("\n2. Testing event system...")
    event_ok = test_event_system()

    # Test voice pipeline
    print("\n3. Testing voice pipeline initialization...")
    try:
        pipeline_ok = test_voice_pipeline_init()
    except Exception as e:
        print(f"[ERROR] Voice pipeline test crashed: {e}")
        traceback.print_exc()
        pipeline_ok = False

    # Summary
    print("\n=== Test Summary ===")
    if not failed_imports and event_ok and pipeline_ok:
        print("[PASS] All tests passed!")
        return 0
    else:
        print("[FAIL] Some tests failed:")
        if failed_imports:
            print("  Failed imports:")
            for name, error in failed_imports:
                print(f"    - {name}: {error}")
        if not event_ok:
            print("  Event system failed")
        if not pipeline_ok:
            print("  Voice pipeline initialization failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())