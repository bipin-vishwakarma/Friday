import React from 'react';
import { Cpu, HardDrive } from 'lucide-react';

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

  const getMetricColor = (val: number) => {
    if (val > 85) return 'from-red-500 to-rose-600 text-red-400';
    if (val > 65) return 'from-amber-500 to-orange-500 text-amber-400';
    return 'from-cyan-400 to-blue-500 text-cyan-400';
  };

  return (
    <div className="grid grid-cols-2 gap-1.5 w-full px-1">
      {/* CPU Card */}
      <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-xl p-2 flex flex-col justify-between">
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <div className="flex items-center gap-1 font-medium">
            <Cpu size={12} className="text-cyan-400" />
            <span>CPU</span>
          </div>
          <span className="font-cyber text-slate-500 text-[9px]">{data?.cpu?.cores ?? 4}C</span>
        </div>
        <div className="my-1 flex items-baseline justify-between">
          <span className={`text-lg font-cyber font-bold leading-none ${getMetricColor(cpuPercent).split(' ')[2]}`}>
            {cpuPercent.toFixed(0)}%
          </span>
        </div>
        {/* Progress bar */}
        <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${getMetricColor(cpuPercent).split(' ')[0]} ${getMetricColor(cpuPercent).split(' ')[1]} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(5, cpuPercent))}%` }}
          />
        </div>
      </div>

      {/* RAM Card */}
      <div className="bg-slate-900/70 backdrop-blur-md border border-slate-800 rounded-xl p-2 flex flex-col justify-between">
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <div className="flex items-center gap-1 font-medium">
            <HardDrive size={12} className="text-purple-400" />
            <span>RAM</span>
          </div>
          <span className="font-cyber text-slate-500 text-[9px]">{memUsed}G</span>
        </div>
        <div className="my-1 flex items-baseline justify-between">
          <span className="text-lg font-cyber font-bold text-purple-400 leading-none">
            {memPercent.toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, memPercent))}%` }}
          />
        </div>
      </div>
    </div>
  );
};
