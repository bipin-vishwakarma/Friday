"""
AI Brain / Buddy Agent (System 2)
Conversational companion engine supporting Groq Free Tier, Local Ollama,
and OmniRoute with rolling context memory and Friday persona.
"""

import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("friday.brain")

FRIDAY_SYSTEM_PROMPT = """You are FRIDAY, an ultra-smart, loyal, witty, and helpful personal AI desktop assistant and companion.
You talk naturally like a real buddy on a desk. Keep your verbal responses direct, warm, concise, and engaging (usually 1-3 sentences unless asked for an in-depth explanation).
You know you have full control over the user's PC and have a dedicated desk HUD screen running on a Samsung Galaxy J2 Core.
"""

class BrainAgent:
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.max_history = 10

    def clear_memory(self):
        self.history = []

    async def chat(self, user_message: str) -> str:
        """Generate conversational response using the optimal free model provider."""
        self.history.append({"role": "user", "content": user_message})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]

        messages = [{"role": "system", "content": FRIDAY_SYSTEM_PROMPT}] + self.history

        # 1. Try Groq Free Tier if configured
        if settings.GROQ_API_KEY:
            try:
                reply = await self._call_groq(messages)
                if reply:
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
            except Exception as e:
                logger.warning(f"Groq API error: {e}. Falling back...")

        # 2. Try OmniRoute / OpenAI-compatible proxy if configured
        if settings.OMNIROUTE_API_KEY and settings.OMNIROUTE_BASE_URL:
            try:
                reply = await self._call_openai_compatible(
                    base_url=settings.OMNIROUTE_BASE_URL,
                    api_key=settings.OMNIROUTE_API_KEY,
                    model=settings.OMNIROUTE_MODEL,
                    messages=messages
                )
                if reply:
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
            except Exception as e:
                logger.debug(f"OmniRoute proxy not reachable: {e}")

        # 3. Try Local Ollama (100% offline free)
        try:
            reply = await self._call_ollama(messages)
            if reply:
                self.history.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            logger.debug(f"Ollama local not reachable: {e}")

        # 4. Built-in Offline Fallback Buddy Responses
        reply = self._offline_fallback_response(user_message)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    async def _call_groq(self, messages: List[Dict[str, str]]) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "max_tokens": 400,
            "temperature": 0.7
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            return None

    async def _call_openai_compatible(self, base_url: str, api_key: str, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 400,
            "temperature": 0.7
        }
        url = f"{base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            return None

    async def _call_ollama(self, messages: List[Dict[str, str]]) -> Optional[str]:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["message"]["content"].strip()
            return None

    def _offline_fallback_response(self, text: str) -> str:
        """Smart reflex responses when no external LLM endpoint is active."""
        t = text.lower()
        if any(w in t for w in ["hello", "hi", "hey"]):
            return "Hey there! Friday 2.0 is online and ready on your desk. How can I help you today?"
        if any(w in t for w in ["who are you", "what are you"]):
            return "I am Friday, your personal AI desktop companion and intelligence system. I monitor your PC and assist you with anything you need!"
        if any(w in t for w in ["how are you", "how are you doing"]):
            return "Running at peak efficiency! All systems are nominal and ready for commands."
        if any(w in t for w in ["joke", "funny"]):
            return "Why do programmers prefer dark mode? Because light attracts bugs!"
        if any(w in t for w in ["thank", "thanks"]):
            return "Always at your service, boss!"
        return f"I heard you loud and clear: '{text}'. For deep conversations, connect your free Groq key or start local Ollama."
