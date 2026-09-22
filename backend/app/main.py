"""
Friday 2.0 Backend Application
FastAPI server orchestrating Laya System 1 routing, multi-agent dispatch,
Edge-TTS, PC automation, and real-time WebSocket communication for the J2 HUD.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .config import settings
from .agents.router import RouterAgent
from .agents.brain import BrainAgent
from .agents.pc_controller import PCControllerAgent
from .agents.research import ResearchAgent
from .agents.monitor import MonitorAgent
from .services.voice import VoiceService
from .services.adb_bridge import ADBBridgeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("friday.main")

# Initialize Agents & Services
router = RouterAgent()
brain = BrainAgent()
pc_controller = PCControllerAgent()
research = ResearchAgent()
monitor = MonitorAgent()
voice = VoiceService()
adb_bridge = ADBBridgeService()

class ConnectionManager:
    """Manages active WebSocket connections from desktop & Samsung J2 HUD."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()

# Background telemetry broadcaster
async def telemetry_loop():
    while True:
        try:
            if ws_manager.active_connections:
                telemetry = monitor.get_telemetry()
                await ws_manager.broadcast(telemetry)
        except Exception as e:
            logger.debug(f"Telemetry loop error: {e}")
        await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background telemetry loop
    telemetry_task = asyncio.create_task(telemetry_loop())
    logger.info("Friday 2.0 backend services online.")
    
    # Auto-launch J2 if enabled
    if settings.AUTO_LAUNCH_J2:
        try:
            asyncio.create_task(asyncio.to_thread(adb_bridge.setup_j2_hud))
        except Exception as e:
            logger.warning(f"Failed to auto-launch J2 on startup: {e}")
            
    yield
    # Shutdown
    telemetry_task.cancel()

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    text: str
    speak: bool = True

class ActionRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}

@app.get("/api/health")
async def health_check():
    devices = adb_bridge.get_connected_devices()
    return {
        "status": "online",
        "version": settings.VERSION,
        "brain_provider": settings.BRAIN_PROVIDER,
        "j2_connected": len(devices) > 0,
        "connected_devices": devices
    }

@app.get("/api/telemetry")
async def get_telemetry():
    return monitor.get_telemetry()

@app.post("/api/j2/launch")
async def launch_j2():
    result = await asyncio.to_thread(adb_bridge.setup_j2_hud)
    return result

@app.post("/api/pc/action")
async def execute_pc_action(req: ActionRequest):
    result = pc_controller.execute(req.action, req.params)
    await ws_manager.broadcast({
        "type": "action_result",
        "action": req.action,
        "result": result
    })
    return result

@app.post("/api/process")
async def process_query(req: QueryRequest):
    user_text = req.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    # 1. Broadcast user message and thinking state to HUD
    await ws_manager.broadcast({"type": "user_message", "text": user_text})
    await ws_manager.broadcast({"type": "agent_state", "state": "thinking"})

    # 2. Reflex Router (System 1: Laya Classifier)
    decision = router.route(user_text)
    intent = decision.get("intent", "chat_buddy")
    logger.info(f"Routed intent: {intent} (engine: {decision.get('engine')})")

    reply_text = ""
    action_info = None

    # 3. Multi-Agent Dispatch
    if intent == "pc_control":
        action = decision.get("action")
        params = decision.get("params", {})
        if action:
            action_result = pc_controller.execute(action, params)
            action_info = {"action": action, "params": params, "result": action_result}
            reply_text = action_result.get("message", f"Executed {action}")
        else:
            reply_text = "I recognized a system command, but couldn't determine the exact action."

    elif intent == "system_monitor":
        telemetry = monitor.get_telemetry()
        cpu = telemetry["cpu"]["percent"]
        mem = telemetry["memory"]["percent"]
        reply_text = f"CPU is currently at {cpu}%, and RAM usage is at {mem}%."
        action_info = {"action": "telemetry", "data": telemetry}

    elif intent == "web_search":
        query = decision.get("params", {}).get("query", user_text)
        res_data = await research.search(query)
        summary = res_data.get("summary", "")
        reply_text = summary if summary else f"I searched the web for {query}."
        action_info = {"action": "search", "query": query, "source": res_data.get("source")}

    else:
        # Chat Buddy Agent (System 2)
        reply_text = await brain.chat(user_text)

    # 4. Broadcast response to HUD & switch state to speaking
    await ws_manager.broadcast({"type": "agent_state", "state": "speaking"})
    await ws_manager.broadcast({
        "type": "assistant_message",
        "text": reply_text,
        "intent": intent,
        "action_info": action_info
    })

    # 5. Speak response via Edge-TTS (if requested)
    if req.speak and reply_text:
        asyncio.create_task(voice.speak_local(reply_text))

    # Reset state to idle
    await asyncio.sleep(0.5)
    await ws_manager.broadcast({"type": "agent_state", "state": "idle"})

    return {
        "reply": reply_text,
        "intent": intent,
        "action_info": action_info
    }

@app.get("/api/tts")
async def tts_endpoint(text: str):
    """Audio streaming endpoint for web clients."""
    audio_bytes = await voice.synthesize(text)
    return Response(content=audio_bytes, media_type="audio/mpeg")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial status & telemetry
        await websocket.send_json({"type": "agent_state", "state": "idle"})
        await websocket.send_json(monitor.get_telemetry())
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "query":
                text = data.get("text", "")
                speak = data.get("speak", True)
                if text:
                    # Process query asynchronously
                    asyncio.create_task(process_query(QueryRequest(text=text, speak=speak)))
                    
            elif msg_type == "action":
                action = data.get("action", "")
                params = data.get("params", {})
                if action:
                    res = pc_controller.execute(action, params)
                    await websocket.send_json({
                        "type": "action_result",
                        "action": action,
                        "result": res
                    })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
