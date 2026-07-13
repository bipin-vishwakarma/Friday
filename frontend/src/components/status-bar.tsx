'use client'

import React from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Activity, Clock, Users, MicOff, Mic, Zap, Wifi, WifiOff, Server, ServerOff } from 'lucide-react'
import { formatTime } from '@/lib/utils'

const stateColors: Record<string, string> = {
  idle: 'bg-zinc-500/20 text-zinc-400',
  listening: 'bg-emerald-500/20 text-emerald-400',
  processing: 'bg-amber-500/20 text-amber-400',
  speaking: 'bg-primary/20 text-primary',
  error: 'bg-destructive/20 text-destructive',
}

const stateLabels: Record<string, string> = {
  idle: 'IDLE',
  listening: 'LISTENING',
  processing: 'PROCESSING',
  speaking: 'SPEAKING',
  error: 'ERROR',
}

interface StatTileProps {
  icon: React.ReactNode
  label: string
  value: string | number
  accent?: boolean
}

function StatTile({ icon, label, value, accent }: StatTileProps) {
  return (
    <div className="flex items-center gap-2.5 rounded-md bg-secondary/40 px-3 py-2">
      <span className={accent ? 'text-primary' : 'text-muted-foreground'}>
        {icon}
      </span>
      <div className="flex flex-col">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <span className="text-sm font-semibold tabular-nums">{value}</span>
      </div>
    </div>
  )
}

export const StatusBar = () => {
  const pipelineState = useStore((s) => s.pipelineState)
  const wsConnected = useStore((s) => s.wsConnected)
  const backendHealthy = useStore((s) => s.backendHealthy)
  const uptime = useStore((s) => s.uptimeSeconds)
  const latency = useStore((s) => s.latency)
  const interactions = useStore((s) => s.interactions)
  const settings = useStore((s) => s.settings)

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="relative z-10 px-6 py-4 bg-black/60 backdrop-blur-md border-b border-[rgba(0,212,255,0.1)]"
    >
      <div className="mx-auto max-w-7xl flex items-center justify-between">
        {/* Left: FRIDAY Logo & Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="orb-glow relative flex h-10 w-10 items-center justify-center rounded-full bg-primary/20 border border-primary/30">
              <span className="relative text-sm font-black text-primary">F</span>
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-foreground">
                FRIDAY<span className="text-primary"> AI</span>
              </h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                Voice Assistant Online
              </p>
            </div>
          </div>

          {/* Pipeline State */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border bg-black/50 backdrop-blur-sm"
            style={{ borderColor: `rgba(0, 212, 255, 0.2)` }}>
            <motion.div
              className="w-2 h-2 rounded-full"
              style={{ background: STATE_CONFIG[pipelineState]?.color || '#00d4ff' }}
              animate={{
                scale: pipelineState !== 'idle' ? [1, 1.4, 1] : 1,
                opacity: pipelineState !== 'idle' ? [0.6, 1, 0.6] : 1,
              }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <span className="text-xs font-mono tracking-wider text-primary glow-text-dim">
              {stateLabels[pipelineState] || pipelineState.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Center: System Stats */}
        <div className="flex items-center gap-4">
          <StatTile
            icon={<Zap className="h-4 w-4" />}
            label="Avg Latency"
            value={latency.count > 0 ? `${Math.round(latency.avgMs)}ms` : '--'}
            accent
          />
          <StatTile
            icon={<Clock className="h-4 w-4" />}
            label="Uptime"
            value={formatUptime(uptime)}
          />
          <StatTile
            icon={<Users className="h-4 w-4" />}
            label="Interactions"
            value={interactions}
          />
        </div>

        {/* Right: Connection Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Badge variant={wsConnected ? 'success' : 'destructive'}>
              <span className="flex items-center gap-1">
                {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                WebSocket
              </span>
            </Badge>
            <Badge variant={backendHealthy ? 'success' : 'destructive'}>
              <span className="flex items-center gap-1">
                {backendHealthy ? <Server className="h-3 w-3" /> : <ServerOff className="h-3 w-3" />}
                API
              </span>
            </Badge>
          </div>
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Backend</p>
            <p className="text-xs font-mono text-primary/80 truncate max-w-[180px]">
              {settings.wsBase}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Helper function for uptime formatting
function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  if (m < 60) return `${m}m ${s}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

// State config for status indicator colors
const STATE_CONFIG: Record<string, { color: string }> = {
  idle: { color: '#00d4ff' },
  listening: { color: '#00d4ff' },
  recording: { color: '#ff3366' },
  processing: { color: '#ffaa00' },
  speaking: { color: '#00ff88' },
  error: { color: '#ff3366' },
}