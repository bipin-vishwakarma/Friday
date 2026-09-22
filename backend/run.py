"""
Friday 2.0 Backend Launcher
"""

import sys
import uvicorn
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings

if __name__ == "__main__":
    print(f"Starting Friday 2.0 Backend on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
