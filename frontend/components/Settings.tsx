"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Cpu, Sliders } from "lucide-react";
import { useStore } from "@/store/useStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function Settings() {
  const open = useStore((s) => s.settingsOpen);
  const setOpen = useStore((s) => s.setSettingsOpen);
  const settings = useStore((s) => s.settings);
  const update = useStore((s) => s.updateSettings);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 300 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l border-border bg-card shadow-glow-lg"
          >
            <Card className="h-full rounded-none border-0 bg-transparent">
              <CardHeader className="flex flex-row items-center justify-between border-b border-border">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sliders className="h-4 w-4 text-primary" />
                  Settings
                </CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </CardHeader>

              <CardContent className="space-y-6 overflow-y-auto p-5">
                {/* -- Connection -- */}
                <section className="space-y-3">
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Connection
                  </h4>
                  <div className="space-y-2">
                    <Label htmlFor="apiBase">API Base URL</Label>
                    <Input
                      id="apiBase"
                      value={settings.apiBase}
                      onChange={(e) => update({ apiBase: e.target.value })}
                      placeholder="http://localhost:8000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="wsBase">WebSocket Base URL</Label>
                    <Input
                      id="wsBase"
                      value={settings.wsBase}
                      onChange={(e) => update({ wsBase: e.target.value })}
                      placeholder="ws://localhost:8000"
                    />
                  </div>
                </section>

                {/* -- Local stack -- */}
                <section className="space-y-3">
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Cpu className="h-3 w-3" />
                    Local Stack
                  </h4>
                  <div className="space-y-2">
                    <Label htmlFor="brainMode">Brain Mode</Label>
                    <Input
                      id="brainMode"
                      value={settings.brainMode}
                      onChange={(e) => update({ brainMode: e.target.value })}
                      placeholder="rules-only"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="deviceMode">Desk Buddy Device</Label>
                    <Input
                      id="deviceMode"
                      value={settings.deviceMode}
                      onChange={(e) => update({ deviceMode: e.target.value })}
                      placeholder="Samsung J2 Core Browser"
                    />
                  </div>
                  <p className="rounded-md bg-primary/10 p-3 text-[10px] text-primary">
                    FRIDAY is configured for a free local stack. No Gemini, Groq,
                    OpenAI, or cloud API key is required.
                  </p>
                </section>

                {/* -- Voice -- */}
                <section className="space-y-3">
                  <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Voice Configuration
                  </h4>
                  <div className="space-y-2">
                    <Label htmlFor="wakeWord">Wake Word</Label>
                    <Input
                      id="wakeWord"
                      value={settings.wakeWord}
                      onChange={(e) => update({ wakeWord: e.target.value })}
                      placeholder="hey friday"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="voiceId">TTS Voice</Label>
                    <Input
                      id="voiceId"
                      value={settings.voiceId}
                      onChange={(e) => update({ voiceId: e.target.value })}
                      placeholder="en-US-Neural2-F"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="sttModel">STT Model</Label>
                    <Input
                      id="sttModel"
                      value={settings.sttModel}
                      onChange={(e) => update({ sttModel: e.target.value })}
                      placeholder="whisper-1"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="ttsSpeed">TTS Speed: {settings.ttsSpeed.toFixed(1)}x</Label>
                    <input
                      id="ttsSpeed"
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={settings.ttsSpeed}
                      onChange={(e) => update({ ttsSpeed: parseFloat(e.target.value) })}
                      className="w-32 accent-primary"
                    />
                  </div>
                </section>

                {/* Note */}
                <p className="rounded-md bg-secondary/50 p-3 text-[10px] text-muted-foreground">
                  Settings are stored in browser memory. To persist them across
                  sessions, use the FRIDAY backend config or a browser extension.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
