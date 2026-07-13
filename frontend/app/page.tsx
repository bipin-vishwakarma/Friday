"use client";

import React from "react";
import Link from "next/link";
import { Inter } from "next/font/google";
import { motion } from "framer-motion";
import { Cpu, Smartphone, ArrowRight, Shield, Wifi, Activity } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  return (
    <div className={`${inter.className} min-h-screen bg-gradient-to-br from-background to-secondary/20 flex items-center justify-center p-4`}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-6xl"
      >
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center gap-3 mb-6">
            <div className="orb-glow relative flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
              <span className="text-lg font-black text-primary">F</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold">
              <span className="text-foreground">FRIDAY</span>
              <span className="text-primary"> AI</span>
            </h1>
          </div>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-4">
            Fully free local stack with rules-only brain and Samsung J2 Core desk buddy integration
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30">
            <Shield className="h-4 w-4 text-primary" />
            <span className="text-sm text-primary">Gemini, Groq, OpenAI NOT required</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="group"
          >
            <Link href="/admin">
              <div className="block h-full p-8 rounded-2xl border border-border bg-card/50 hover:bg-card/80 hover:border-primary/40 transition-all duration-300 cursor-pointer group-hover:shadow-lg group-hover:shadow-primary/10">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/20">
                      <Cpu className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-foreground group-hover:text-primary transition-colors">
                        Admin Panel
                      </h2>
                      <p className="text-sm text-muted-foreground">
                        Desktop control center
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-muted-foreground">WebSocket Connected</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-blue-500" />
                    <span className="text-muted-foreground">Voice Pipeline Active</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-purple-500" />
                    <span className="text-muted-foreground">Rules-Only Brain</span>
                  </div>
                  <div className="pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground">
                      Control voice, view vision, manage settings, and monitor system status.
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="group"
          >
            <Link href="/buddy">
              <div className="block h-full p-8 rounded-2xl border border-border bg-card/50 hover:bg-card/80 hover:border-primary/40 transition-all duration-300 cursor-pointer group-hover:shadow-lg group-hover:shadow-primary/10">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20">
                      <Smartphone className="h-6 w-6 text-emerald-400" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-foreground group-hover:text-emerald-400 transition-colors">
                        Desk Buddy
                      </h2>
                      <p className="text-sm text-muted-foreground">
                        Samsung J2 Core (Android Chrome)
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-emerald-400 transition-colors" />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-orange-500" />
                    <span className="text-muted-foreground">Browser WebRTC Camera</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-teal-500" />
                    <span className="text-muted-foreground">ADB Wi-Fi Control</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="h-2 w-2 rounded-full bg-cyan-500" />
                    <span className="text-muted-foreground">Local Analysis (PC)</span>
                  </div>
                  <div className="pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground">
                      Mobile-friendly UI for old Android hardware with big touch controls and live camera feed.
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Wifi className="h-4 w-4" />
              <span>Free Stack</span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span>Rules-Only Brain</span>
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span>No Cloud Keys Needed</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
