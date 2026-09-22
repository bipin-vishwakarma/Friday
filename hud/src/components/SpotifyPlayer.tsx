import React from 'react';
import { Music2, Play, Pause, SkipForward, SkipBack } from 'lucide-react';

export interface MediaData {
  active: boolean;
  title: string;
  artist: string;
  album?: string;
  status: 'playing' | 'paused' | 'stopped' | 'unknown';
}

interface SpotifyPlayerProps {
  media: MediaData | null;
  onAction: (action: string) => void;
}

export const SpotifyPlayer: React.FC<SpotifyPlayerProps> = ({ media, onAction }) => {
  const isPlaying = media?.status === 'playing';
  const hasTrack = Boolean(media?.title && media.title !== 'Unknown Track');

  return (
    <div className="w-full px-1">
      <div className="bg-gradient-to-r from-emerald-950/50 via-slate-900/90 to-slate-900/90 backdrop-blur-md border border-emerald-500/40 rounded-xl p-2 flex items-center justify-between gap-1.5 shadow-md">
        {/* Track Icon & Info */}
        <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0">
            <Music2 size={16} className={isPlaying ? "text-emerald-400 animate-bounce" : "text-emerald-500/70"} />
          </div>

          <div className="min-w-0 flex-1 overflow-hidden">
            <div className="flex items-center gap-1">
              <span className="text-[8px] font-cyber tracking-widest text-emerald-400 font-bold uppercase truncate">
                {isPlaying ? "PLAYING" : "PAUSED"}
              </span>
              {isPlaying && (
                <div className="flex items-end gap-0.5 h-2">
                  <span className="w-0.5 h-full bg-emerald-400 animate-pulse" />
                  <span className="w-0.5 h-2/3 bg-emerald-400 animate-pulse delay-75" />
                  <span className="w-0.5 h-4/5 bg-emerald-400 animate-pulse delay-150" />
                </div>
              )}
            </div>

            <p className="text-[11px] font-semibold text-slate-100 truncate leading-none mt-0.5">
              {hasTrack ? media?.title : "No active track"}
            </p>
            <p className="text-[9px] text-slate-400 truncate leading-none mt-0.5">
              {hasTrack ? media?.artist : "Play media on PC"}
            </p>
          </div>
        </div>

        {/* Media Controls */}
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            onClick={() => onAction('media_prev')}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 active:scale-90 transition-transform"
            title="Previous Track"
          >
            <SkipBack size={13} />
          </button>

          <button
            onClick={() => onAction('media_play_pause')}
            className="p-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 active:scale-90 transition-transform"
            title="Play/Pause"
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
          </button>

          <button
            onClick={() => onAction('media_next')}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 active:scale-90 transition-transform"
            title="Next Track"
          >
            <SkipForward size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};
