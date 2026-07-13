#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Event Bus v1.2 - Robust pub/sub system

Provides asynchronous event subscription and firing.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger("friday.events")

# Mapping of event types to list of handler callables
_event_handlers: Dict[str, List[Callable[[str, dict], Awaitable[None] | None]]] = defaultdict(list)

_lock = asyncio.Lock()

async def subscribe(event_type: str, handler: Callable[[str, dict], Awaitable[None] | None]) -> None:
    """Subscribe a handler to an event type.

    The handler can be a regular function or an async coroutine.
    """
    async with _lock:
        _event_handlers[event_type].append(handler)
        logger.debug("Subscribed %s to %s", handler, event_type)

async def unsubscribe(event_type: str, handler: Optional[Callable[[str, dict], Awaitable[None] | None]] = None) -> None:
    """Unsubscribe a handler from an event type.

    If `handler` is None, all handlers for the event are removed.
    """
    async with _lock:
        if event_type not in _event_handlers:
            return
        if handler is None:
            _event_handlers[event_type].clear()
            logger.debug("Unsubscribed all handlers from %s", event_type)
        else:
            try:
                _event_handlers[event_type].remove(handler)
                logger.debug("Unsubscribed %s from %s", handler, event_type)
            except ValueError:
                logger.warning("Handler %s not found for event %s", handler, event_type)

async def fire_event(event_type: str, data: dict) -> None:
    """Fire an event, invoking all subscribed handlers.

    Handlers are awaited if they are coroutines; regular functions are called normally.
    Exceptions in one handler do not stop others.
    """
    async with _lock:
        handlers = list(_event_handlers.get(event_type, []))
    for handler in handlers:
        try:
            result = handler(event_type, data)
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error in handler %s for event %s: %s", handler, event_type, exc)

# Synchronous wrapper for legacy code that expects a blocking call
def fire_event_sync(event_type: str, data: dict) -> None:
    """Fire an event synchronously, running the async loop temporarily.

    This is useful for code paths that cannot be async.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # If already running, schedule the coroutine
        asyncio.create_task(fire_event(event_type, data))
    else:
        loop.run_until_complete(fire_event(event_type, data))

# Helper to retrieve current handlers (read‑only)
def get_handlers(event_type: str) -> List[Callable[[str, dict], Awaitable[None] | None]]:
    return list(_event_handlers.get(event_type, []))

# Clear all handlers – mainly for tests or shutdown
def clear_all_handlers() -> None:
    _event_handlers.clear()

# Event type constants – can be imported elsewhere
class Events:
    WAKE_DETECTED = "wake_detected"
    SPEECH_STARTED = "speech_started"
    TRANSCRIPT_RECEIVED = "transcript_received"
    RESPONSE_GENERATED = "response_generated"
    TTS_STARTED = "tts_started"
    TTS_ENDED = "tts_ended"
    SYSTEM_READY = "system_ready"
    ERROR_OCCURRED = "error_occurred"
    ADB_COMMAND_EXECUTED = "adb_command_executed"
    ADB_QR_GENERATED = "adb_qr_generated"
    QR_DETECTED = "qr_detected"
    PIPELINE_STATE_CHANGE = "pipeline_state_change"
    FRAME_PROCESSED = "frame_processed"
