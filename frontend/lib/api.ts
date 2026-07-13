import { useEffect, useRef, useCallback } from "react";
import { useStore } from "@/store/useStore";

// ---------------------------------------------------------------------------
// REST helpers
// ---------------------------------------------------------------------------

function baseUrl(): string {
  return useStore.getState().settings.apiBase;
}

export async function fetchHealth(): Promise<{ status: string }> {
  const r = await fetch(`${baseUrl()}/health`);
  return r.json();
}

export async function fetchStatus() {
  const r = await fetch(`${baseUrl()}/api/v1/status`);
  return r.json();
}

export async function startWake(): Promise<void> {
  await fetch(`${baseUrl()}/api/v1/wake?start=true`, { method: "POST" });
}

export async function stopWake(): Promise<void> {
  await fetch(`${baseUrl()}/api/v1/wake`, { method: "DELETE" });
}

export async function askText(text: string) {
  const r = await fetch(
    `${baseUrl()}/api/v1/ask?text=${encodeURIComponent(text)}`,
    { method: "POST" }
  );
  return r.json();
}

/** Fetch the latest vision JPEG frame as a Blob URL. */
export async function fetchVisionFrame(): Promise<string | null> {
  try {
    const r = await fetch(`${baseUrl()}/api/v1/vision/frame`);
    if (!r.ok) return null;
    const blob = await r.blob();
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// WebSocket hook
// ---------------------------------------------------------------------------

/**
 * Connects to the backend WebSocket at /api/v1/events and dispatches incoming
 * events into the Zustand store.
 *
 * Automatically reconnects on disconnect.
 */
export function useEventSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelay = useRef(500);

  const {
    settings,
    setWsConnected,
    setBackendHealthy,
    setPipelineState,
    setPipelineRunning,
    setInteractions,
    setUptime,
    addTranscript,
    updateLatency,
    setVisionFrame,
    setVisionRunning,
  } = useStore.getState();

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

    const url = `${settings.wsBase}/api/v1/events`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      setBackendHealthy(true);
      reconnectDelay.current = 500;
    };

    ws.onclose = () => {
      setWsConnected(false);
      // Exponential backoff
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, 30_000);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      setBackendHealthy(false);
      ws.close();
    };

    ws.onmessage = (ev) => {
      let msg: any;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }

      // -- Pipeline-ready broadcast --
      if (msg.type === "pipeline_ready") {
        setPipelineRunning(true);
        setPipelineState(msg.data?.state ?? "listening");
        return;
      }

      // -- Plain text broadcast (ask response) --
      if (msg.type === "text") {
        try {
          const payload = JSON.parse(msg.data);
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: payload.received_text ?? JSON.stringify(payload),
            timestamp: Date.now(),
            latencyMs: payload.timestamp ? Math.round(payload.timestamp * 1000) : undefined,
          });
          if (payload.timestamp) updateLatency(Math.round(payload.timestamp * 1000));
        } catch {
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: msg.data,
            timestamp: Date.now(),
          });
        }
        return;
      }

      // -- Typed event payloads --
      const { event_type, payload } = msg;
      if (!event_type) return;

      switch (event_type) {
        case "wake_detected":
          setPipelineState("processing");
          addTranscript({
            id: `t-${Date.now()}`,
            role: "user",
            text: "(wake word detected)",
            timestamp: Date.now(),
          });
          break;

        case "transcript_received":
          addTranscript({
            id: `t-${Date.now()}`,
            role: "user",
            text: payload?.text ?? payload?.transcript ?? JSON.stringify(payload),
            timestamp: Date.now(),
          });
          break;

        case "response_generated":
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: payload?.text ?? payload?.response ?? JSON.stringify(payload),
            timestamp: Date.now(),
          });
          if (payload?.latency_ms) updateLatency(payload.latency_ms);
          break;

        case "tts_started":
          setPipelineState("speaking");
          break;

        case "tts_ended":
          setPipelineState("listening");
          break;

        case "system_ready": {
          const comp = payload?.component;
          if (comp === "voice") {
            setPipelineRunning(true);
            setPipelineState("listening");
          }
          break;
        }

        case "frame_processed":
          setVisionRunning(true);
          setVisionFrame({
            frameId: payload?.frame_id ?? 0,
            faces: payload?.faces ?? [],
            objects: payload?.objects ?? [],
            emotions: payload?.emotions ?? [],
            text: payload?.text ?? "",
            timestamp: Date.now(),
          });
          break;

        case "error_occurred":
          setPipelineState("error");
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: `[ERROR] ${payload?.message ?? JSON.stringify(payload)}`,
            timestamp: Date.now(),
          });
          break;
      }
    };
  }, [
    settings.wsBase,
    setWsConnected,
    setBackendHealthy,
    setPipelineState,
    setPipelineRunning,
    setInteractions,
    setUptime,
    addTranscript,
    updateLatency,
    setVisionFrame,
    setVisionRunning,
  ]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
}

// ---------------------------------------------------------------------------
// Background health poller
// ---------------------------------------------------------------------------

let _healthInterval: ReturnType<typeof setInterval> | null = null;

export function startHealthPoller() {
  if (_healthInterval) return;
  _healthInterval = setInterval(async () => {
    try {
      const s = await fetchStatus();
      useStore.getState().setPipelineRunning(s.is_running ?? false);
      if (s.pipeline) {
        if (s.pipeline.interactions != null) useStore.getState().setInteractions(s.pipeline.interactions);
        if (s.pipeline.uptime != null) useStore.getState().setUptime(s.pipeline.uptime);
      }
      useStore.getState().setBackendHealthy(true);
    } catch {
      useStore.getState().setBackendHealthy(false);
    }
  }, 5_000);
}
