import React, { useEffect, useRef } from 'react';

export type AgentState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface FluidOrbProps {
  state: AgentState;
  onClick?: () => void;
  size?: number;
}

export const FluidOrb: React.FC<FluidOrbProps> = ({ state, onClick, size = 180 }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const baseRadius = size * 0.32;

      // Color pallete based on agent state
      let color1 = 'rgba(0, 240, 255, ';     // Cyan
      let color2 = 'rgba(0, 112, 243, ';     // Blue
      let speed = 0.03;
      let waveAmp = 6;

      if (state === 'listening') {
        color1 = 'rgba(255, 183, 3, ';       // Amber
        color2 = 'rgba(251, 133, 0, ';
        speed = 0.06;
        waveAmp = 10;
      } else if (state === 'thinking') {
        color1 = 'rgba(138, 43, 226, ';      // Purple
        color2 = 'rgba(217, 70, 239, ';
        speed = 0.08;
        waveAmp = 14;
      } else if (state === 'speaking') {
        color1 = 'rgba(57, 255, 20, ';       // Neon Emerald
        color2 = 'rgba(0, 240, 255, ';
        speed = 0.05;
        waveAmp = 12;
      }

      angle += speed;

      // Draw background glow halo
      const radialGrad = ctx.createRadialGradient(
        centerX, centerY, baseRadius * 0.2,
        centerX, centerY, baseRadius * 1.5
      );
      radialGrad.addColorStop(0, `${color1}0.45)`);
      radialGrad.addColorStop(0.6, `${color2}0.15)`);
      radialGrad.addColorStop(1, 'rgba(0,0,0,0)');

      ctx.fillStyle = radialGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 1.6, 0, Math.PI * 2);
      ctx.fill();

      // Draw undulating organic fluid orb boundary
      ctx.beginPath();
      const numPoints = 64;
      for (let i = 0; i <= numPoints; i++) {
        const theta = (i / numPoints) * Math.PI * 2;
        const wave1 = Math.sin(theta * 4 + angle) * waveAmp;
        const wave2 = Math.cos(theta * 3 - angle * 1.5) * (waveAmp * 0.6);
        const r = baseRadius + wave1 + wave2;
        const x = centerX + Math.cos(theta) * r;
        const y = centerY + Math.sin(theta) * r;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();

      // Fluid gradient fill
      const orbGrad = ctx.createLinearGradient(
        centerX - baseRadius, centerY - baseRadius,
        centerX + baseRadius, centerY + baseRadius
      );
      orbGrad.addColorStop(0, `${color1}0.85)`);
      orbGrad.addColorStop(0.5, `${color2}0.65)`);
      orbGrad.addColorStop(1, `${color1}0.9)`);

      ctx.fillStyle = orbGrad;
      ctx.shadowBlur = 24;
      ctx.shadowColor = `${color1}0.9)`;
      ctx.fill();
      ctx.shadowBlur = 0; // reset

      // Inner energetic core
      const coreGrad = ctx.createRadialGradient(
        centerX - 8, centerY - 8, 2,
        centerX, centerY, baseRadius * 0.65
      );
      coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
      coreGrad.addColorStop(0.4, `${color1}0.6)`);
      coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');

      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 0.65, 0, Math.PI * 2);
      ctx.fill();

      // Orbital cyber rings
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(angle * 0.4);
      ctx.strokeStyle = `${color1}0.35)`;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([12, 16]);
      ctx.beginPath();
      ctx.ellipse(0, 0, baseRadius * 1.25, baseRadius * 0.7, Math.PI / 4, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [state, size]);

  const stateLabels: Record<AgentState, { text: string; color: string; badge: string }> = {
    idle: { text: 'FRIDAY ONLINE', color: 'text-cyan-400', badge: 'bg-cyan-500/20 border-cyan-500/40' },
    listening: { text: 'LISTENING...', color: 'text-amber-400', badge: 'bg-amber-500/20 border-amber-500/40 animate-pulse' },
    thinking: { text: 'PROCESSING...', color: 'text-purple-400', badge: 'bg-purple-500/20 border-purple-500/40 animate-pulse' },
    speaking: { text: 'TRANSMITTING', color: 'text-emerald-400', badge: 'bg-emerald-500/20 border-emerald-500/40' }
  };

  const label = stateLabels[state];

  return (
    <div className="flex flex-col items-center justify-center relative cursor-pointer active:scale-95 transition-transform" onClick={onClick}>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="touch-none"
        style={{ width: `${size}px`, height: `${size}px` }}
      />
      <div className={`mt-1 px-3 py-0.5 rounded-full border text-[11px] font-cyber tracking-widest uppercase ${label.color} ${label.badge}`}>
        {label.text}
      </div>
    </div>
  );
};
