import React, { useState, useEffect, useRef, useMemo } from 'react';
import { AudioSync } from '../audio/AudioSync';

interface TerminalPhaseProps {
  active: boolean;
  onComplete: () => void;
  audioSync: AudioSync | null;
}

interface TerminalItem {
  text: string;
  type: 'cmd' | 'ready' | 'verified';
  latency: number; // pause after line in ms
}

function getLiveHardwareTelemetry() {
  try {
    if (typeof window !== 'undefined' && window.require) {
      const os = window.require('os');
      return {
        cpu: os.cpus()?.[0]?.model || 'Apple Silicon M-Series',
        cores: os.cpus()?.length || 10,
        ram: Math.round(os.totalmem() / (1024 * 1024 * 1024)) || 32,
        host: os.hostname() || 'macOS.local',
        user: os.userInfo()?.username || 'Divyanshu',
      };
    }
  } catch {}
  return {
    cpu: 'Apple M5',
    cores: 10,
    ram: 32,
    host: 'Divyanshus-MacBook-pro.local',
    user: 'divyanshu',
  };
}

export const TerminalPhase: React.FC<TerminalPhaseProps> = ({ active, onComplete, audioSync }) => {
  const telemetry = useMemo(() => getLiveHardwareTelemetry(), []);

  const terminalLog = useMemo<TerminalItem[]>(() => [
    { text: `Initializing JARVIS AI Core [${telemetry.host}]...`, type: 'cmd', latency: 110 },
    { text: `Hardware Platform: ${telemetry.cpu} (${telemetry.cores} Cores)`, type: 'ready', latency: 120 },
    { text: `System Memory: ${telemetry.ram} GB Unified Memory Verified`, type: 'ready', latency: 110 },
    { text: `Operator Identified: ${telemetry.user.toUpperCase()} // Clearance Alpha`, type: 'verified', latency: 130 },
    { text: "Loading Cognitive Architecture...", type: 'cmd', latency: 110 },
    { text: "Initializing Neural Processing Engine...", type: 'cmd', latency: 110 },
    { text: "Initializing Context Engine...", type: 'cmd', latency: 100 },
    { text: "Loading Voice Interface...", type: 'cmd', latency: 100 },
    { text: "Initializing Perception Layer...", type: 'cmd', latency: 110 },
    { text: "Synchronizing Intelligence Modules...", type: 'cmd', latency: 120 },
    { text: "Initializing Long-Term Memory...", type: 'cmd', latency: 110 },
    { text: "Establishing Secure Communication Layer...", type: 'cmd', latency: 110 },
    { text: "Running Diagnostics...", type: 'cmd', latency: 120 },
    { text: "Verifying Core Integrity...", type: 'cmd', latency: 110 },
    { text: "Neural Core: READY", type: 'ready', latency: 120 },
    { text: "Memory System: READY", type: 'ready', latency: 120 },
    { text: "Voice Interface: READY", type: 'ready', latency: 120 },
    { text: "Perception System: READY", type: 'ready', latency: 130 },
    { text: "System Integrity: VERIFIED // READY FOR AI CORE", type: 'verified', latency: 250 },
  ], [telemetry]);

  const [displayedLines, setDisplayedLines] = useState<{ text: string; isComplete: boolean; type: string }[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isDissolving, setIsDissolving] = useState(false);
  const [cursorStopped, setCursorStopped] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Background Hex Telemetry Stream
  const [hexRows, setHexRows] = useState<string[]>([]);
  useEffect(() => {
    const generateHex = () => {
      const rows: string[] = [];
      for (let i = 0; i < 20; i++) {
        const addr = `0x${(0x7ff00000 + i * 0x1000).toString(16).toUpperCase()}`;
        const b1 = Math.floor(Math.random() * 0xff).toString(16).padStart(2, '0').toUpperCase();
        const b2 = Math.floor(Math.random() * 0xff).toString(16).padStart(2, '0').toUpperCase();
        const b3 = Math.floor(Math.random() * 0xff).toString(16).padStart(2, '0').toUpperCase();
        const b4 = Math.floor(Math.random() * 0xff).toString(16).padStart(2, '0').toUpperCase();
        rows.push(`${addr}: ${b1} ${b2} ${b3} ${b4}`);
      }
      return rows;
    };
    setHexRows(generateHex());
    const interval = setInterval(() => setHexRows(generateHex()), 400);
    return () => clearInterval(interval);
  }, []);

  // Character-by-character typing loop (~10s total for all 19 lines)
  useEffect(() => {
    if (!active || isDissolving) return;

    let timeout: ReturnType<typeof setTimeout>;

    if (currentLineIndex < terminalLog.length) {
      const lineItem = terminalLog[currentLineIndex];
      const fullText = lineItem.text;

      if (currentCharIndex < fullText.length) {
        // High-precision character cadence (5ms - 10ms)
        const delay = Math.random() * 5 + 5;
        timeout = setTimeout(() => {
          setDisplayedLines(prev => {
            const next = [...prev];
            if (!next[currentLineIndex]) {
              next[currentLineIndex] = { text: '', isComplete: false, type: lineItem.type };
            }
            next[currentLineIndex].text = fullText.slice(0, currentCharIndex + 1);
            return next;
          });

          // Subtle procedural audio tick every 4 characters
          if (currentCharIndex % 4 === 0 && audioSync) {
            audioSync.playKeystroke();
          }

          setCurrentCharIndex(prev => prev + 1);
        }, delay);
      } else {
        // Line completed
        setDisplayedLines(prev => {
          const next = [...prev];
          if (next[currentLineIndex]) {
            next[currentLineIndex].isComplete = true;
          }
          return next;
        });

        // Chime on milestones
        if ((lineItem.type === 'ready' || lineItem.type === 'verified') && audioSync) {
          audioSync.playConfirm();
        }

        timeout = setTimeout(() => {
          setCurrentLineIndex(prev => prev + 1);
          setCurrentCharIndex(0);
        }, Math.min(lineItem.latency, 140));
      }
    } else {
      // Final line reached: stop cursor, trigger particle dissolve
      setCursorStopped(true);
      
      timeout = setTimeout(() => {
        setIsDissolving(true);
        triggerParticleDissolve();

        // 1.8s dissolve and particle drift towards center -> transition to Reactor
        setTimeout(() => {
          onComplete();
        }, 1800);
      }, 300);
    }

    // Smooth Progress Calculation
    const totalLines = terminalLog.length;
    const progressVal = ((currentLineIndex + (currentCharIndex / (terminalLog[currentLineIndex]?.text.length || 1))) / totalLines) * 100;
    setProgress(Math.min(Math.round(progressVal), 100));

    return () => clearTimeout(timeout);
  }, [active, currentLineIndex, currentCharIndex, isDissolving, onComplete, audioSync, terminalLog]);

  // Canvas particle dissolve into center
  const triggerParticleDissolve = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    interface DissolveParticle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      alpha: number;
    }

    const particles: DissolveParticle[] = [];
    // Spawn 350 luminous particles across screen
    for (let i = 0; i < 350; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        size: Math.random() * 2 + 1,
        alpha: Math.random() * 0.8 + 0.2,
      });
    }

    let frameId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach(p => {
        // Gravitational pull toward screen center
        const dx = centerX - p.x;
        const dy = centerY - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 5) {
          p.x += (dx / dist) * 4.5 + p.vx;
          p.y += (dy / dist) * 4.5 + p.vy;
          p.alpha = Math.min(1.0, p.alpha * 0.985);
        } else {
          p.alpha = 0;
        }

        ctx.fillStyle = `rgba(0, 229, 255, ${p.alpha})`;
        ctx.shadowColor = '#00e5ff';
        ctx.shadowBlur = 6;
        ctx.fillRect(p.x, p.y, p.size, p.size);
      });

      frameId = requestAnimationFrame(animate);
    };

    animate();

    setTimeout(() => {
      cancelAnimationFrame(frameId);
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }, 3400);
  };

  // Auto-scroll terminal
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayedLines]);

  if (!active) return null;

  const renderLine = (item: { text: string; type: string }, i: number) => {
    if (item.type === 'verified') {
      const parts = item.text.split(': VERIFIED');
      return (
        <div key={i} className="terminal-line" style={{ marginTop: '8px' }}>
          <span>&gt; {parts[0]}:</span>
          <span className="status-verified">VERIFIED</span>
        </div>
      );
    }

    if (item.type === 'ready') {
      const parts = item.text.split(': READY');
      return (
        <div key={i} className="terminal-line">
          <span>&gt; {parts[0]}:</span>
          <span className="status-ok">READY</span>
        </div>
      );
    }

    return (
      <div key={i} className="terminal-line">
        <span>&gt; {item.text}</span>
      </div>
    );
  };

  return (
    <div className={`terminal-wrapper ${isDissolving ? 'dissolving' : ''}`}>
      {/* Dissolve Particles Canvas */}
      <canvas ref={canvasRef} className="dissolve-canvas" />

      {/* Telemetry Header Bar */}
      <div className="terminal-header">
        <div className="header-left">
          <div className="divyanshu-logo-mark">DIVYANSHU INDUSTRIES</div>
          <div className="header-badge pulse">JARVIS OS // MARK VII BOOTLOADER</div>
          <span>HOST: {telemetry.host}</span>
        </div>
        <div className="header-right">
          <span>PLATFORM: {telemetry.cpu.toUpperCase()}</span>
          <span>RAM: {telemetry.ram} GB UNIFIED</span>
          <span>CLEARANCE: ALPHA PRIME</span>
        </div>
      </div>

      {/* Terminal Main Body */}
      <div className="terminal-body">
        <div className="terminal-scroll" ref={scrollRef}>
          {displayedLines.map((line, i) => renderLine(line, i))}
          {!isDissolving && !cursorStopped && currentLineIndex < terminalLog.length && (
            <span className="cursor" />
          )}
          {cursorStopped && !isDissolving && (
            <span className="cursor static" />
          )}
        </div>

        {/* Real-time Hex Memory Telemetry Sidebar */}
        <div className="terminal-telemetry-sidebar">
          <div style={{ color: 'var(--cyan)', borderBottom: '1px solid rgba(0,229,255,0.2)', paddingBottom: '4px' }}>
            HEX DUMP // BUFFER REALTIME
          </div>
          <div className="hex-stream">
            {hexRows.map((row, idx) => (
              <div key={idx}>{row}</div>
            ))}
          </div>
          <div style={{ fontSize: '10px', color: 'rgba(0,229,255,0.45)' }}>
            STATUS: NOMINAL // ALL CHANNELS VERIFIED
          </div>
        </div>
      </div>

      {/* Progress Footer */}
      <div className="terminal-footer">
        <div className="progress-label-row">
          <span>INITIALIZING SYSTEM MATRIX</span>
          <span>[ {progress}% ]</span>
        </div>
        <div className="progress-track">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
};
