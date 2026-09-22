import React, { useState, useEffect, useRef } from 'react';
import { FluidOrb, AgentState } from './components/FluidOrb';
import { TelemetryGauges, TelemetryData } from './components/TelemetryGauges';
import { SpotifyPlayer, MediaData } from './components/SpotifyPlayer';
import { QuickActions } from './components/QuickActions';
import { ChatFeed } from './components/ChatFeed';
import { StandaloneClock } from './components/StandaloneClock';
import { Zap, RefreshCw, Layers } from 'lucide-react';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  intent?: string;
}

export const App: React.FC = () => {
  const [agentState, setAgentState] = useState<AgentState>('idle');
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [media, setMedia] = useState<MediaData | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<ChatMessage | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isLandscape, setIsLandscape] = useState<boolean>(window.innerWidth > window.innerHeight);

  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);

  // Monitor orientation changes
  useEffect(() => {
    const handleResize = () => {
      setIsLandscape(window.innerWidth > window.innerHeight);
    };
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  // Setup WebSocket connection to backend
  useEffect(() => {
    let reconnectTimeout: any;

    const connectWs = () => {
      const host = window.location.hostname || 'localhost';
      const wsUrl = `ws://${host}:8000/ws`;

      try {
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
          console.log('[WS] Handshake established! Supercharged PC mode active.');
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'telemetry') {
              setTelemetry(msg);
            } else if (msg.type === 'media') {
              setMedia(msg.data);
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
      } catch (err) {
        reconnectTimeout = setTimeout(connectWs, 2000);
      }
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Web Speech API for voice recognition on Android
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
      alert('Voice typing is not active in this mode. Type your command below.');
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
      // Local Standalone mode fallback
      setLastMessage({ sender: 'user', text });
      setTimeout(() => {
        setLastMessage({
          sender: 'assistant',
          text: `[Offline Standalone] "${text}" noted. Connect PC for full Laya & Groq AI automation.`,
          intent: 'standalone_edge'
        });
      }, 250);
    }
  };

  const handleExecuteAction = (action: string, params: Record<string, any> = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'action',
        action: action,
        params: params
      }));
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#080b11] text-slate-100 p-2 select-none overflow-hidden justify-between">
      {/* Top Status Header */}
      <header className="w-full flex items-center justify-between px-3 py-1 border-b border-slate-800/80 shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="font-cyber font-bold text-sm tracking-wider text-cyan-400">
            FRIDAY
          </span>
          <span className="text-[10px] font-cyber text-slate-500">v2.0</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-[10px] font-cyber">
            {isConnected ? (
              <>
                <Zap size={11} className="text-emerald-400 animate-pulse" />
                <span className="text-emerald-400 font-bold tracking-wider">SUPERCHARGED // PC LINKED</span>
              </>
            ) : (
              <>
                <Layers size={11} className="text-cyan-400" />
                <span className="text-cyan-400 font-medium tracking-wider">STANDALONE EDGE</span>
              </>
            )}
          </div>

          <button 
            onClick={() => window.location.reload()}
            className="text-slate-500 hover:text-slate-300 active:rotate-180 transition-transform p-1"
          >
            <RefreshCw size={11} />
          </button>
        </div>
      </header>

      {/* Main Dynamic Workspace - Responsive for Landscape and Portrait */}
      <div className={`flex-1 flex ${isLandscape ? 'flex-row items-center justify-between gap-3 overflow-hidden py-1' : 'flex-col items-center justify-evenly py-1 gap-2 overflow-y-auto'}`}>
        {/* Left Section in Landscape, Top in Portrait */}
        <div className={`flex flex-col items-center justify-center ${isLandscape ? 'w-1/2 h-full justify-evenly' : 'w-full gap-2'}`}>
          <FluidOrb 
            state={agentState} 
            onClick={handleToggleMic} 
            size={isLandscape ? 130 : 160} 
          />

          <ChatFeed 
            lastMessage={lastMessage} 
            onSend={handleSendQuery} 
            isListening={isListening} 
            onToggleMic={handleToggleMic} 
          />
        </div>

        {/* Right Section in Landscape, Bottom in Portrait */}
        <div className={`flex flex-col items-center justify-center ${isLandscape ? 'w-1/2 h-full justify-evenly gap-2 overflow-y-auto' : 'w-full gap-2'}`}>
          {isConnected ? (
            <>
              {/* Live Spotify & Windows Media Session */}
              <SpotifyPlayer media={media} onAction={handleExecuteAction} />

              {/* Real-time PC Hardware Telemetry */}
              <TelemetryGauges data={telemetry} />

              {/* Quick Touch Controls */}
              <QuickActions onAction={handleExecuteAction} />
            </>
          ) : (
            <>
              {/* Standalone Desk Clock & Local Ambient Status */}
              <StandaloneClock />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
