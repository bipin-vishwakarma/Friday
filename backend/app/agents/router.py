"""
Reflex Router Agent (System 1)
Powered by Laya non-autoregressive decision model (~33ms inference)
with ultra-fast zero-latency fallback heuristics.
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("friday.router")

class RouterAgent:
    def __init__(self):
        self.laya_router = None
        self._init_laya()

    def _init_laya(self):
        try:
            import laya
            # Try initializing Laya Router
            # Laya Router can route state + questions in ~33ms
            self.laya_router = laya.Router(preload=False)
            logger.info("Laya System 1 Decision Router initialized successfully.")
        except Exception as e:
            logger.warning(f"Laya router running in lightweight mode: {e}")
            self.laya_router = None

    def route(self, user_text: str) -> Dict[str, Any]:
        """
        Classify intent and extract routing decision.
        Returns:
            {
                "intent": "pc_control" | "chat_buddy" | "web_search" | "system_monitor",
                "confidence": float,
                "action": Optional[str],
                "params": Dict[str, Any],
                "engine": "laya" | "heuristic"
            }
        """
        text = user_text.strip().lower()
        if not text:
            return {"intent": "chat_buddy", "confidence": 1.0, "engine": "default", "params": {}}

        # First, attempt Laya classification if available
        if self.laya_router is not None:
            try:
                state = {"input": user_text}
                questions = {
                    "intent": {
                        "type": "choice",
                        "instructions": "What is the primary user intent?",
                        "criteria": ["pc_control", "chat_buddy", "web_search", "system_monitor"]
                    },
                    "needs_action": {
                        "type": "noul",
                        "instructions": "Does this request execute a hardware or system action on the PC?"
                    }
                }
                res = self.laya_router.route(state, questions)
                if res and "intent" in res:
                    intent = res["intent"].get("value", "chat_buddy")
                    conf = res["intent"].get("confidence", 0.9)
                    action, params = self._extract_pc_action(text)
                    return {
                        "intent": intent,
                        "confidence": conf,
                        "action": action,
                        "params": params,
                        "engine": "laya"
                    }
            except Exception as e:
                logger.debug(f"Laya inference fallback: {e}")

        # High-speed Heuristic Reflex Classifier
        return self._heuristic_route(text)

    def _heuristic_route(self, text: str) -> Dict[str, Any]:
        # 1. PC System Monitoring check
        if any(w in text for w in ["cpu", "ram", "memory usage", "gpu", "battery", "system stats", "pc status", "pc temperature", "specs"]):
            return {
                "intent": "system_monitor",
                "confidence": 0.98,
                "action": "get_stats",
                "params": {},
                "engine": "heuristic"
            }

        # 2. PC Control check
        action, params = self._extract_pc_action(text)
        if action:
            return {
                "intent": "pc_control",
                "confidence": 0.95,
                "action": action,
                "params": params,
                "engine": "heuristic"
            }

        # 3. Web Search check
        if any(text.startswith(w) for w in ["search for", "google", "look up", "who is", "what is the latest", "weather in"]):
            query = re.sub(r"^(search for|google|look up)\s*", "", text).strip()
            return {
                "intent": "web_search",
                "confidence": 0.92,
                "action": "search",
                "params": {"query": query or text},
                "engine": "heuristic"
            }

        # 4. Default to Conversational Brain / Chat Buddy
        return {
            "intent": "chat_buddy",
            "confidence": 0.90,
            "action": None,
            "params": {"query": text},
            "engine": "heuristic"
        }

    def _extract_pc_action(self, text: str) -> (Optional[str], Dict[str, Any]):
        """Extract Windows desktop actions from natural text."""
        # Volume control
        if "mute" in text:
            return "mute_volume", {}
        vol_match = re.search(r"(?:set|change|turn)?\s*volume\s*(?:to)?\s*(\d{1,3})%?", text)
        if vol_match:
            return "set_volume", {"level": int(vol_match.group(1))}
        if "volume up" in text or "increase volume" in text:
            return "volume_up", {"steps": 5}
        if "volume down" in text or "decrease volume" in text or "lower volume" in text:
            return "volume_down", {"steps": 5}

        # Media control
        if any(w in text for w in ["pause music", "pause video", "pause playback", "play music", "resume music"]):
            return "media_play_pause", {}
        if "next song" in text or "skip song" in text or "next track" in text:
            return "media_next", {}
        if "previous song" in text or "prev track" in text:
            return "media_prev", {}

        # Screen & Lock
        if any(w in text for w in ["lock pc", "lock screen", "lock computer"]):
            return "lock_workstation", {}
        if any(w in text for w in ["sleep pc", "put pc to sleep", "sleep computer"]):
            return "sleep_pc", {}
        if any(w in text for w in ["take screenshot", "capture screen"]):
            return "take_screenshot", {}

        # Application Launch
        open_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\.\s]+)", text)
        if open_match:
            app_name = open_match.group(1).strip()
            # filter out non-app queries like "open conversation"
            if app_name not in ["the door", "settings"]:
                return "open_application", {"app": app_name}

        # Close Application
        close_match = re.search(r"(?:close|exit|terminate)\s+([a-zA-Z0-9_\-\.\s]+)", text)
        if close_match:
            app_name = close_match.group(1).strip()
            return "close_application", {"app": app_name}

        return None, {}
