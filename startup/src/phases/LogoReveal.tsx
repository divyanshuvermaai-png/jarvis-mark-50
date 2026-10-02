import React, { useState, useEffect } from 'react';
import { AudioSync } from '../audio/AudioSync';

interface LogoRevealProps {
  active: boolean;
  onComplete: () => void;
  audioSync: AudioSync | null;
}

export const LogoReveal: React.FC<LogoRevealProps> = ({ active, onComplete, audioSync }) => {
  const [pulseExpanding, setPulseExpanding] = useState(false);

  useEffect(() => {
    if (!active) {
      setPulseExpanding(false);
      return;
    }

    // Single bright core point pauses briefly in complete darkness (anticipation)
    const timerPulse = setTimeout(() => {
      setPulseExpanding(true);
      if (audioSync) {
        audioSync.playResolutionTone();
      }
    }, 600);

    // Final expansion pulse reveals and bridges directly into the main JARVIS HUD
    const timerDone = setTimeout(() => {
      onComplete();
    }, 2000);

    return () => {
      clearTimeout(timerPulse);
      clearTimeout(timerDone);
    };
  }, [active, onComplete, audioSync]);

  if (!active) return null;

  return (
    <div className="interface-generation-container">
      {/* Central Singularity Point in Void */}
      <div className={`singularity-core-point ${pulseExpanding ? 'burst' : ''}`} />

      {/* Controlled Radial Pulse Expanding into the Central Reticle of the Main HUD */}
      <div className={`singularity-collapse-flare ${pulseExpanding ? 'expand' : ''}`} />
    </div>
  );
};
