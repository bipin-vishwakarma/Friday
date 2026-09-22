"""
Windows Media & Spotify Tracker Service
Monitors live media playback (Spotify, Chrome, Edge, media players)
using Windows GlobalSystemMediaTransportControlsSessionManager.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("friday.media_tracker")

class MediaTrackerService:
    def __init__(self):
        self._cached_media: Dict[str, Any] = {"active": False, "title": "", "artist": "", "status": "stopped"}

    async def get_current_media(self) -> Dict[str, Any]:
        """Fetch current media info asynchronously."""
        try:
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus

            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if not session:
                return {"active": False, "title": "", "artist": "", "album": "", "status": "stopped"}

            info = await session.try_get_media_properties_async()
            playback = session.get_playback_info()
            
            status = "unknown"
            if playback:
                raw_status = playback.playback_status
                if raw_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                    status = "playing"
                elif raw_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED:
                    status = "paused"
                elif raw_status == GlobalSystemMediaTransportControlsSessionPlaybackStatus.STOPPED:
                    status = "stopped"

            data = {
                "active": bool(info.title),
                "title": info.title or "Unknown Track",
                "artist": info.artist or "Unknown Artist",
                "album": info.album_title or "",
                "status": status
            }
            self._cached_media = data
            return data
        except Exception as e:
            logger.debug(f"Media extraction note: {e}")
            return self._cached_media
