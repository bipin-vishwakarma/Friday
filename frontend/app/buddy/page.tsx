"use client";

import React from "react";
import { Inter } from "next/font/google";
import { motion } from "framer-motion";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Wifi,
  WifiOff,
  Shield,
} from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

type BuddyState = "idle" | "listening" | "speaking" | "thinking";

export default function BuddyPage() {
  const [cameraPermission, setCameraPermission] = React.useState<
    "granted" | "denied" | "prompt"
  >("prompt");
  const [cameraOn, setCameraOn] = React.useState(true);
  const [connected, setConnected] = React.useState(false);
  const [state, setState] = React.useState<BuddyState>("idle");

  React.useEffect(() => {
    async function requestCameraPermission() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach((track) => track.stop());
        setCameraPermission("granted");
      } catch {
        setCameraPermission("denied");
      }
    }
    requestCameraPermission();
  }, []);

  const stateLabel: Record<BuddyState, string> = {
    idle: "READY",
    listening: "LISTENING",
    speaking: "SPEAKING",
    thinking: "THINKING",
  };

  const orbColor: Record<BuddyState, string> = {
    idle: "hsl(0 0% 35%)",
    listening: "hsl(199 89% 48%)",
    speaking: "hsl(150 89% 48%)",
    thinking: "hsl(45 89% 48%)",
  };

  return (
    <div
      className={`${inter.className} flex min-h-screen flex-col bg-background bg-grid text-foreground`}
    >
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="orb-glow relative flex h-9 w-9 items-center justify-center rounded-full bg-primary/20">
            <span className="text-base font-black text-primary">F</span>
          </div>
          <span className="text-lg font-bold">Desk Buddy</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {connected ? (
            <Wifi className="h-4 w-4 text-emerald-400" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-400" />
          )}
          <span>{connected ? "Wi-Fi" : "Offline"}</span>
        </div>
      </header>

      {/* Center orb */}
      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-4">
        <motion.div
          className="orb-glow relative h-40 w-40 rounded-full md:h-52 md:w-52"
          style={{ backgroundColor: orbColor[state] }}
          animate={state !== "idle" ? { scale: [1, 1.08, 1] } : { scale: 1 }}
          transition={{
            repeat: state !== "idle" ? Infinity : 0,
            duration: 1.6,
            ease: "easeInOut",
          }}
        />
        <div
          className="rounded-full px-4 py-1.5 text-sm font-bold tracking-wider"
          style={{
            backgroundColor: `${orbColor[state]}22`,
            color: orbColor[state],
          }}
        >
          {stateLabel[state]}
        </div>

        {/* Camera permission note */}
        <p className="max-w-xs text-center text-xs text-muted-foreground">
          {cameraPermission === "granted"
            ? "Camera ready. Browser WebRTC feed will stream to the PC for local analysis."
            : cameraPermission === "denied"
              ? "Camera permission denied. Grant it in Chrome to enable the vision feed."
              : "Waiting for camera permission from Chrome…"}
        </p>

        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <Shield className="h-3 w-3 text-primary" />
          Free local stack · Rules-only brain · No cloud keys
        </div>
      </main>

      {/* Bottom touch controls */}
      <footer className="grid grid-cols-3 gap-3 border-t border-border p-4">
        <button
          onClick={() => setState((s) => (s === "listening" ? "idle" : "listening"))}
          className="flex flex-col items-center gap-1 rounded-xl border border-border bg-secondary/40 py-3 text-muted-foreground active:scale-95"
        >
          {state === "listening" ? (
            <MicOff className="h-6 w-6 text-primary" />
          ) : (
            <Mic className="h-6 w-6" />
          )}
          <span className="text-[11px]">{state === "listening" ? "Mute" : "Talk"}</span>
        </button>

        <button
          onClick={() => setCameraOn((v) => !v)}
          className="flex flex-col items-center gap-1 rounded-xl border border-border bg-secondary/40 py-3 text-muted-foreground active:scale-95"
        >
          {cameraOn ? (
            <Video className="h-6 w-6 text-primary" />
          ) : (
            <VideoOff className="h-6 w-6" />
          )}
          <span className="text-[11px]">{cameraOn ? "Cam On" : "Cam Off"}</span>
        </button>

        <button
          onClick={() => setConnected((v) => !v)}
          className="flex flex-col items-center gap-1 rounded-xl border border-border bg-secondary/40 py-3 text-muted-foreground active:scale-95"
        >
          {connected ? (
            <Wifi className="h-6 w-6 text-emerald-400" />
          ) : (
            <WifiOff className="h-6 w-6" />
          )}
          <span className="text-[11px]">{connected ? "Online" : "Reconnect"}</span>
        </button>
      </footer>
    </div>
  );
}