import React, { useState, useEffect, useRef } from 'react';
import { TerminalPhase } from './phases/TerminalPhase';
import { ReactorPhase } from './phases/ReactorPhase';
import { LogoReveal } from './phases/LogoReveal';
import { AudioSync } from './audio/AudioSync';

type Phase = 'terminal' | 'reactor' | 'logo' | 'fadeout' | 'complete';

const getAudioPath = (): string => {
  try {
    if (window.require) {
      const path = window.require('path');
      const htmlDir = decodeURIComponent(
        window.location.href.replace('file://', '').replace(/\/[^/]*$/, '')
      );
      const wavPath = path.join(htmlDir, 'jarvis.wav');
      return wavPath;
    }
  } catch {}
  return './jarvis.wav';
};

const App: React.FC = () => {
  const [phase, setPhase] = useState<Phase>('terminal');
  const [audioSyncInstance, setAudioSyncInstance] = useState<AudioSync | null>(null);
  const audioRef = useRef<AudioSync | null>(null);

  useEffect(() => {
    const audioPath = getAudioPath();
    const audio = new AudioSync(audioPath);
    audioRef.current = audio;
    setAudioSyncInstance(audio);
    
    try {
      audio.play();
    } catch (e) {
      console.warn('Audio failed to play, proceeding without sound.', e);
    }

    return () => {
      audio.stop();
    };
  }, []);

  const handleTerminalComplete = () => setPhase('reactor');
  const handleReactorComplete = () => setPhase('logo');
  const handleLogoComplete = () => setPhase('complete');

  useEffect(() => {
    if (phase === 'fadeout') {
      const timer = setTimeout(() => {
        setPhase('complete');
      }, 300);
      return () => clearTimeout(timer);
    }
    
    if (phase === 'complete') {
      if (window.require) {
        try {
          const { ipcRenderer } = window.require('electron');
          ipcRenderer.send('startup-complete');
        } catch (e) {
          console.warn('Failed to send IPC message:', e);
        }
      } else {
        console.log('Startup sequence complete. Not running in Electron environment.');
      }
    }
  }, [phase]);

  const handleSkip = () => {
    if (audioRef.current) {
      audioRef.current.stop();
    }
    setPhase('fadeout');
  };

  return (
    <>
      {/* CRT Scanline & Holographic Overlays */}
      <div className="scanline-overlay" />
      <div className="crt-vignette" />

      {/* Phase 1: Terminal Boot Sequence (0s - 15s) */}
      <TerminalPhase 
        active={phase === 'terminal'} 
        onComplete={handleTerminalComplete} 
        audioSync={audioSyncInstance}
      />
      
      {/* Phase 2: 3D Holographic AI Reactor (15s - 39.5s) */}
      <ReactorPhase 
        active={phase === 'reactor'} 
        onComplete={handleReactorComplete} 
        audioSync={audioSyncInstance}
      />
      
      {/* Phase 3: AI Activation Logo & Singularity Expansion (53s - 55s) */}
      <LogoReveal 
        active={phase === 'logo'} 
        onComplete={handleLogoComplete} 
        audioSync={audioSyncInstance}
      />

      {/* Seamless Transition to Main Tactical HUD (#010409) */}
      <div 
        className={`fade-to-hud ${phase === 'fadeout' || phase === 'complete' ? 'active' : ''}`} 
      />

      {/* Skip Button */}
      {phase !== 'fadeout' && phase !== 'complete' && (
        <button className="skip-btn" onClick={handleSkip}>
          SKIP ▸
        </button>
      )}
    </>
  );
};

export default App;
