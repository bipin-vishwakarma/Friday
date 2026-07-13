import os
from pathlib import Path
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import json
import cv2
import numpy as np
from datetime import datetime

# Import local modules
from .config.settings import (
    KNOWN_FACES_DIR,
    SNAPSHOTS_DIR,
    LOGS_DIR,
    STATIC_DIR,
    API_HOST,
    API_PORT,
    API_WORKERS,
    ENABLE_VISION,
    ENABLE_TTS,
    ENABLE_ADB,
    ENABLE_WEATHER,
    ENABLE_LOGGING
)
from .vision import VisionEngine
from .tts import TTSManager
from .adb import ADBManager
from .db import Database
from .utils import logger

# Initialize modules
vision_engine = VisionEngine()
tts_manager = TTSManager()
adb_manager = ADBManager()
db = Database()

# Initialize FastAPI app
app = FastAPI(
    title="FRIDAY AI",
    description="Smart personal AI assistant for Bipin",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", response_class=JSONResponse)
async def root():
    return {"status": "online", "service": "FRIDAY AI", "version": "2.0.0"}

# Health check
@app.get("/health")
async def health():
    return {"status": "online", "service": "FRIDAY AI", "version": "2.0.0"}

# Video feed endpoint
@app.get("/video_feed")
async def video_feed():
    """Stream video frames with analysis overlay"""
    async def generate():
        while True:
            # In real implementation, this would process video frames
            # For now, just send a simple frame
            frame_data = b'frame_data_placeholder'  # Replace with actual frame data
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            await asyncio.sleep(0.15)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")