import React, { useState, useEffect, useRef } from 'react';
import { FluidOrb, AgentState } from './components/FluidOrb';
import { TelemetryGauges, TelemetryData } from './components/TelemetryGauges';
import { QuickActions } from './components/QuickActions';
import { ChatFeed } from './components/ChatFeed';
import { Radio, ShieldCheck, RefreshCw } from 'lucide-react';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  intent?: string;
}

export const App: React.FC = () => {
  const [agentState, setAgentState] = useState<AgentState>('idle');
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<ChatMessage | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);

  // Setup WebSocket connection to backend
  useEffect(() => {
    let reconnectTimeout: any;

    const connectWs = () => {
      const host = window.location.hostname || 'localhost';
      const wsUrl = `ws://${host}:8000/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[WS] Connected to Friday backend');
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'telemetry') {
            setTelemetry(msg);
          } else if (msg.type === 'agent_state') {
            setAgentState(msg.state);
          } else if (msg.type === 'user_message') {
            setLastMessage({ sender: 'user', text: msg.text });
          } else if (msg.type === 'assistant_message') {
            setLastMessage({ sender: 'assistant', text: msg.text, intent: msg.intent });
          }
        } catch (e) {
          console.error('[WS] Parse error', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setAgentState('idle');
        reconnectTimeout = setTimeout(connectWs, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Setup Web Speech API for voice recognition on J2 / Browser
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setAgentState('listening');
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log('[STT] Recognized:', transcript);
        handleSendQuery(transcript);
      };

      recognition.onerror = (e: any) => {
        console.warn('[STT] Error:', e.error);
        setIsListening(false);
        setAgentState('idle');
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const handleToggleMic = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please type your command.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setAgentState('idle');
    } else {
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleSendQuery = (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setAgentState('thinking');
      wsRef.current.send(JSON.stringify({
        type: 'query',
        text: text,
        speak: true
      }));
    } else {
      // Fallback via HTTP REST
      const host = window.location.hostname || 'localhost';
      fetch(`http://${host}:8000/api/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, speak: true })
      }).catch(err => console.error(err));
    }
  };

  const handleExecuteAction = (action: string, params: Record<string, any> = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'action',
        action: action,
        params: params
      }));
    } else {
      const host = window.location.hostname || 'localhost';
      fetch(`http://${host}:8000/api/pc/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, params })
      }).catch(err => console.error(err));
    }
  };

  return (
    <div className="flex flex-col items-center justify-between min-h-screen h-screen w-full bg-[#080b11] text-slate-100 p-2 select-none overflow-hidden">
      {/* Top Header / Status Bar */}
      <header className="w-full max-w-sm flex items-center justify-between px-3 py-1 border-b border-slate-800/80">
        <div className="flex items-center gap-1.5">
          <span className="font-cyber font-bold text-sm tracking-wider text-cyan-400">
            FRIDAY
          </span>
          <span className="text-[10px] font-cyber text-slate-500">v2.0</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-[11px] font-cyber">
            <Radio size={12} className={isConnected ? "text-emerald-400 animate-pulse" : "text-rose-500"} />
            <span className={isConnected ? "text-emerald-400" : "text-rose-400"}>
              {isConnected ? "LINKED" : "OFFLINE"}
            </span>
          </div>

          <button 
            onClick={() => window.location.reload()}
            className="text-slate-500 hover:text-slate-300 active:rotate-180 transition-transform p-1"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </header>

      {/* Main Dynamic View Area */}
      <main className="flex-1 w-full max-w-sm flex flex-col items-center justify-evenly py-1 gap-2 overflow-y-auto">
        {/* Animated Fluid Orb */}
        <FluidOrb 
          state={agentState} 
          onClick={handleToggleMic} 
          size={160} 
        />

        {/* Real-time PC Telemetry Dials */}
        <TelemetryGauges data={telemetry} />

        {/* Quick Action Touch Tiles */}
        <QuickActions onAction={handleExecuteAction} />
      </main>

      {/* Bottom Chat and Voice Bar */}
      <footer className="w-full max-w-sm pb-1 pt-0.5">
        <ChatFeed 
          lastMessage={lastMessage} 
          onSend={handleSendQuery} 
          isListening={isListening} 
          onToggleMic={handleToggleMic} 
        />
      </footer>
    </div>
  );
};
