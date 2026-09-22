import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Sparkles, BatteryCharging, Zap } from 'lucide-react';

export const StandaloneClock: React.FC = () => {
  const [time, setTime] = useState<string>('');
  const [date, setDate] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }));
      setDate(now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-sm px-2 flex flex-col items-center gap-2">
      {/* Clock HUD */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3 w-full flex flex-col items-center">
        <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-cyber mb-1">
          <Clock size={13} />
          <span>STANDALONE DESK CLOCK</span>
        </div>
        <div className="text-3xl font-cyber font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
          {time}
        </div>
        <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-0.5 font-medium">
          <Calendar size={11} className="text-slate-500" />
          <span>{date}</span>
        </div>
      </div>

      {/* Standalone Status Info */}
      <div className="w-full bg-slate-900/40 border border-slate-800/60 rounded-xl p-2 flex items-center justify-between text-[10px] text-slate-400">
        <div className="flex items-center gap-1">
          <Zap size={12} className="text-amber-400" />
          <span>ON-DEVICE EDGE RUNTIME</span>
        </div>
        <span className="text-cyan-400 font-cyber">PLUG USB FOR PC LINK</span>
      </div>
    </div>
  );
};
