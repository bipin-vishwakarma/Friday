"use client";

import React, { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, User, Bot } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useStore, type TranscriptEntry } from "@/store/useStore";
import { formatTime } from "@/lib/utils";

function LogEntry({ entry, index }: { entry: TranscriptEntry; index: number }) {
  const isUser = entry.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -8 }}
      transition={{ duration: 0.25 }}
      className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      <div
        className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
          isUser
            ? "bg-secondary text-muted-foreground"
            : "bg-primary/20 text-primary"
        }`}
      >
        {isUser ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
          isUser
            ? "bg-secondary text-foreground rounded-tr-sm"
            : "bg-primary/10 text-foreground/90 rounded-tl-sm border border-primary/10"
        }`}
      >
        <p className="break-words">{entry.text}</p>
        <span className="mt-1 block text-[9px] text-muted-foreground">
          {formatTime(entry.timestamp)}
          {entry.latencyMs != null && ` · ${entry.latencyMs}ms`}
        </span>
      </div>
    </motion.div>
  );
}

export default function VoiceLog() {
  const transcript = useStore((s) => s.transcript);
  const clearTranscript = useStore((s) => s.clearTranscript);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new entries
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript.length]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageSquare className="h-4 w-4 text-primary" />
          Transcript
        </CardTitle>
        {transcript.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearTranscript}>
            Clear
          </Button>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden px-3 pb-3">
        <div
          ref={scrollRef}
          className="flex h-[320px] flex-col gap-2.5 overflow-y-auto pr-1"
        >
          {transcript.length === 0 && (
            <div className="flex flex-1 items-center justify-center">
              <p className="text-xs text-muted-foreground">
                No conversations yet. Start the voice pipeline or type a query.
              </p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {transcript.map((entry, i) => (
              <LogEntry key={entry.id} entry={entry} index={i} />
            ))}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  );
}
