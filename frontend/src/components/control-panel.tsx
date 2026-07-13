import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '../../store/useStore';
import { FiSettings, FiSmartphone } from 'react-icons/fi';

export const ControlPanel: React.FC = () => {
  const { latency, mute, toggleMute } = useStore(state => ({
    latency: state.latency,
    mute: state.mute,
    toggleMute: state.toggleMute,
  }));

  const [qrOpen, setQrOpen] = useState(false);
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [qrLoading, setQrLoading] = useState(false);

  const handleWake = async () => {
    try {
      await fetch('/api/v1/wake', { method: 'POST' });
    } catch (e) {
      console.error('Wake failed', e);
    }
  };

  const handleQR = async () => {
    if (qrOpen) { setQrOpen(false); return; }
    setQrOpen(true);
    setQrLoading(true);
    try {
      const res = await fetch('/api/v1/adb/qr');
      const blob = await res.blob();
      setQrSrc(URL.createObjectURL(blob));
    } catch (e) {
      console.error('QR fetch failed', e);
    } finally {
      setQrLoading(false);
    }
  };

  return (
    <>
      <motion.div
        className="fixed bottom-0 left-0 right-0 p-4 flex items-center justify-center gap-6 bg-black/70 backdrop-blur-md border-t border-cyan-500/30"
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        transition={{ type: 'spring', stiffness: 300 }}
      >
        <button
          onClick={handleWake}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md shadow-lg border border-cyan-400/30"
        >
          Wake Manually
        </button>

        <button
          onClick={handleQR}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md shadow-lg border border-cyan-400/30 flex items-center gap-2"
        >
          <FiSmartphone size={16} />
          QR Pair
        </button>

        <button
          onClick={toggleMute}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md shadow-lg border border-cyan-400/30"
        >
          {mute ? 'Unmute' : 'Mute'}
        </button>

        <button className="p-2 text-cyan-300 hover:text-cyan-200">
          <FiSettings size={24} />
        </button>

        <div className="text-cyan-400 text-sm ml-4">
          Latency: {latency ? `${latency}ms` : '--'}
        </div>
      </motion.div>

      <AnimatePresence>
        {qrOpen && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setQrOpen(false)}
          >
            <motion.div
              className="bg-gray-900 border border-cyan-500/50 rounded-2xl p-8 shadow-2xl shadow-cyan-500/20 flex flex-col items-center gap-4"
              initial={{ scale: 0.8, y: 30 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 30 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-cyan-300 text-lg font-semibold tracking-wide">
                Scan to Pair Device
              </h3>
              {qrLoading ? (
                <div className="w-48 h-48 flex items-center justify-center text-cyan-400 animate-pulse">
                  Generating QR...
                </div>
              ) : qrSrc ? (
                <img
                  src={qrSrc}
                  alt="ADB QR Code"
                  className="w-48 h-48 rounded-lg bg-white p-2"
                />
              ) : (
                <div className="w-48 h-48 flex items-center justify-center text-red-400">
                  Failed to load
                </div>
              )}
              <p className="text-cyan-500/70 text-xs text-center max-w-64">
                Point your phone's camera at this code to connect via ADB over WiFi
              </p>
              <button
                onClick={() => setQrOpen(false)}
                className="mt-2 px-4 py-1.5 text-sm text-cyan-300 border border-cyan-500/30 rounded-lg hover:bg-cyan-500/10"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};