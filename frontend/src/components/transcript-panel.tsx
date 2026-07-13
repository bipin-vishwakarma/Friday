'use client'

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStore } from '@/store/useStore'
import { formatTime } from '@/lib/utils'

// Typewriter hook
const useTypewriter = (text: string, speed = 25) => {
  const [display, setDisplay] = React.useState('')
  React.useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      setDisplay(text.slice(0, i))
      i++
      if (i > text.length) clearInterval(interval)
    }, speed)
    return () => clearInterval(interval)
  }, [text, speed])
  return display
}

export const TranscriptPanel = () => {
  const { transcript } = useStore(state => ({
    transcript: state.transcript,
  }))

  return (
    <motion.div
      className="fixed inset-y-0 right-0 w-[380px] max-h-[85vh] overflow-y-auto backdrop-blur-lg bg-[rgba(10,22,40,0.8)] border-l border-[rgba(0,212,255,0.2)] px-4 pt-6 pb-8 space-y-4 z-[50]"
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 100 }}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-2 border-b border-[rgba(0,212,255,0.1)]">
          <h3 className="text-xs font-mono tracking-wider text-[#6b8ba4] uppercase">
            TRANSCRIPT LOG
          </h3>
          <div className="flex items-center gap-2 text-[10px]">
            <div className="w-2 h-2 rounded-full bg-[rgba(0,212,255,0.4)]" />
            <span className="text-[#6b8ba4]">ONLINE</span>
          </div>
        </div>

        {/* Transcript entries */}
        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {transcript.map((entry, index) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                <div className={`flex gap-3 ${
                  entry.role === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                  {/* Avatar */}
                  <div className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold">
                    {entry.role === 'user' ? (
                      <>
                        <div className="w-4 h-4 bg-[rgba(0,212,255,0.2)] rounded-full flex items-center justify-center">
                          <div className="w-2 h-2 bg-[#00d4ff] rounded-full" />
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="w-4 h-4 bg-[rgba(0,212,255,0.1)] rounded-full flex items-center justify-center">
                          <div className="w-2 h-2 bg-[#00ff88] rounded-full" />
                        </div>
                      </>
                    )}
                  </div>

                  {/* Message bubble */}
                  <motion.div
                    className={`max-w-xs rounded-lg px-3 py-2 text-xs leading-relaxed break-words ${
                      entry.role === 'user'
                        ? 'bg-[rgba(0,212,255,0.15)] border border-[rgba(0,212,255,0.3)] text-[#d0e8ff] rounded-tr-lg'
                        : 'bg-[rgba(0,255,136,0.1)] border border-[rgba(0,255,136,0.3)] text-[#a0fcc8] rounded-tl-lg'
                    }`}
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="break-all">{entry.text}</p>
                    {entry.latencyMs !== undefined && (
                      <div className="mt-1 flex items-center gap-1 text-[9px] text-[rgba(255,255,255,0.5)]">
                        <div className="w-1 h-1 rounded-full bg-[rgba(255,255,255,0.3)]" />
                        <span>{entry.latencyMs}ms</span>
                      </div>
                    )}
                    <span className="mt-1 block text-[9px] text-[rgba(255,255,255,0.4)]">
                      {formatTime(entry.timestamp)}
                    </span>
                  </motion.div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Placeholder when empty */}
          {transcript.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-10 h-10 rounded-full bg-[rgba(0,212,255,0.1)] flex items-center justify-center">
                <div className="w-4 h-4 bg-[#00d4ff]/50 rounded-full" />
              </div>
              <p className="mt-4 text-xs text-[rgba(255,255,255,0.4)] tracking-wider uppercase font-mono">
                AWAITING TRANSMISSION
              </p>
            </div>
          )}
        </div>

        {/* Footer stats */}
        <div className="mt-4 pt-3 border-t border-[rgba(0,212,255,0.1)]">
          <div className="flex items-center justify-between text-[9px] text-[rgba(255,255,255,0.5)] font-mono">
            <span>TOTAL ENTRIES</span>
            <span>{transcript.length}</span>
          </div>
          <div className="flex items-center justify-between mt-1 text-[9px] text-[rgba(255,255,255,0.5)] font-mono">
            <span>SESSION TIME</span>
            <span>00:00:00</span>
          </div>
        </div>
      </div>

      {/* Scanline overlay */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 pointer-events-none scanline-sweep" />
      </div>
    </motion.div>
  )
}