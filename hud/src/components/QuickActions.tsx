import React from 'react';
import { 
  Volume2, VolumeX, Volume1, 
  Play, SkipForward, 
  Lock, Moon, Camera, 
  Globe, Code2, Music, Terminal
} from 'lucide-react';

interface QuickActionsProps {
  onAction: (action: string, params?: Record<string, any>) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onAction }) => {
  const actions = [
    { id: 'vol_mute', label: 'Mute', icon: VolumeX, color: 'hover:border-rose-500/50 text-rose-400', action: 'mute_volume' },
    { id: 'vol_up', label: 'Vol +', icon: Volume2, color: 'hover:border-cyan-500/50 text-cyan-400', action: 'volume_up' },
    { id: 'vol_down', label: 'Vol -', icon: Volume1, color: 'hover:border-blue-500/50 text-blue-400', action: 'volume_down' },
    { id: 'play_pause', label: 'Play/Pause', icon: Play, color: 'hover:border-emerald-500/50 text-emerald-400', action: 'media_play_pause' },
    { id: 'next_track', label: 'Next', icon: SkipForward, color: 'hover:border-amber-500/50 text-amber-400', action: 'media_next' },
    { id: 'lock', label: 'Lock PC', icon: Lock, color: 'hover:border-purple-500/50 text-purple-400', action: 'lock_workstation' },
    { id: 'screenshot', label: 'Capture', icon: Camera, color: 'hover:border-cyan-400 text-cyan-300', action: 'take_screenshot' },
    { id: 'app_chrome', label: 'Chrome', icon: Globe, color: 'hover:border-yellow-400 text-yellow-400', action: 'open_application', params: { app: 'chrome' } },
    { id: 'app_code', label: 'VS Code', icon: Code2, color: 'hover:border-blue-400 text-blue-400', action: 'open_application', params: { app: 'code' } },
    { id: 'app_spotify', label: 'Spotify', icon: Music, color: 'hover:border-green-400 text-green-400', action: 'open_application', params: { app: 'spotify' } },
    { id: 'app_term', label: 'Terminal', icon: Terminal, color: 'hover:border-slate-300 text-slate-300', action: 'open_application', params: { app: 'terminal' } },
    { id: 'sleep', label: 'Sleep', icon: Moon, color: 'hover:border-indigo-400 text-indigo-400', action: 'sleep_pc' },
  ];

  return (
    <div className="w-full max-w-sm px-2">
      <div className="text-[10px] font-cyber tracking-widest text-slate-500 mb-1.5 uppercase flex items-center justify-between">
        <span>QUICK CONTROLS</span>
        <span className="text-[9px] text-cyan-500/80">TAP TO TRIGGER</span>
      </div>
      <div className="grid grid-cols-4 gap-1.5">
        {actions.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onAction(item.action, item.params)}
              className={`flex flex-col items-center justify-center p-2 rounded-xl bg-slate-900/70 border border-slate-800/80 active:scale-90 active:bg-slate-800 transition-all ${item.color}`}
            >
              <Icon size={18} />
              <span className="text-[10px] font-medium tracking-tight mt-1 text-slate-300">
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
