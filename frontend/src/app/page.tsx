'use client'

import React, { useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { FridayOrb } from '@/components/friday-orb'
import { TranscriptPanel } from '@/components/transcript-panel'
import { StatusBar } from '@/components/status-bar'
import { ControlPanel } from '@/components/control-panel'
import { useEventSocket, startHealthPoller } from '@/lib/api'

function Particles() {
  const particles = useMemo(() => {
    return Array.from({ length: 30 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      delay: `${Math.random() * 15}s`,
      duration: `${10 + Math.random() * 20}s`,
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.1,
    }))
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: p.left,
            width: `${p.size}px`,
            height: `${p.size}px`,
            animationDelay: p.delay,
            animationDuration: p.duration,
            opacity: p.opacity,
          }}
        />
      ))}
    </div>
  )
}

function HexGrid() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 opacity-[0.03]">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="hex" width="56" height="100" patternUnits="userSpaceOnUse" patternTransform="scale(2)">
            <path d="M28 66L0 50L0 16L28 0L56 16L56 50L28 66L28 100" fill="none" stroke="#00d4ff" strokeWidth="0.5"/>
            <path d="M28 0L28 34L0 50L0 84L28 100L56 84L56 50L28 34" fill="none" stroke="#00d4ff" strokeWidth="0.3"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hex)" />
      </svg>
    </div>
  )
}

export default function Home() {
  useEventSocket()

  useEffect(() => {
    startHealthPoller()
  }, [])

  return (
    <div className="relative flex flex-col h-screen w-screen overflow-hidden bg-[#020b18]">
      {/* Background layers */}
      <Particles />
      <HexGrid />
      <div className="fixed inset-0 bg-grid pointer-events-none z-0" />

      {/* Scanline overlay */}
      <div className="fixed inset-0 scanlines pointer-events-none z-[60]" />
      <div className="fixed inset-0 scanline-sweep pointer-events-none z-[55]" />

      {/* Radial vignette */}
      <div
        className="fixed inset-0 pointer-events-none z-[1]"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 30%, rgba(2,11,24,0.6) 70%, rgba(2,11,24,0.95) 100%)',
        }}
      />

      {/* Status Bar - Top */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="relative z-10"
      >
        <StatusBar />
      </motion.div>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 gap-4 overflow-hidden">
        {/* Orb */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3, ease: 'easeOut' }}
        >
          <FridayOrb />
        </motion.div>

        {/* Transcript */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="w-full max-w-2xl"
        >
          <TranscriptPanel />
        </motion.div>
      </main>

      {/* Control Panel - Bottom */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.7 }}
        className="relative z-10"
      >
        <ControlPanel />
      </motion.div>
    </div>
  )
}