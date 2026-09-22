import React from 'react';
import { Cpu, HardDrive, Wifi, BatteryCharging } from 'lucide-react';

export interface TelemetryData {
  cpu?: { percent: number; cores: number };
  memory?: { percent: number; used_gb: number; total_gb: number };
  disk?: { percent: number };
  network?: { kb_sent: number; kb_recv: number };
  battery?: { percent: number; power_plugged: boolean };
}

interface TelemetryGaugesProps {
  data: TelemetryData | null;
}

export const TelemetryGauges: React.FC<TelemetryGaugesProps> = ({ data }) => {
  const cpuPercent = data?.cpu?.percent ?? 0;
  const memPercent = data?.memory?.percent ?? 0;
  const memUsed = data?.memory?.used_gb ?? 0;
  const memTotal = data?.memory?.total_gb ?? 0;
  const diskPercent = data?.disk?.percent ?? 0;

  const getMetricColor = (val: number) => {
    if (val > 85) return 'from-red-500 to-rose-600 border-red-500/50 text-red-400';
    if (val > 65) return 'from-amber-500 to-orange-500 border-amber-500/50 text-amber-400';
    return 'from-cyan-400 to-blue-500 border-cyan-500/50 text-cyan-400';
  };

  return (
    <div className="grid grid-cols-2 gap-2 w-full max-w-sm px-2">
      {/* CPU Card */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-2.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5 font-medium">
            <Cpu size={14} className="text-cyan-400" />
            <span>CPU LOAD</span>
          </div>
          <span className="font-cyber text-slate-500 text-[10px]">{data?.cpu?.cores ?? 4}C</span>
        </div>
        <div className="my-1.5 flex items-baseline justify-between">
          <span className={`text-xl font-cyber font-bold ${getMetricColor(cpuPercent).split(' ')[3]}`}>
            {cpuPercent.toFixed(0)}%
          </span>
        </div>
        {/* Progress bar */}
        <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${getMetricColor(cpuPercent).split(' ')[0]} ${getMetricColor(cpuPercent).split(' ')[1]} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(5, cpuPercent))}%` }}
          />
        </div>
      </div>

      {/* RAM Card */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-2.5 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5 font-medium">
            <HardDrive size={14} className="text-purple-400" />
            <span>MEMORY</span>
          </div>
          <span className="font-cyber text-slate-500 text-[10px]">{memUsed}/{memTotal}GB</span>
        </div>
        <div className="my-1.5 flex items-baseline justify-between">
          <span className="text-xl font-cyber font-bold text-purple-400">
            {memPercent.toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, memPercent))}%` }}
          />
        </div>
      </div>
    </div>
  );
};
