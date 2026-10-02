import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactorScene, { ReactorSubPhase } from '../three/ReactorScene';
import { AudioSync } from '../audio/AudioSync';

interface ReactorPhaseProps {
  active: boolean;
  onComplete: () => void;
  audioSync: AudioSync | null;
}

export const ReactorPhase: React.FC<ReactorPhaseProps> = ({ active, onComplete, audioSync }) => {
  const [subPhase, setSubPhase] = useState<ReactorSubPhase>('materialization');
  const [visible, setVisible] = useState(false);
  const [showFlash, setShowFlash] = useState(false);
  const [fluxDensity, setFluxDensity] = useState('0.00');
  const [outputGJ, setOutputGJ] = useState('0.00');
  const [solenoidCount, setSolenoidCount] = useState(0);
  const [barWidth, setBarWidth] = useState(0);
  const tickIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [titleChars, setTitleChars] = useState(0);

  useEffect(() => {
    if (!active) {
      setVisible(false);
      setSubPhase('materialization');
      return;
    }

    setVisible(true);
    setSubPhase('materialization');

    // Ambient sub-bass drone as the core point materializes (11.8s in overall sequence)
    if (audioSync) {
      audioSync.playSubDrone();
      audioSync.playReactorHum();
    }

    // ── Audio Beat-Synced Milestones (relative to Reactor start at 11.2s of jarvis.wav) ──

    // At 3.05s (Audio 14.25s - Beat 1 Riser Impact): 10 Radial CNC Titanium Spokes lock in
    const tAssembly = setTimeout(() => {
      setSubPhase('assembly');
    }, 3050);

    // At 6.80s (Audio 18.00s - Beat 2 MASSIVE BEAT DROP): 10 Copper-Wound Solenoids slam in
    const tScan = setTimeout(() => {
      setSubPhase('scanning');
      if (audioSync) {
        audioSync.surgeReactorHum(0.18);
        audioSync.playResonancePing();
      }
    }, 6800);

    // At 13.05s (Audio 24.25s - Beat 5 Heavy Impact): Borosilicate Quartz Dome seals down
    const tSync = setTimeout(() => {
      setSubPhase('synchronization');
    }, 13050);

    // At 19.05s (Audio 30.25s - Beat 7 THE CLIMAX ACTIVATION BLAST): Full Iron Man Arc Flash
    const tActivation = setTimeout(() => {
      setSubPhase('activation');
      if (audioSync) {
        audioSync.surgeReactorHum(0.25);
        audioSync.playLFEThud();
      }
      // Trigger screen flash 250ms after activation starts
      setTimeout(() => setShowFlash(true), 250);
      setTimeout(() => setShowFlash(false), 1100);
    }, 19050);

    // At 20.20s (Audio 31.4s): Inward collapse into quantum singularity
    const tCollapse = setTimeout(() => {
      setSubPhase('collapse');
      if (audioSync) audioSync.stopReactorHum();
    }, 20200);

    // At 21.20s (Audio 32.4s): Hand-off to Singularity Expansion (LogoReveal)
    const tComplete = setTimeout(() => {
      onComplete();
    }, 21200);

    return () => {
      clearTimeout(tAssembly);
      clearTimeout(tScan);
      clearTimeout(tSync);
      clearTimeout(tActivation);
      clearTimeout(tCollapse);
      clearTimeout(tComplete);
    };
  }, [active, onComplete, audioSync]);

  // Live animated HUD counters synced to reactor sub-phases
  useEffect(() => {
    if (tickIntervalRef.current) clearInterval(tickIntervalRef.current);

    if (subPhase === 'materialization') {
      let tick = 0;
      tickIntervalRef.current = setInterval(() => {
        tick++;
        setFluxDensity((tick * 0.22).toFixed(2));
        setOutputGJ((tick * 0.15).toFixed(2));
        setBarWidth(Math.min(tick * 3, 25));
      }, 150);
    } else if (subPhase === 'assembly') {
      setFluxDensity('1.45');
      setOutputGJ('0.82');
      setBarWidth(35);
    } else if (subPhase === 'scanning') {
      // Solenoids slam in one by one
      let coil = 0;
      tickIntervalRef.current = setInterval(() => {
        coil++;
        setSolenoidCount(coil);
        setBarWidth(35 + coil * 4);
        if (coil >= 10) {
          if (tickIntervalRef.current) clearInterval(tickIntervalRef.current);
        }
      }, 180);
      setFluxDensity('2.88');
      setOutputGJ('1.76');
    } else if (subPhase === 'synchronization') {
      setSolenoidCount(10);
      setFluxDensity('4.12');
      setOutputGJ('2.65');
      setBarWidth(82);
    } else if (subPhase === 'activation') {
      setSolenoidCount(10);
      setFluxDensity('4.82');
      setOutputGJ('3.24');
      setBarWidth(98);
    }

    return () => {
      if (tickIntervalRef.current) clearInterval(tickIntervalRef.current);
    };
  }, [subPhase]);

  // Micro-flicker on numeric values
  useEffect(() => {
    if (!visible) return;
    const flickerInterval = setInterval(() => {
      setFluxDensity(prev => {
        const base = parseFloat(prev);
        if (isNaN(base)) return prev;
        return (base + (Math.random() - 0.5) * 0.02).toFixed(2);
      });
    }, 250);
    return () => clearInterval(flickerInterval);
  }, [visible]);

  // Cinematic character-by-character title assembly
  useEffect(() => {
    if (subPhase !== 'activation') {
      setTitleChars(0);
      return;
    }
    const fullTitle = 'J.A.R.V.I.S.';
    let charIdx = 0;
    const interval = setInterval(() => {
      charIdx++;
      setTitleChars(charIdx);
      if (charIdx >= fullTitle.length) clearInterval(interval);
    }, 55);
    return () => clearInterval(interval);
  }, [subPhase]);

  return (
    <div className={`reactor-container ${visible ? 'active' : ''}`}>
      {visible && (
        <>
          <ReactorScene 
            phase={subPhase} 
            audioSync={audioSync}
            onLatchSound={() => audioSync?.playMechanicalLatch()}
            onScanSound={() => audioSync?.playScanSweep()}
            onSyncSound={() => audioSync?.playSyncChime()}
            onShockwaveSound={() => audioSync?.playShockwave()}
            onRiserSound={() => audioSync?.playRisingChord()}
          />

          {/* Marvel Studios / Cantina Creative Tier FUI HUD Telemetry */}
          <div className="reactor-hud-overlay">
            <div className="hud-corner-tl">
              <div className="hud-brand">DIVYANSHU INDUSTRIES // MARK VII CORE</div>
              <div className="hud-data-row">
                <span className="hud-indicator-dot" />
                <span className="hud-val">FLUX DENSITY: {fluxDensity} T // {subPhase === 'activation' ? 'STABLE' : 'CALIBRATING'}</span>
              </div>
              <div className="hud-sub">THERMAL LOAD: 294 K // CRYOGENIC NOMINAL</div>
            </div>

            <div className="hud-corner-tr">
              <div className="hud-label">PALLADIUM ISOTOPE: 106-PD</div>
              <div className="hud-val">OUTPUT: {outputGJ} GJ/s [{barWidth}%]</div>
              <div className="hud-indicator-bar"><span className="hud-bar-fill" style={{ width: `${barWidth}%` }} /></div>
              <div className="hud-sub">CARRIER FREQ: 48.24 MHz</div>
            </div>

            <div className="hud-corner-bl">
              <div className="hud-label">CONTAINMENT MATRIX: CLOSED LOOP</div>
              <div className="hud-val">{solenoidCount}/10 SOLENOIDS {solenoidCount === 10 ? 'SYNCHRONIZED' : 'LOCKING...'}</div>
              <div className="hud-sub">TOROIDAL INDUCTANCE: 12.8 mH</div>
            </div>

            <div className="hud-corner-br">
              <div className="hud-label">AUTHORIZED OPERATOR</div>
              <div className="hud-val">DIVYANSHU VERMA // ALPHA PRIME</div>
              <div className="hud-sub">LOCAL MACHINE: APPLE M5 (10-CORE)</div>
            </div>
          </div>

          {/* Cinematic Screen Flash on Activation Blast */}
          <AnimatePresence>
            {showFlash && (
              <>
                <motion.div
                  key="white-flash"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.85 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.08, exit: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } }}
                  style={{
                    position: 'fixed',
                    inset: 0,
                    background: '#ffffff',
                    zIndex: 100,
                    pointerEvents: 'none',
                  }}
                />
                <motion.div
                  key="cyan-flash"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.3 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: 0.1, duration: 0.06, exit: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }}
                  style={{
                    position: 'fixed',
                    inset: 0,
                    background: '#00f5ff',
                    zIndex: 99,
                    pointerEvents: 'none',
                  }}
                />
              </>
            )}
          </AnimatePresence>

          {/* Clean Activation Badge: Positioned below the reactor so it never covers the core */}
          <AnimatePresence>
            {subPhase === 'activation' && (
              <motion.div
                initial={{ opacity: 0, y: 25, scale: 0.92 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, filter: 'blur(12px)' }}
                transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                className="activation-badge-container"
              >
                <div className="divyanshu-badge-brand">DIVYANSHU INDUSTRIES // AI PROTOCOL</div>
                <div className="activation-title">
                  {'J.A.R.V.I.S.'.split('').map((char, i) => (
                    <span
                      key={i}
                      style={{
                        opacity: i < titleChars ? 1 : 0,
                        transition: 'opacity 0.08s',
                        textShadow: i === titleChars - 1 ? '0 0 30px #00f5ff, 0 0 60px #00f5ff' : undefined,
                      }}
                    >
                      {char}
                    </span>
                  ))}
                </div>
                <div className="title-reveal-line" style={{ width: `${Math.min(titleChars / 12, 1) * 100}%` }} />
                <div className="activation-status">
                  <span className="status-bullet" />
                  <span>ONLINE // ALL SYSTEMS COMBAT READY</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
};

