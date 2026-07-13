import React from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../../store/useStore';
import { FiSettings } from 'react-icons/fi';

export const ControlPanel: React.FC = () => {
  const { latency, mute, toggleMute } = useStore(state => ({
    latency: state.latency,
    mute: state.mute,
    toggleMute: state.toggleMute,
  }));

  const handleWake = async () => {
    try {
      await fetch('/api/v1/wake', { method: 'POST' });
    } catch (e) {
      console.error('Wake failed', e);
    }
  };

  return (
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
  );
};