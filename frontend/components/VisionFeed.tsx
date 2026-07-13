"use client";

import React, { useEffect, useRef, useCallback, useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useStore } from "@/store/useStore";
import { fetchVisionFrame } from "@/lib/api";

/**
 * VisionFeed shows the latest camera frame from the backend with face-box
 * overlays.  It polls /api/v1/vision/frame at ~10 FPS when vision is running,
 * and draws bounding boxes over the image via a <canvas> overlay.
 */
export default function VisionFeed() {
  const visionRunning = useStore((s) => s.visionRunning);
  const visionFrame = useStore((s) => s.visionFrame);
  const setVisionRunning = useStore((s) => s.setVisionRunning);
  const setVisionFrame = useStore((s) => s.setVisionFrame);

  const imgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameUrl = useRef<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [fps, setFps] = useState(0);

  // -- Poll for frames -------------------------------------------------------
  const pollFrame = useCallback(async () => {
    const url = await fetchVisionFrame();
    if (url) {
      // Revoke old blob URL to avoid memory leak
      if (frameUrl.current) URL.revokeObjectURL(frameUrl.current);
      frameUrl.current = url;

      if (imgRef.current) {
        imgRef.current.src = url;
      }
    }
  }, []);

  useEffect(() => {
    if (visionRunning) {
      pollRef.current = setInterval(pollFrame, 100); // ~10 FPS
      let count = 0;
      const fpsTimer = setInterval(() => {
        setFps(count);
        count = 0;
      }, 1000);
      // Increment count on each poll
      const origPoll = pollFrame;
      // We use the interval ref to track; FPS counting is approximate
      return () => {
        if (pollRef.current) clearInterval(pollRef.current);
        clearInterval(fpsTimer);
      };
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, [visionRunning, pollFrame]);

  // -- Draw face boxes on canvas ---------------------------------------------
  useEffect(() => {
    if (!visionFrame || !canvasRef.current || !imgRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = imgRef.current;

    // Wait for the image to have dimensions
    const draw = () => {
      canvas.width = img.naturalWidth || img.width;
      canvas.height = img.naturalHeight || img.height;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const face of visionFrame.faces) {
        const scaleX = canvas.width / 640; // backend default width
        const scaleY = canvas.height / 480;
        const x = face.x * scaleX;
        const y = face.y * scaleY;
        const w = face.w * scaleX;
        const h = face.h * scaleY;

        // Glow
        ctx.shadowColor = "rgba(56, 189, 248, 0.6)";
        ctx.shadowBlur = 12;
        ctx.strokeStyle = "rgba(56, 189, 248, 0.9)";
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);

        // Corner accents
        const cornerLen = Math.min(w, h) * 0.2;
        ctx.lineWidth = 3;
        ctx.shadowBlur = 0;
        ctx.strokeStyle = "#38bdf8";
        // Top-left
        ctx.beginPath(); ctx.moveTo(x, y + cornerLen); ctx.lineTo(x, y); ctx.lineTo(x + cornerLen, y); ctx.stroke();
        // Top-right
        ctx.beginPath(); ctx.moveTo(x + w - cornerLen, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + cornerLen); ctx.stroke();
        // Bottom-left
        ctx.beginPath(); ctx.moveTo(x, y + h - cornerLen); ctx.lineTo(x, y + h); ctx.lineTo(x + cornerLen, y + h); ctx.stroke();
        // Bottom-right
        ctx.beginPath(); ctx.moveTo(x + w - cornerLen, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - cornerLen); ctx.stroke();

        // Label
        ctx.font = "12px 'Inter', sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.shadowBlur = 4;
        ctx.fillText("FACE", x + 4, y - 6);
      }
    };

    if (img.complete) draw();
    else img.onload = draw;
  }, [visionFrame]);

  const toggleVision = async () => {
    if (visionRunning) {
      setVisionRunning(false);
    } else {
      setVisionRunning(true);
    }
  };

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          {visionRunning ? (
            <Eye className="h-4 w-4 text-primary" />
          ) : (
            <EyeOff className="h-4 w-4 text-muted-foreground" />
          )}
          Vision Feed
        </CardTitle>
        <div className="flex items-center gap-2">
          {visionRunning && (
            <Badge variant="success">{fps > 0 ? `${fps} FPS` : "LIVE"}</Badge>
          )}
          <Button
            variant={visionRunning ? "destructive" : "default"}
            size="sm"
            onClick={toggleVision}
          >
            {visionRunning ? "Stop" : "Start"}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="relative">
        <div className="relative aspect-video w-full overflow-hidden rounded-md border border-border bg-black/40">
          {/* Hidden image element that receives the MJPEG/JPEG frames */}
          <img
            ref={imgRef}
            alt="Vision feed"
            className="absolute inset-0 h-full w-full object-contain opacity-0 transition-opacity duration-300"
            onLoad={(e) => {
              (e.currentTarget as HTMLImageElement).style.opacity = "1";
            }}
          />

          {/* Canvas overlay for face boxes */}
          <canvas
            ref={canvasRef}
            className="absolute inset-0 h-full w-full object-contain"
          />

          {/* Empty state */}
          {!visionRunning && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-muted-foreground">
              <EyeOff className="h-8 w-8 opacity-40" />
              <p className="text-xs">Vision system inactive</p>
            </div>
          )}

          {/* Scanline overlay when live */}
          {visionRunning && (
            <div className="pointer-events-none absolute inset-0 scanline" />
          )}
        </div>

        {/* Frame metadata */}
        {visionFrame && (
          <div className="mt-2 flex items-center gap-3 text-[10px] text-muted-foreground">
            <span>Frame #{visionFrame.frameId}</span>
            <span>{visionFrame.faces.length} face(s)</span>
            {visionFrame.text && <span>OCR: {visionFrame.text}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
