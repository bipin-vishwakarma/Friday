# FRIDAY AI - Frontend Dashboard

Professional JARVIS-style AI assistant dashboard built with Next.js 14, React 18, TypeScript, Tailwind CSS, Framer Motion, and Zustand.

## Features

- **Real-time WebSocket** connection to the FRIDAY FastAPI backend (`/api/v1/events`)
- **Voice Pipeline Status** with live state indicators, latency stats, and uptime tracking
- **Transcript / Response Log** with animated message bubbles and auto-scroll
- **Vision Feed** displaying the latest camera frame with face-box overlay (canvas-rendered)
- **Controls** for starting/stopping the wake word listener and sending text queries
- **Settings Panel** for API keys (Gemini, Groq), voice config, and connection URLs
- **JARVIS-style dark UI** with glowing effects, scanline overlays, and animated transitions

## Tech Stack

| Layer        | Technology                          |
|-------------|-------------------------------------|
| Framework   | Next.js 14 (App Router)             |
| UI          | React 18 + TypeScript               |
| Styling     | Tailwind CSS 3 + custom animations  |
| Animation   | Framer Motion 11                    |
| UI Primitives | Radix UI (Dialog, Switch, Label, Tooltip) |
| State       | Zustand 5                           |
| Icons       | Lucide React                        |
| Backend     | FastAPI (Python) on port 8000       |

## Prerequisites

- Node.js >= 18
- npm >= 9
- FRIDAY FastAPI backend running on `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at **http://localhost:3000**.

## Scripts

| Command         | Description                          |
|----------------|--------------------------------------|
| `npm run dev`   | Start development server with hot reload |
| `npm run build` | Production build                     |
| `npm start`     | Start production server              |
| `npm run lint`  | Run ESLint                           |

## Backend Connection

The frontend expects the FRIDAY FastAPI backend at `http://localhost:8000`. If your backend runs on a different port or host, open the **Settings** panel (gear icon, top right) and update:

- **API Base URL** - REST endpoint root (default: `http://localhost:8000`)
- **WebSocket Base URL** - WS endpoint root (default: `ws://localhost:8000`)

### Backend Endpoints Used

| Endpoint                    | Method   | Purpose                              |
|----------------------------|----------|--------------------------------------|
| `/health`                   | GET      | Backend health check                 |
| `/api/v1/status`            | GET      | Pipeline status                      |
| `/api/v1/events`            | WebSocket| Real-time event stream               |
| `/api/v1/wake?start=true`   | POST     | Start wake word listener             |
| `/api/v1/wake`              | DELETE   | Stop wake word listener              |
| `/api/v1/ask?text=...`      | POST     | Send a text query                    |
| `/api/v1/vision/frame`      | GET      | Latest camera frame (JPEG)           |

## Project Structure

```
frontend/
  app/
    layout.tsx          Root layout (HTML shell)
    page.tsx            Next.js entry page
    dashboard.tsx       Main dashboard component (client)
    globals.css         Tailwind base + custom animations
  components/
    StatusCard.tsx      Pipeline status + latency stats
    Controls.tsx        Wake word toggle + text input
    VoiceLog.tsx        Transcript / response log
    VisionFeed.tsx      Camera feed with face-box overlay
    Settings.tsx        Settings slide-over panel
    ui/                 Reusable primitives (Card, Button, Badge, Input, Label, Switch)
  lib/
    api.ts              REST helpers + WebSocket hook + health poller
    utils.ts            Utility functions (cn, formatUptime, formatTime)
  store/
    useStore.ts         Zustand global state
  tailwind.config.js    Tailwind configuration
  next.config.js        Next.js configuration
  postcss.config.js     PostCSS configuration
  tsconfig.json         TypeScript configuration
  package.json          Dependencies and scripts
```

## CORS

The FRIDAY backend must allow CORS from `http://localhost:3000`. The existing FastAPI config uses `allow_origins=["*"]` which works for development.

## License

Part of the FRIDAY AI Desktop Assistant project.
