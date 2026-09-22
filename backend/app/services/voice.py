"""
Voice Service
Generates natural neural speech using Microsoft's free Edge-TTS.
Supports direct local speaker playback and streaming over WebSocket to the J2 HUD.
"""

import os
import io
import asyncio
import logging
import edge_tts
from typing import Optional
from ..config import settings

logger = logging.getLogger("friday.voice")

class VoiceService:
    def __init__(self):
        self.voice = settings.EDGE_VOICE

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to MP3 audio bytes using Edge-TTS."""
        if not text.strip():
            return b""
        
        logger.info(f"Synthesizing voice with {self.voice}: '{text[:40]}...'")
        communicate = edge_tts.Communicate(text, self.voice)
        audio_stream = io.BytesIO()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
                
        return audio_stream.getvalue()

    async def speak_local(self, text: str):
        """Synthesize and play audio through PC speakers asynchronously."""
        try:
            audio_bytes = await self.synthesize(text)
            if not audio_bytes:
                return

            # Save temporary file for playback
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
                f.write(audio_bytes)

            # Play using PowerShell or native player without blocking
            cmd = f"$player = New-Object -ComObject WMPlayer.OCX; $player.URL = '{temp_path}'; $player.controls.play(); while($player.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}; [System.IO.File]::Delete('{temp_path}')"
            asyncio.create_task(self._run_powershell_audio(cmd))
        except Exception as e:
            logger.error(f"Error playing local speech: {e}")

    async def _run_powershell_audio(self, cmd: str):
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
