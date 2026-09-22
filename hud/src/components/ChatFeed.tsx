import React, { useState } from 'react';
import { Send, Mic, MicOff, MessageSquare } from 'lucide-react';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  intent?: string;
}

interface ChatFeedProps {
  lastMessage: ChatMessage | null;
  onSend: (text: string) => void;
  isListening: boolean;
  onToggleMic: () => void;
}

export const ChatFeed: React.FC<ChatFeedProps> = ({ lastMessage, onSend, isListening, onToggleMic }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <div className="w-full max-w-sm px-2 flex flex-col gap-2">
      {/* Response Box */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-xl p-2.5 min-h-[58px] flex items-start gap-2">
        <MessageSquare size={16} className="text-cyan-400 shrink-0 mt-0.5" />
        <div className="flex-1 overflow-hidden">
          {lastMessage ? (
            <div>
              <div className="text-[10px] font-cyber text-slate-500 uppercase tracking-wider mb-0.5">
                {lastMessage.sender === 'assistant' ? 'FRIDAY' : 'YOU'} {lastMessage.intent ? `// ${lastMessage.intent}` : ''}
              </div>
              <p className="text-xs text-slate-200 leading-snug line-clamp-3">
                {lastMessage.text}
              </p>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              "Hey Friday, set volume to 50" or tap the orb...
            </p>
          )}
        </div>
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSubmit} className="flex items-center gap-1.5 w-full">
        <button
          type="button"
          onClick={onToggleMic}
          className={`p-2.5 rounded-xl border flex items-center justify-center shrink-0 active:scale-90 transition-all ${
            isListening 
              ? 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse' 
              : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-cyan-400'
          }`}
        >
          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
        </button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Friday or type command..."
          className="flex-1 bg-slate-900/80 border border-slate-800 text-xs rounded-xl px-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
        />

        <button
          type="submit"
          disabled={!input.trim()}
          className="p-2.5 rounded-xl bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 disabled:opacity-40 shrink-0 active:scale-90 transition-all"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
};
