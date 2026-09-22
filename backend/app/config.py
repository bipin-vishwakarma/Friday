import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # App
    APP_NAME: str = "Friday AI Companion"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    HUD_PORT: int = int(os.getenv("HUD_PORT", "5173"))
    
    # Brain / Cognition
    BRAIN_PROVIDER: str = os.getenv("FRIDAY_BRAIN_PROVIDER", "hybrid")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    
    OMNIROUTE_BASE_URL: str = os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    OMNIROUTE_API_KEY: str = os.getenv("OMNIROUTE_API_KEY", "")
    OMNIROUTE_MODEL: str = os.getenv("FRIDAY_OMNIROUTE_MODEL", "auto/best-fast")
    
    # Speech Synthesis (TTS)
    EDGE_VOICE: str = os.getenv("FRIDAY_EDGE_VOICE", "en-GB-RyanNeural")
    
    # Samsung J2 / ADB
    J2_DEVICE_ID: str = os.getenv("J2_DEVICE_ID", "ee866a9b")
    AUTO_LAUNCH_J2: bool = os.getenv("AUTO_LAUNCH_J2", "true").lower() == "true"

settings = Settings()
