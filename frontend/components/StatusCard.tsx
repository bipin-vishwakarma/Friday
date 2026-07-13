"use client";

import React from "react";
import { motion } from "framer-motion";
import { Activity, Zap, Clock, Users } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStore, type PipelineState } from "@/store/useStore";
import { formatUptime } from "@/lib/utils";

const stateColors: Record<PipelineState, string> = {
  idle: "bg-zinc-500/20 text-zinc-400",
  listening: "bg-emerald-500/20 text-emerald-400",
  recording: "bg-sky-500/20 text-sky-400",
  processing: "bg-amber-500/20 text-amber-400",
  speaking: "bg-primary/20 text-primary",
  error: "bg-destructive/20 text-destructive",
};

const stateLabels: Record<PipelineState, string> = {
  idle: "IDLE",
  listening: "LISTENING",
  recording: "RECORDING",
  processing: "PROCESSING",
  speaking: "SPEAKING",
  error: "ERROR",
};

interface StatTileProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  accent?: boolean;
}

function StatTile({ icon, label, value, accent }: StatTileProps) {
  return (
    <div className="flex items-center gap-2.5 rounded-md bg-secondary/40 px-3 py-2">
      <span className={accent ? "text-primary" : "text-muted-foreground"}>{icon}</span>
      <div className="flex flex-col">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold tabular-nums">{value}</span>
      </div>
    </div>
  );
}

export default function StatusCard() {
  const pipelineState = useStore((s) => s.pipelineState);
  const wsConnected = useStore((s) => s.wsConnected);
  const backendHealthy = useStore((s) => s.backendHealthy);
  const uptime = useStore((s) => s.uptimeSeconds);
  const latency = useStore((s) => s.latency);
  const interactions = useStore((s) => s.interactions);

  return (
    <Card className="relative overflow-hidden border-glow">
      {/* Subtle scanline overlay */}
      <div className="pointer-events-none absolute inset-0 scanline" />

      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4 text-primary" />
          Voice Pipeline
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={wsConnected ? "success" : "destructive"}>
            {wsConnected ? "WS Live" : "WS Down"}
          </Badge>
          <Badge variant={backendHealthy ? "success" : "destructive"}>
            {backendHealthy ? "API OK" : "API Down"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* State indicator */}
        <div className="flex items-center gap-3">
          <motion.div
            className="orb-glow relative h-5 w-5 rounded-full"
            style={{
              backgroundColor:
                pipelineState === "error"
                  ? "hsl(0 72% 51%)"
                  : pipelineState === "idle"
                  ? "hsl(0 0% 35%)"
                  : "hsl(199 89% 48%)",
            }}
            animate={
              pipelineState !== "idle"
                ? { scale: [1, 1.15, 1] }
                : { scale: 1 }
            }
            transition={
              pipelineState !== "idle"
                ? { repeat: Infinity, duration: 1.6, ease: "easeInOut" }
                : {}
            }
          />
          <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-bold tracking-wide ${stateColors[pipelineState]}`}>
            {stateLabels[pipelineState]}
          </span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatTile
            icon={<Clock className="h-3.5 w-3.5" />}
            label="Uptime"
            value={formatUptime(uptime)}
          />
          <StatTile
            icon={<Zap className="h-3.5 w-3.5" />}
            label="Avg Latency"
            value={
              latency.count > 0 ? `${Math.round(latency.avgMs)}ms` : "--"
            }
            accent
          />
          <StatTile
            icon={<Activity className="h-3.5 w-3.5" />}
            label="Min / Max"
            value={
              latency.count > 0
                ? `${Math.round(latency.minMs)} / ${Math.round(latency.maxMs)}`
                : "--"
            }
          />
          <StatTile
            icon={<Users className="h-3.5 w-3.5" />}
            label="Interactions"
            value={interactions}
          />
        </div>
      </CardContent>
    </Card>
  );
}
