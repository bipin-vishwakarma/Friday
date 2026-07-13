import { create } from "zustand";

// ---- Types ----------------------------------------------------------------

export interface FaceBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface VisionFrameData {
  frameId: number;
  faces: FaceBox[];
  objects: string[];
  emotions: string[];
  text: string;
  timestamp: number;
}

export interface TranscriptEntry {
  id: string;
  role: "user" | "friday";
  text: string;
  timestamp: number;
  latencyMs?: number;
}

export interface LatencyStats {
  avgMs: number;
  minMs: number;
  maxMs: number;
  count: number;
}

export type PipelineState =
  | "idle"
  | "listening"
  | "recording"
  | "processing"
  | "speaking"
  | "error";

export interface Settings {
  apiBase: string;
  wsBase: string;
  brainMode: string;
  voiceId: string;
  wakeWord: string;
  sttModel: string;
  ttsSpeed: number;
  deviceMode: string;
}

// ---- Store ----------------------------------------------------------------

interface FridayState {
  // -- Connection --
  wsConnected: boolean;
  backendHealthy: boolean;

  // -- Pipeline --
  pipelineState: PipelineState;
  pipelineRunning: boolean;
  interactions: number;
  uptimeSeconds: number;

  // -- Latency --
  latency: LatencyStats;

  // -- Transcript / log --
  transcript: TranscriptEntry[];

  // -- Vision --
  visionRunning: boolean;
  visionFrame: VisionFrameData | null;
  visionFrameUrl: string | null;

  // -- Settings panel --
  settingsOpen: boolean;
  settings: Settings;

  // -- Actions --
  setWsConnected: (v: boolean) => void;
  setBackendHealthy: (v: boolean) => void;
  setPipelineState: (s: PipelineState) => void;
  setPipelineRunning: (v: boolean) => void;
  setInteractions: (n: number) => void;
  setUptime: (n: number) => void;
  updateLatency: (ms: number) => void;
  addTranscript: (entry: TranscriptEntry) => void;
  clearTranscript: () => void;
  setVisionRunning: (v: boolean) => void;
  setVisionFrame: (d: VisionFrameData | null) => void;
  setVisionFrameUrl: (u: string | null) => void;
  setSettingsOpen: (v: boolean) => void;
  updateSettings: (partial: Partial<Settings>) => void;
}

const defaultSettings: Settings = {
  apiBase: "http://localhost:8000",
  wsBase: "ws://localhost:8000",
  brainMode: "rules-only",
  voiceId: "local-piper",
  wakeWord: "hey friday",
  sttModel: "tiny.en",
  ttsSpeed: 1.0,
  deviceMode: "Samsung J2 Core Browser",
};

let _idCounter = 0;

export const useStore = create<FridayState>((set) => ({
  // -- Defaults --
  wsConnected: false,
  backendHealthy: false,
  pipelineState: "idle",
  pipelineRunning: false,
  interactions: 0,
  uptimeSeconds: 0,
  latency: { avgMs: 0, minMs: Infinity, maxMs: 0, count: 0 },
  transcript: [],
  visionRunning: false,
  visionFrame: null,
  visionFrameUrl: null,
  settingsOpen: false,
  settings: defaultSettings,

  // -- Mutators --
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setBackendHealthy: (backendHealthy) => set({ backendHealthy }),
  setPipelineState: (pipelineState) => set({ pipelineState }),
  setPipelineRunning: (pipelineRunning) => set({ pipelineRunning }),
  setInteractions: (interactions) => set({ interactions }),
  setUptime: (uptimeSeconds) => set({ uptimeSeconds }),
  updateLatency: (ms) =>
    set((s) => {
      const prev = s.latency;
      const count = prev.count + 1;
      const avgMs = (prev.avgMs * prev.count + ms) / count;
      return {
        latency: {
          avgMs,
          minMs: Math.min(prev.minMs, ms),
          maxMs: Math.max(prev.maxMs, ms),
          count,
        },
      };
    }),
  addTranscript: (entry) =>
    set((s) => ({ transcript: [...s.transcript.slice(-99), entry] })),
  clearTranscript: () => set({ transcript: [] }),
  setVisionRunning: (visionRunning) => set({ visionRunning }),
  setVisionFrame: (visionFrame) => set({ visionFrame }),
  setVisionFrameUrl: (visionFrameUrl) => set({ visionFrameUrl }),
  setSettingsOpen: (settingsOpen) => set({ settingsOpen }),
  updateSettings: (partial) =>
    set((s) => ({ settings: { ...s.settings, ...partial } })),
}));

/** Convenience: generate a unique ID for transcript entries. */
export function nextTranscriptId(): string {
  return `t-${Date.now()}-${++_idCounter}`;
}
