# ════════════════════════════════════════════════════════════════════
# FRIDAY AI — Configuration (Production-Ready)
# ════════════════════════════════════════════════════════════════════

import os
from pathlib import Path
from typing import Optional

# BASE_DIR = project root (Friday/)
# __file__ is src/friday/config/settings.py  ->  .parent = config/  ->  .parent = friday/
# ->  .parent = src/  ->  .parent = Friday/
BASE_DIR = Path(__file__).parent.parent.parent.parent

# ─── Paths ─────────────────────────────────────────────────────────────
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"
KNOWN_FACES_DIR = BASE_DIR / "data" / "known_faces"
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"

for d in (MODELS_DIR, LOGS_DIR, STATIC_DIR, KNOWN_FACES_DIR, SNAPSHOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ─── Database ──────────────────────────────────────────────────────────
DB_PATH = BASE_DIR / "data" / "friday.db"

# ─── Face Recognition ──────────────────────────────────────────────────
FACE_DETECTION_CONFIDENCE = 0.6
FACE_RECOGNITION_THRESHOLD = 0.5
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_SKIP = 2  # Process every Nth frame

# ─── API Server ────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8000
API_WORKERS = 1

# ─── TTS ───────────────────────────────────────────────────────────────
TTS_VOICE = "en_US-amy-low"
TTS_SPEED = 1.0
TTS_LANG_CODE = "a"  # American English

# ─── Voice / Wake Word ─────────────────────────────────────────────────
WAKE_WORD = "friday"

# ─── ADB Integration ───────────────────────────────────────────────────
ADB_PATH = ""
ADB_POLL_INTERVAL = 10  # seconds

# ─── Greeting & Alerts ─────────────────────────────────────────────────
GREETING_COOLDOWN = 300  # 5 minutes
ALERT_COOLDOWN = 60  # seconds

# ─── Weather (Open-Meteo - no API key needed) ──────────────────────────
WEATHER_CITY = "Dehradun"
WEATHER_LAT = 30.3165
WEATHER_LON = 78.0322
WEATHER_UNITS = "metric"

# ─── Feature Flags ─────────────────────────────────────────────────────
ENABLE_VISION = True
ENABLE_TTS = True
ENABLE_ADB = True
ENABLE_WEATHER = True
ENABLE_LOGGING = True

# ─── Logging ───────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "7 days"
