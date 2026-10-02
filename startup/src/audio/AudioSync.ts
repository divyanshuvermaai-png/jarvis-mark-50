import { Howl } from 'howler';

/**
 * AudioSync manages the primary startup voice soundtrack (jarvis.wav)
 * and generates procedural, microsecond-synced cinematic sound design
 * (keystroke ticks, sub-bass drones, mechanical latches, scan sweeps,
 * harmonic chords, shockwave impacts, and resolution tones) via Web Audio API.
 */
export class AudioSync {
  private sound: Howl | null = null;
  private startTime: number = 0;
  private isElectron: boolean = false;
  private audioCtx: AudioContext | null = null;
  private subGain: GainNode | null = null;
  private subOsc: OscillatorNode | null = null;
  private samples: Int16Array | null = null;

  constructor(soundPath: string) {
    try {
      if (typeof window !== 'undefined' && typeof window.require === 'function') {
        this.isElectron = true;
      }
    } catch {
      this.isElectron = false;
    }

    // Direct synchronous PCM buffer load for 60-FPS audio-reactive analysis
    if (this.isElectron) {
      try {
        const fs = window.require('fs');
        if (fs.existsSync(soundPath)) {
          const buf = fs.readFileSync(soundPath);
          this.samples = new Int16Array(buf.buffer, buf.byteOffset + 92, Math.floor((buf.length - 92) / 2));
        }
      } catch (e) {
        console.warn('[JARVIS Audio] PCM load warning:', e);
      }
    }

    // Initialize Web Audio API for procedural cinematic sound design
    try {
      const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    } catch (e) {
      console.warn('[JARVIS Audio] Web Audio API init warning:', e);
    }

    // Initialize Howler fallback if not in Electron
    if (!this.isElectron) {
      try {
        this.sound = new Howl({
          src: [soundPath],
          format: ['wav'],
          volume: 1.0,
          html5: true,
          preload: true,
        });
      } catch (e) {
        console.warn('[JARVIS Audio] Howler init error:', e);
      }
    }
  }

  play(): void {
    this.startTime = performance.now();
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }

    if (this.isElectron) {
      try {
        const { ipcRenderer } = window.require('electron');
        ipcRenderer.send('play-startup-sound');
        console.log('[JARVIS Audio] Primary voice soundtrack initialized via Electron IPC');
        return;
      } catch (e) {
        console.warn('[JARVIS Audio] IPC play failed:', e);
      }
    }

    if (this.sound) {
      try {
        this.sound.play();
      } catch (e) {
        console.warn('[JARVIS Audio] Web audio play error:', e);
      }
    }
  }

  getElapsed(): number {
    return (performance.now() - this.startTime) / 1000;
  }

  /**
   * Real-time audio waveform energy sampler (0.0 to 1.0).
   * Computes true instantaneous RMS and bass energy of jarvis.wav at 60 FPS.
   */
  getEnergy(timeSec?: number): { rms: number; bass: number; peak: number } {
    const t = timeSec !== undefined ? timeSec : this.getElapsed();
    if (!this.samples || this.samples.length === 0) {
      return { rms: 0.15, bass: 0.15, peak: 0.15 };
    }
    const center = Math.floor(t * 48000) * 2;
    const windowSize = 1024;
    let sum = 0;
    let count = 0;
    let maxV = 0;
    for (let i = center - windowSize; i < center + windowSize; i += 2) {
      if (i >= 0 && i < this.samples.length) {
        const v = Math.abs(this.samples[i]) / 32768;
        sum += v * v;
        if (v > maxV) maxV = v;
        count++;
      }
    }
    const rawRms = count > 0 ? Math.sqrt(sum / count) : 0;
    const normalizedRms = Math.min(rawRms / 0.14, 1.0);
    return {
      rms: normalizedRms,
      bass: Math.min(normalizedRms * 1.35, 1.0),
      peak: Math.min(maxV / 0.75, 1.0),
    };
  }

  // ── Procedural Sound Effects (Web Audio API) ──

  /** Persistent reactor hum: layered 55Hz + 110Hz sine drone */
  private reactorHumGain: GainNode | null = null;
  private reactorHumOsc1: OscillatorNode | null = null;
  private reactorHumOsc2: OscillatorNode | null = null;

  playReactorHum(): void {
    if (!this.audioCtx || this.reactorHumOsc1) return;
    try {
      const ctx = this.audioCtx;
      
      this.reactorHumGain = ctx.createGain();
      this.reactorHumGain.gain.setValueAtTime(0, ctx.currentTime);
      this.reactorHumGain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 2.0);
      this.reactorHumGain.connect(ctx.destination);

      // 55 Hz fundamental
      this.reactorHumOsc1 = ctx.createOscillator();
      this.reactorHumOsc1.type = 'sine';
      this.reactorHumOsc1.frequency.setValueAtTime(55, ctx.currentTime);
      this.reactorHumOsc1.connect(this.reactorHumGain);
      this.reactorHumOsc1.start();

      // 110 Hz harmonic
      this.reactorHumOsc2 = ctx.createOscillator();
      this.reactorHumOsc2.type = 'sine';
      this.reactorHumOsc2.frequency.setValueAtTime(110, ctx.currentTime);
      const harmGain = ctx.createGain();
      harmGain.gain.setValueAtTime(0.04, ctx.currentTime);
      this.reactorHumOsc2.connect(harmGain);
      harmGain.connect(this.reactorHumGain);
      this.reactorHumOsc2.start();
    } catch (e) {
      console.warn('[JARVIS Audio] Reactor hum error:', e);
    }
  }

  /** Surge the reactor hum intensity (call on beat impacts) */
  surgeReactorHum(intensity: number = 0.15): void {
    if (!this.audioCtx || !this.reactorHumGain) return;
    try {
      const ctx = this.audioCtx;
      this.reactorHumGain.gain.cancelScheduledValues(ctx.currentTime);
      this.reactorHumGain.gain.setValueAtTime(intensity, ctx.currentTime);
      this.reactorHumGain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 0.6);
    } catch {}
  }

  /** Play a resonance harmonic ping on beat impacts */
  playResonancePing(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(220, ctx.currentTime);
      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);
    } catch {}
  }

  /** LFE shockwave thud at 20Hz for activation blast */
  playLFEThud(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(20, ctx.currentTime);
      gain.gain.setValueAtTime(0.5, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.15);
    } catch {}
  }

  /** Stop the persistent reactor hum */
  stopReactorHum(): void {
    try {
      if (this.reactorHumOsc1) { this.reactorHumOsc1.stop(); this.reactorHumOsc1 = null; }
      if (this.reactorHumOsc2) { this.reactorHumOsc2.stop(); this.reactorHumOsc2 = null; }
      this.reactorHumGain = null;
    } catch {}
  }

  /** Subtle, crisp keystroke click for terminal typing */
  playKeystroke(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      filter.type = 'highpass';
      filter.frequency.value = 1600;

      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200 + Math.random() * 600, ctx.currentTime);

      gain.gain.setValueAtTime(0.012, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.035);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.04);
    } catch {}
  }

  /** Soft harmonic confirmation chime for [READY] / [VERIFIED] */
  playConfirm(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
      osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.14); // A6

      gain.gain.setValueAtTime(0.025, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.28);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch {}
  }

  /** Deep ambient sub-bass drone when the energy singularity ignites (45Hz – 70Hz) */
  playSubDrone(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      if (this.subOsc) {
        try { this.subOsc.stop(); } catch {}
      }

      this.subOsc = ctx.createOscillator();
      this.subGain = ctx.createGain();

      this.subOsc.type = 'sine';
      this.subOsc.frequency.setValueAtTime(42, ctx.currentTime);
      this.subOsc.frequency.linearRampToValueAtTime(68, ctx.currentTime + 3.5);

      this.subGain.gain.setValueAtTime(0.001, ctx.currentTime);
      this.subGain.gain.linearRampToValueAtTime(0.06, ctx.currentTime + 2.0);

      this.subOsc.connect(this.subGain);
      this.subGain.connect(ctx.destination);

      this.subOsc.start();
    } catch {}
  }

  /** Mechanical latch / aperture servo click when iris segments lock into position */
  playMechanicalLatch(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      filter.type = 'bandpass';
      filter.frequency.value = 750;
      filter.Q.value = 3.5;

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(280, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(95, ctx.currentTime + 0.08);

      gain.gain.setValueAtTime(0.045, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.09);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.095);
    } catch {}
  }

  /** Resonant frequency sweep during the holographic system scan */
  playScanSweep(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const osc = ctx.createOscillator();
      const filter = ctx.createBiquadFilter();
      const gain = ctx.createGain();

      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(450, ctx.currentTime);
      filter.frequency.exponentialRampToValueAtTime(1600, ctx.currentTime + 1.2);
      filter.frequency.exponentialRampToValueAtTime(450, ctx.currentTime + 2.4);
      filter.Q.value = 4.0;

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, ctx.currentTime);

      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.025, ctx.currentTime + 0.6);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 2.5);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 2.55);
    } catch {}
  }

  /** Layered harmonic chord for system synchronization lock */
  playSyncChime(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const freqs = [330, 440, 554.37, 659.25]; // E, A, C#, E
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime);

        gain.gain.setValueAtTime(0.001, ctx.currentTime + idx * 0.06);
        gain.gain.linearRampToValueAtTime(0.02, ctx.currentTime + idx * 0.06 + 0.2);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.8);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(ctx.currentTime + idx * 0.06);
        osc.stop(ctx.currentTime + 1.9);
      });
    } catch {}
  }

  /** Rising harmonic energy chord during core power-up */
  playRisingChord(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const freqs = [220, 277.18, 329.63, 440]; // A major chord
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(freq * 1.5, ctx.currentTime + 3.0);

        gain.gain.setValueAtTime(0.001, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.02, ctx.currentTime + 1.4);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 3.2);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(ctx.currentTime + idx * 0.05);
        osc.stop(ctx.currentTime + 3.3);
      });
    } catch {}
  }

  /** Sub-bass punch and energy shockwave impact on full AI core activation */
  playShockwave(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      
      // Sub-bass impact oscillator
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(130, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(32, ctx.currentTime + 0.7);

      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.4);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 1.5);

      // Filtered white noise blast
      const bufferSize = ctx.sampleRate * 0.45;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }

      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const noiseFilter = ctx.createBiquadFilter();
      noiseFilter.type = 'lowpass';
      noiseFilter.frequency.setValueAtTime(1100, ctx.currentTime);
      noiseFilter.frequency.exponentialRampToValueAtTime(180, ctx.currentTime + 0.45);

      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(0.05, ctx.currentTime);
      noiseGain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.45);

      noise.connect(noiseFilter);
      noiseFilter.connect(noiseGain);
      noiseGain.connect(ctx.destination);

      noise.start();
      noise.stop(ctx.currentTime + 0.5);
    } catch {}
  }

  /** Warm resolution chime on main interface materialization */
  playResolutionTone(): void {
    if (!this.audioCtx) return;
    try {
      const ctx = this.audioCtx;
      const freqs = [440, 659.25, 880]; // A4, E5, A5
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime);

        gain.gain.setValueAtTime(0.001, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.025, ctx.currentTime + 0.15);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.2);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(ctx.currentTime + idx * 0.08);
        osc.stop(ctx.currentTime + 1.3);
      });
    } catch {}
  }

  stop(): void {
    if (this.isElectron) {
      try {
        const { ipcRenderer } = window.require('electron');
        ipcRenderer.send('stop-startup-sound');
      } catch {}
    }

    if (this.subGain && this.audioCtx) {
      try {
        this.subGain.gain.exponentialRampToValueAtTime(0.0001, this.audioCtx.currentTime + 0.4);
      } catch {}
    }

    if (this.sound) {
      try {
        this.sound.fade(1.0, 0, 1000);
        setTimeout(() => this.sound?.stop(), 1000);
      } catch {}
    }
  }

  isLoaded(): boolean {
    return true;
  }
}
