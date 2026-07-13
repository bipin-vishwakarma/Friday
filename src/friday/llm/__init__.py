"""Rules-only local brain service for FRIDAY AI.

This module intentionally avoids cloud AI providers.  It preserves the old
``llm_service`` / ``get_llm_callback`` API surface so the voice pipeline and
existing endpoints can keep working while the product labels move to
"Rules Brain".
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Generator, List, Optional


RuleHandler = Callable[[str], Optional[str]]


class LLMService:
    """Local rules-only assistant brain.

    The class name is kept for backwards compatibility with imports such as
    ``from src.friday.llm import llm_service``. No Gemini, Groq, OpenAI, or other
    cloud backend is initialized here.
    """

    def __init__(self) -> None:
        self._backend = "rules"
        self._rules: list[RuleHandler] = [
            self._greeting_rule,
            self._farewell_rule,
            self._identity_rule,
            self._time_rule,
            self._date_rule,
            self._status_rule,
            self._vision_rule,
            self._adb_rule,
            self._voice_rule,
            self._help_rule,
        ]

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    @property
    def backend(self) -> str:
        return self._backend

    def is_ready(self) -> bool:
        """Return True when the local rules brain is available."""
        return True

    def get_status(self) -> dict[str, Any]:
        """Return lightweight status metadata for API/admin surfaces."""
        return {
            "backend": self._backend,
            "mode": "rules-only",
            "cloud_required": False,
            "providers": [],
            "rules": len(self._rules),
        }

    # ------------------------------------------------------------------
    # Generation API
    # ------------------------------------------------------------------
    def generate(self, prompt: str, history: Optional[List[dict]] = None) -> str:
        """Generate a deterministic local response for ``prompt``."""
        normalized = self._normalize(prompt)
        if not normalized:
            return "I am here. Say a command or ask for help."

        for rule in self._rules:
            response = rule(normalized)
            if response:
                return response

        return (
            "I can handle local FRIDAY commands right now: status, voice, "
            "camera, ADB, time, date, and help. No cloud AI is connected."
        )

    def generate_stream(
        self, prompt: str, history: Optional[List[dict]] = None
    ) -> Generator[str, None, None]:
        """Yield the local response as a single stream chunk."""
        yield self.generate(prompt, history)

    def get_llm_callback(self) -> Any:
        """Return the callback expected by ``VoicePipeline.set_llm_callback``."""

        def _callback(transcript: str) -> str:
            return self.generate(transcript)

        return _callback

    # ------------------------------------------------------------------
    # Rule helpers
    # ------------------------------------------------------------------
    def _normalize(self, prompt: str) -> str:
        text = (prompt or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text

    def _contains_any(self, text: str, words: tuple[str, ...]) -> bool:
        return any(word in text for word in words)

    def _greeting_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("hello", "hi", "hey", "namaste", "friday")):
            return "Hello bro. FRIDAY is online with the local rules brain."
        return None

    def _farewell_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("bye", "goodbye", "shutdown", "see you")):
            return "Goodbye. I will stay ready for the next local command."
        return None

    def _identity_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("who are you", "what are you", "your name")):
            return "I am FRIDAY, your local desktop buddy running without Gemini, Groq, or OpenAI."
        return None

    def _time_rule(self, text: str) -> Optional[str]:
        if "time" in text:
            return f"The local time is {datetime.now().strftime('%I:%M %p')}."
        return None

    def _date_rule(self, text: str) -> Optional[str]:
        if "date" in text or "today" in text:
            return f"Today is {datetime.now().strftime('%A, %d %B %Y')}."
        return None

    def _status_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("status", "health", "online", "ready")):
            return "FRIDAY backend is ready. Brain mode is rules-only and fully local."
        return None

    def _vision_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("camera", "vision", "see", "frame")):
            return "Camera mode is planned for the J2 browser feed. The PC will analyze received frames locally."
        return None

    def _adb_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("adb", "phone", "j2", "android", "samsung")):
            return "ADB is used for Samsung J2 setup, Wi-Fi connection, opening the buddy UI, and keeping the screen awake."
        return None

    def _voice_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("voice", "whisper", "tts", "speak", "listen")):
            return "Voice stays local: wake word, local STT, rules brain, and local TTS when the models are installed."
        return None

    def _help_rule(self, text: str) -> Optional[str]:
        if self._contains_any(text, ("help", "commands", "what can you do")):
            return (
                "Try: status, time, date, voice status, camera status, ADB status, "
                "or ask me who I am."
            )
        return None


# Backwards-compatible singleton/export names.
llm_service = LLMService()


def get_llm_callback():
    """Return the local brain callback used by the voice pipeline."""
    return llm_service.get_llm_callback()
