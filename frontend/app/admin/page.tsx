"use client";

import React from "react";
import { Inter } from "next/font/google";
import { motion } from "framer-motion";
import { Settings as SettingsIcon, Smartphone } from "lucide-react";

import StatusCard from "@/components/StatusCard";
import Controls from "@/components/Controls";
import VoiceLog from "@/components/VoiceLog";
import VisionFeed from "@/components/VisionFeed";
import SettingsPanel from "@/components/Settings";
import { useStore } from "@/store/useStore";
import { useEventSocket, startHealthPoller } from "@/lib/api";

const inter = Inter({ subsets: ["latin"] });

function Header() {
  const setSettingsOpen = useStore((s) => s.setSettingsOpen);
  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-3">
      <div className="flex items-center gap-3">
        <div className="orb-glow relative flex h-8 w-8 items-center justify-center rounded-full bg-primary/20">
          <span className="relative text-sm font-black text-primary">F</span>
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-foreground">
            FRIDAY<span className="text-primary"> AI</span>
          </h1>
          <p className="text-[10px] text-muted-foreground">
            Admin Control Panel
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-1.5 rounded-md bg-secondary/30 px-3 py-1.5 text-xs text-muted-foreground sm:flex">
          <Smartphone className="h-3.5 w-3.5" />
          Desk Buddy: /buddy
        </div>
        <button
          onClick={() => setSettingsOpen(true)}
          className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <SettingsIcon className="h-3.5 w-3.5" />
          Settings
        </button>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border px-6 py-2 text-[10px] text-muted-foreground">
      FRIDAY AI Admin Panel &middot; Free local stack + Samsung J2 Core browser
    </footer>
  );
}

export default function AdminDashboard() {
  useEventSocket();
  React.useEffect(() => {
    startHealthPoller();
  }, []);

  return (
    <div className={`${inter.className} flex min-h-screen flex-col bg-background bg-grid text-foreground`}>
      <Header />

      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mx-auto grid max-w-7xl grid-cols-1 gap-4 lg:grid-cols-3"
        >
          <div className="space-y-4 lg:col-span-2">
            <StatusCard />
            <Controls />
            <VisionFeed />
          </div>

          <div className="lg:col-span-1">
            <VoiceLog />
          </div>
        </motion.div>
      </main>

      <Footer />
      <SettingsPanel />
    </div>
  );
}