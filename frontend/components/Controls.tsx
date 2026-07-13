"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Mic, MicOff, Send, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useStore, nextTranscriptId } from "@/store/useStore";
import { startWake, stopWake, askText } from "@/lib/api";

export default function Controls() {
  const pipelineRunning = useStore((s) => s.pipelineRunning);
  const setPipelineRunning = useStore((s) => s.setPipelineRunning);
  const setPipelineState = useStore((s) => s.setPipelineState);
  const addTranscript = useStore((s) => s.addTranscript);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const toggleWake = async () => {
    try {
      if (pipelineRunning) {
        await stopWake();
        setPipelineRunning(false);
        setPipelineState("idle");
      } else {
        await startWake();
        setPipelineRunning(true);
        setPipelineState("listening");
      }
    } catch (err) {
      console.error("Wake toggle failed", err);
    }
  };

  const handleAsk = async () => {
    const text = query.trim();
    if (!text || loading) return;

    setLoading(true);
    addTranscript({
      id: nextTranscriptId(),
      role: "user",
      text,
      timestamp: Date.now(),
    });
    setQuery("");

    try {
      await askText(text);
    } catch (err) {
      addTranscript({
        id: nextTranscriptId(),
        role: "friday",
        text: `[ERROR] Failed to send query: ${String(err)}`,
        timestamp: Date.now(),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Wake word toggle */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Wake Word Listener</span>
          <motion.div whileTap={{ scale: 0.92 }}>
            <Button
              variant={pipelineRunning ? "destructive" : "default"}
              size="sm"
              onClick={toggleWake}
              className="gap-1.5"
            >
              {pipelineRunning ? (
                <>
                  <MicOff className="h-3.5 w-3.5" />
                  Stop
                </>
              ) : (
                <>
                  <Mic className="h-3.5 w-3.5" />
                  Start
                </>
              )}
            </Button>
          </motion.div>
        </div>

        {/* Text query */}
        <div className="flex gap-2">
          <Input
            placeholder="Type a message to FRIDAY..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            disabled={loading}
          />
          <motion.div whileTap={{ scale: 0.92 }}>
            <Button
              size="icon"
              onClick={handleAsk}
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </motion.div>
        </div>
      </CardContent>
    </Card>
  );
}
