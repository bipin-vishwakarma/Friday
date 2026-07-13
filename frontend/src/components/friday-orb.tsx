import React from 'react';
import { motion } from 'framer-motion';
import { OrbState } from '../types';

interface FridayOrbProps {
  state: OrbState;
}

const stateConfig = {
  idle: {
    color: 'rgba(0, 255, 255, 0.3)',
    pulseSpeed: 3,
    scale: 1,
    label: 'Idle',
  },
  listening: {
    color: 'rgba(0, 255, 255, 0.8)',
    pulseSpeed: 1.5,
    scale: 1.1,
    label: 'Listening',
  },
  recording: {
    color: 'rgba(255, 0, 0, 0.8)',
    pulseSpeed: 0.8,
    scale: 1.05,
    label: 'Recording',
  },
  processing: {
    color: 'rgba(255, 255, 0, 0.8)',
    pulseSpeed: 1,
    scale: 1,
    label: 'Processing',
  },
  speaking: {
    color: 'rgba(0, 255, 0, 0.8)',
    pulseSpeed: 2,
    scale: 1.1,
    label: 'Speaking',
  },
};

export const FridayOrb: React.FC<FridayOrbProps> = ({ state }) => {
  const config = stateConfig[state];

  const orbVariants = {
    idle: {
      scale: [1, 1.05, 1],
      boxShadow: [
        '0 0 30px rgba(0, 255, 255, 0.3)',
        '0 0 50px rgba(0, 255, 255, 0.5)',
        '0 0 30px rgba(0, 255, 255, 0.3)',
      ],
      transition: {
        duration: config.pulseSpeed,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    listening: {
      scale: [1, 1.15, 1],
      boxShadow: [
        '0 0 40px rgba(0, 255, 255, 0.6)',
        '0 0 80px rgba(0, 255, 255, 0.9)',
        '0 0 40px rgba(0, 255, 255, 0.6)',
      ],
      transition: {
        duration: config.pulseSpeed,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    recording: {
      scale: [1, 1.1, 1],
      boxShadow: [
        '0 0 40px rgba(255, 0, 0, 0.6)',
        '0 0 70px rgba(255, 0, 0, 0.9)',
        '0 0 40px rgba(255, 0, 0, 0.6)',
      ],
      transition: {
        duration: config.pulseSpeed,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    processing: {
      rotate: [0, 360],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'linear',
      },
    },
    speaking: {
      scale: [1, 1.12, 1],
      boxShadow: [
        '0 0 40px rgba(0, 255, 0, 0.5)',
        '0 0 70px rgba(0, 255, 0, 0.8)',
        '0 0 40px rgba(0, 255, 0, 0.5)',
      ],
      transition: {
        duration: config.pulseSpeed,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  const ringVariants = {
    idle: {
      opacity: 0,
      scale: 1,
    },
    listening: {
      opacity: [0, 0.6, 0],
      scale: [1, 1.8, 2],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeOut',
      },
    },
    recording: {
      opacity: [0, 0.5, 0],
      scale: [1, 1.5, 1.8],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeOut',
      },
    },
    processing: {
      opacity: [0.3, 0.6, 0.3],
      rotate: [0, 360],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        ease: 'linear',
      },
    },
    speaking: {
      opacity: [0, 0.4, 0],
      scale: [1, 1.6, 1.9],
      transition: {
        duration: 1.8,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen w-full">
      <div className="relative">
        {/* Outer rings for listening, recording, speaking states */}
        {(state === 'listening' || state === 'recording' || state === 'speaking') && (
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{
              width: '300px',
              height: '300px',
              border: '2px solid rgba(0, 255, 255, 0.3)',
              filter: 'blur(2px)',
            }}
            variants={ringVariants}
            animate={state}
          />
        )}

        {/* Additional ring for listening state */}
        {state === 'listening' && (
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{
              width: '300px',
              height: '300px',
              border: '1px solid rgba(0, 255, 255, 0.2)',
              filter: 'blur(4px)',
              marginTop: '-10px',
              marginLeft: '-10px',
            }}
            animate={{
              opacity: [0, 0.4, 0],
              scale: [1, 2.2, 2.5],
              transition: {
                duration: 2.5,
                repeat: Infinity,
                ease: 'easeOut',
              },
            }}
          />
        )}

        {/* Spinning rings for processing state */}
        {state === 'processing' && (
          <>
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{
                width: '320px',
                height: '320px',
                borderTop: '3px solid rgba(255, 255, 0, 0.6)',
                borderRight: '3px solid transparent',
                borderBottom: '3px solid rgba(255, 255, 0, 0.6)',
                borderLeft: '3px solid transparent',
              }}
              animate={{
                rotate: [0, 360],
                transition: {
                  duration: 1,
                  repeat: Infinity,
                  ease: 'linear',
                },
              }}
            />
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{
                width: '340px',
                height: '340px',
                borderTop: '2px solid rgba(255, 255, 0, 0.4)',
                borderRight: '2px solid transparent',
                borderBottom: '2px solid rgba(255, 255, 0, 0.4)',
                borderLeft: '2px solid transparent',
              }}
              animate={{
                rotate: [360, 0],
                transition: {
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'linear',
                },
              }}
            />
          </>
        )}

        {/* Main orb */}
        <motion.div
          className="relative rounded-full flex items-center justify-center"
          style={{
            width: '300px',
            height: '300px',
            background: 'radial-gradient(circle, rgba(0, 255, 255, 0.2) 0%, rgba(0, 100, 255, 0.1) 70%, rgba(0, 0, 50, 0.3) 100%)',
            border: '2px solid rgba(0, 255, 255, 0.5)',
            boxShadow: 'inset 0 0 50px rgba(0, 255, 255, 0.3), 0 0 30px rgba(0, 255, 255, 0.3)',
            backdropFilter: 'blur(10px)',
          }}
          variants={orbVariants}
          animate={state}
        >
          {/* Inner glow */}
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(0, 255, 255, 0.4) 0%, transparent 70%)',
              opacity: state === 'listening' ? 0.6 : 0.3,
            }}
          />
        </motion.div>
      </div>

      {/* State label */}
      <motion.div
        className="mt-8 text-cyan-400 text-xl font-mono tracking-wider"
        style={{
          textShadow: '0 0 10px rgba(0, 255, 255, 0.5)',
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {config.label}
      </motion.div>
    </div>
  );
};