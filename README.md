# ⚡ FRIDAY 2.0 // Personal AI Desktop Intelligence System

Friday 2.0 is a 100% free, multi-agent AI desktop companion designed to control your computer, conduct instant web research, hold witty companion chats, and display real-time cybernetic hardware telemetry on a dedicated desk screen (using an Android phone like the Samsung Galaxy J2 Core via ADB).

---

## 🌟 Key Architecture & Features

1. **Laya Classifier (System 1 Reflex)**:
   - Evaluates natural language in a single forward pass (~33ms) to determine intent (`pc_control`, `chat_buddy`, `web_research`, `system_monitor`) with calibrated probabilities.
2. **RareUI-Inspired Cybernetic Desk HUD**:
   - Ultra-lightweight Vite + React SPA (<55 KB gzipped).
   - Animated 60 FPS **Fluid AI Orb** reacting dynamically to Idle, Listening, Thinking, and Transmitting states.
   - Designed for zero-lag performance on the **Samsung Galaxy J2 Core (540x960)**.
3. **100% Free AI & Voice Stack**:
   - **Brain**: Groq LLaMA 3.3 70B (free tier @ 300+ tok/s), local Ollama (100% offline), or OmniRoute.
   - **Voice**: Microsoft Edge-TTS neural audio (`en-GB-RyanNeural` - Jarvis style).
   - **Search**: Instant DuckDuckGo & Wikipedia lookups with zero API fees.
4. **Desktop Automation & Hardware Telemetry**:
   - Live CPU%, RAM usage, Disk, and Network streamed at 1Hz over WebSockets.
   - Native PC control: Volume, Mute, Media playback, App launching (Chrome, Spotify, VS Code, Terminal), Screenshot capture, and Workstation Lock.

---

## 📂 Project Structure

```
Friday/
├── backend/
│   ├── app/
│   │   ├── config.py             # Environment & settings parser
│   │   ├── main.py               # FastAPI + WebSocket hub
│   │   ├── agents/
│   │   │   ├── router.py         # Laya System 1 reflex classifier
│   │   │   ├── brain.py          # AI Chat Buddy (Groq/Ollama/OmniRoute)
│   │   │   ├── pc_controller.py  # Win32 desktop automation & media controls
│   │   │   ├── research.py       # Free real-time web research
│   │   │   └── monitor.py        # Real-time hardware telemetry agent
│   │   └── services/
│   │       ├── voice.py          # Edge-TTS speech synthesis
│   │       └── adb_bridge.py     # Samsung J2 auto-detect & port forwarding
│   ├── requirements.txt
│   └── run.py
├── hud/                          # RareUI-inspired cyber HUD
│   ├── src/
│   │   ├── components/
│   │   │   ├── FluidOrb.tsx      # Animated AI Orb (Canvas/GPU)
│   │   │   ├── TelemetryGauges.tsx # CPU & Memory live dials
│   │   │   ├── QuickActions.tsx  # Touch action tiles (Volume, Apps, Lock)
│   │   │   └── ChatFeed.tsx      # Conversation & Web Speech input
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── start.bat                 # One-click start (Backend + HUD + J2)
│   ├── setup_j2.bat              # ADB reverse proxy & screen launcher
│   └── stop.bat                  # Clean shutdown
├── start.bat                     # Root launcher shortcut
├── stop.bat                      # Root shutdown shortcut
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Launch Friday
Simply double-click `start.bat` or run:
```cmd
start.bat
```
This automatically:
- Starts the FastAPI backend on `http://localhost:8000`
- Launches the Cyber HUD on `http://localhost:5173`
- Configures ADB reverse port forwarding for your connected Samsung J2
- Wakes up the Samsung J2 screen and loads the HUD in fullscreen!

### 2. Stop Friday
To stop all services:
```cmd
stop.bat
```

---

## 📱 Using Samsung Galaxy J2 as Desk Screen
1. Enable **USB Debugging** on the J2 (Settings -> Developer Options -> USB Debugging).
2. Connect it to your PC with a USB cable.
3. Friday will automatically reverse-forward port 5173 and 8000 over the USB cable and keep the display awake.
