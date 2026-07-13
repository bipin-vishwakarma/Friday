"""FastAPI backend for FRIDAY AI voice control.

Provides REST and WebSocket interfaces for:
- Starting/stopping voice pipeline
- Handling voice queries
- Streaming system events
- Controlling ADB devices
- Testing local rules brain integration
- Streaming vision frames
"""

import io
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from src.friday.voice.pipeline import pipeline, VoicePipeline
from src.friday.events import fire_event, Events, subscribe
from src.friday.adb import get_adb_manager
from src.friday.llm import llm_service
from src.friday.vision import vision

logger = logging.getLogger("friday.api")

BROADCAST_EVENTS = {
    Events.WAKE_DETECTED,
    Events.TRANSCRIPT_RECEIVED,
    Events.RESPONSE_GENERATED,
    Events.TTS_STARTED,
    Events.TTS_ENDED,
    Events.SYSTEM_READY,
    Events.ERROR_OCCURRED,
    Events.ADB_COMMAND_EXECUTED,
    Events.ADB_QR_GENERATED,
    Events.PIPELINE_STATE_CHANGE,
    Events.FRAME_PROCESSED,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start/stop pipeline, vision and event broadcast."""
    logger.info("🚀 Starting FRIDAY API server (lifespan)")

    app.state.active_pipeline = pipeline
    app.state.manager = ConnectionManager()

    # Subscribe to events bus -> broadcast over WebSocket
    async def broadcast_handler(event_type: str, data: dict):
        if event_type in BROADCAST_EVENTS:
            await app.state.manager.broadcast({"event_type": event_type, "payload": data})

    for evt in BROADCAST_EVENTS:
        await subscribe(evt, broadcast_handler)

    # Start voice pipeline + vision engine
    try:
        pipeline.set_llm_callback(llm_service.get_llm_callback())
        pipeline.start()
    except Exception as e:
        logger.error("Voice pipeline failed to start: %s", e)

    try:
        vision.start(source="webcam")
    except Exception as e:
        logger.error("Vision engine failed to start: %s", e)

    yield

    logger.info("🛑 Shutting down FRIDAY API server")
    try:
        pipeline.stop()
    except Exception:
        pass
    try:
        vision.stop()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Connection manager for WebSocket clients
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)


# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FRIDAY AI Voice Backend",
    description="Backend API for FRIDAY Desktop Buddy voice control",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS – locked to localhost for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "FRIDAY AI backend is running"}


# ---------------------------------------------------------------------------
# WebSocket event stream
# ---------------------------------------------------------------------------
@app.websocket("/api/v1/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await app.state.manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        app.state.manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        app.state.manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Voice pipeline control
# ---------------------------------------------------------------------------
@app.post("/api/v1/wake")
async def wake_control(start: bool = True):
    """Start or stop the voice pipeline."""
    pl: VoicePipeline = app.state.active_pipeline
    if pl is None:
        raise HTTPException(status_code=500, detail="Voice pipeline not initialized")
    if start:
        logger.info("🔊 Starting voice pipeline")
        pl.start()
    else:
        logger.info("🔇 Stopping voice pipeline")
        pl.stop()
    return {"status": "ok", "action": "start" if start else "stop"}


@app.delete("/api/v1/wake")
async def wake_stop():
    return await wake_control(start=False)


@app.post("/api/v1/ask")
async def voice_ask(text: str):
    """Send a text query directly to the local rules brain."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    response = llm_service.generate(text)
    return {"status": "ok", "input": text, "response": response}


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
@app.get("/api/v1/status")
async def get_status():
    pl: VoicePipeline = app.state.active_pipeline
    stats = pl.get_stats() if pl else None
    return {"pipeline": stats, "is_running": pl.is_running if pl else False}


# ---------------------------------------------------------------------------
# ADB control
# ---------------------------------------------------------------------------
@app.get("/api/v1/adb/status")
async def adb_status():
    mgr = get_adb_manager()
    return {
        "connected": mgr.is_connected(),
        "devices": mgr.list_devices(),
        "adb_path": str(mgr.adb_path),
    }


@app.post("/api/v1/adb/connect")
async def adb_connect(ip: str, port: int = 5555):
    mgr = get_adb_manager()
    return {"success": mgr.connect(ip, port), "ip": ip, "port": port}


@app.post("/api/v1/adb/disconnect")
async def adb_disconnect():
    mgr = get_adb_manager()
    return {"success": mgr.disconnect()}


@app.post("/api/v1/adb/action")
async def adb_action(action: str, **kwargs):
    mgr = get_adb_manager()
    actions = mgr.get_actions()
    if action not in actions:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    try:
        result = actions[action](**kwargs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": bool(result), "result": result}


@app.get("/api/v1/adb/qr")
async def adb_qr():
    """Generate a QR code for ADB over-WiFi pairing.

    The QR contains the command ``adb connect <ip>:5555`` which the Android
    device can scan to initiate the connection. Returns the PNG image directly.
    """
    from src.friday.adb.qr import get_qr_payload
    png_bytes, cmd = get_qr_payload()
    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="adb-connect.png"'}
    )


# ---------------------------------------------------------------------------
# Local rules brain (LLM-compatible aliases)
# ---------------------------------------------------------------------------
@app.post("/api/v1/llm/generate")
async def llm_generate(prompt: str, history: Optional[List[dict]] = None):
    response = llm_service.generate(prompt, history)
    return {"success": True, "backend": "rules", "response": response}


@app.post("/api/v1/llm/stream")
async def llm_stream(prompt: str, history: Optional[List[dict]] = None):
    def event_stream():
        for chunk in llm_service.generate_stream(prompt, history):
            yield chunk
    return StreamingResponse(event_stream(), media_type="text/plain")


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------
@app.get("/api/v1/vision/status")
async def vision_status():
    return {
        "running": vision.is_running(),
        "frame_count": vision._frame_count,
        "last_frame_timestamp": (
            vision.get_last_result().timestamp if vision.get_last_result() else None
        ),
    }


@app.post("/api/v1/vision/start")
async def vision_start(source: str = "webcam"):
    vision.start(source=source)
    return {"success": True, "running": vision.is_running()}


@app.post("/api/v1/vision/stop")
async def vision_stop():
    vision.stop()
    return {"success": True, "running": vision.is_running()}


@app.get("/api/v1/vision/frame")
async def vision_frame():
    """Return the most recent processed frame as a JPEG."""
    result = vision.get_last_result()
    if result is None:
        raise HTTPException(status_code=404, detail="No frame available yet")
    frame = getattr(result, "frame", None)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame data not retained")
    ret, jpeg = cv2.imencode(".jpg", frame)
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to encode frame")
    return StreamingResponse(io.BytesIO(jpeg.tobytes()), media_type="image/jpeg")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("src.friday.api.main:app", host="127.0.0.1", port=8000, reload=False)
