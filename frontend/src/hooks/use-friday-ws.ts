"use client"

import { useEffect, useRef, useCallback } from 'react'
import { useStore } from '@/store/useStore'

export function useEventSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelay = useRef(500)

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
  } = useStore()

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return

    const url = `${settings.wsBase}/api/v1/events`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      setBackendHealthy(true)
      reconnectDelay.current = 500
    }

    ws.onclose = () => {
      setWsConnected(false)
      // Exponential backoff
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, 30_000)
        connect()
      }, reconnectDelay.current)
    }

    ws.onerror = () => {
      setBackendHealthy(false)
      ws.close()
    }

    ws.onmessage = (ev) => {
      let msg: any
      try {
        msg = JSON.parse(ev.data)
      } catch {
        return
      }

      // -- Pipeline-ready broadcast --
      if (msg.type === "pipeline_ready") {
        setPipelineRunning(true)
        setPipelineState(msg.data?.state ?? "listening")
        return
      }

      // -- Plain text broadcast (ask response) --
      if (msg.type === "text") {
        try {
          const payload = JSON.parse(msg.data)
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: payload.received_text ?? JSON.stringify(payload),
            timestamp: Date.now(),
            latencyMs: payload.timestamp ? Math.round(payload.timestamp * 1000) : undefined,
          })
          if (payload.timestamp) updateLatency(Math.round(payload.timestamp * 1000))
        } catch {
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: msg.data,
            timestamp: Date.now(),
          })
        }
        return
      }

      // -- Typed event payloads --
      const { event_type, payload } = msg
      if (!event_type) return

      switch (event_type) {
        case "wake_detected":
          setPipelineState("processing")
          addTranscript({
            id: `t-${Date.now()}`,
            role: "user",
            text: "(wake word detected)",
            timestamp: Date.now(),
          })
          break

        case "transcript_received":
          addTranscript({
            id: `t-${Date.now()}`,
            role: "user",
            text: payload?.text ?? payload?.transcript ?? JSON.stringify(payload),
            timestamp: Date.now(),
          })
          break

        case "response_generated":
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: payload?.text ?? payload?.response ?? JSON.stringify(payload),
            timestamp: Date.now(),
          })
          if (payload?.latency_ms) updateLatency(payload.latency_ms)
          break

        case "tts_started":
          setPipelineState("speaking")
          break

        case "tts_ended":
          setPipelineState("listening")
          break

        case "system_ready": {
          const comp = payload?.component
          if (comp === "voice") {
            setPipelineRunning(true)
            setPipelineState("listening")
          }
          break
        }

        case "frame_processed":
          setVisionRunning(true)
          setVisionFrame({
            frameId: payload?.frame_id ?? 0,
            faces: payload?.faces ?? [],
            objects: payload?.objects ?? [],
            emotions: payload?.emotions ?? [],
            text: payload?.text ?? "",
            timestamp: Date.now(),
          })
          break

        case "error_occurred":
          setPipelineState("error")
          addTranscript({
            id: `t-${Date.now()}`,
            role: "friday",
            text: `[ERROR] ${payload?.message ?? JSON.stringify(payload)}`,
            timestamp: Date.now(),
          })
          break
      }
    }
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
  ])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])
}

export function startHealthPoller() {
  let _healthInterval: ReturnType<typeof setInterval> | null = null

  return () => {
    if (_healthInterval) return
    _healthInterval = setInterval(async () => {
      try {
        const response = await fetch(`${useStore.getState().settings.apiBase}/api/v1/status`)
        const s = await response.json()
        useStore.getState().setPipelineRunning(s.is_running ?? false)
        if (s.pipeline) {
          if (s.pipeline.interactions != null) useStore.getState().setInteractions(s.pipeline.interactions)
          if (s.pipeline.uptime != null) useStore.getState().setUptime(s.pipeline.uptime)
        }
        useStore.getState().setBackendHealthy(true)
      } catch {
        useStore.getState().setBackendHealthy(false)
      }
    }, 5_000)
  }
}