"""FRIDAY AI Package - Voice-Controlled Personal Assistant"""

# Core packages and modules
from src.friday.voice import *
from src.friday.llm import LLMService, get_llm_callback
from src.friday.api import main
from src.friday.events import fire_event, Events
from src.friday.memory import log_voice_interaction
from src.friday.config.settings import (
    KNOWN_FACES_DIR,
    SNAPSHOTS_DIR,
    LOGS_DIR,
    STATIC_DIR,
    API_HOST,
    API_PORT,
    API_WORKERS,
    FACE_DETECTION_CONFIDENCE,
    FACE_RECOGNITION_THRESHOLD,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    FRAME_SKIP,
    ENABLE_VISION,
    ENABLE_TTS,
    ENABLE_ADB,
    ENABLE_WEATHER,
    ENABLE_LOGGING,
    LOG_LEVEL,
    LOG_ROTATION,
    LOG_RETENTION,
    DB_PATH,
    GREETING_COOLDOWN,
    ALERT_COOLDOWN,
    WEATHER_CITY,
    WEATHER_LAT,
    WEATHER_LON,
    WEATHER_UNITS,
)

# FastAPI app instance
app = main.app
__all__ = [
    # Subpackages
    "voice",
    "api",
    "events",
    "memory",
    "config",
    # Services
    "fire_event",
    "Events",
    "log_voice_interaction",
    # Configuration
    "KNOWN_FACES_DIR",
    "SNAPSHOTS_DIR",
    "LOGS_DIR",
    "STATIC_DIR",
    "API_HOST",
    "API_PORT",
    "API_WORKERS",
    "FACE_DETECTION_CONFIDENCE",
    "FACE_RECOGNITION_THRESHOLD",
    "FRAME_WIDTH",
    "FRAME_HEIGHT",
    "FRAME_SKIP",
    "ENABLE_VISION",
    "ENABLE_TTS",
    "ENABLE_ADB",
    "ENABLE_WEATHER",
    "ENABLE_LOGGING",
    "LOG_LEVEL",
    "LOG_ROTATION",
    "LOG_RETENTION",
    "DB_PATH",
    "GREETING_COOLDOWN",
    "ALERT_COOLDOWN",
    "WEATHER_CITY",
    "WEATHER_LAT",
    "WEATHER_LON",
    "WEATHER_UNITS",
    # FastAPI
    "app",
]