const API_URL = 'http://localhost:5001/api';

// ─── STARK UI PROCEDURAL AUDIO SYNTHESIZER ───
const StarkAudio = {
    ctx: null,
    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    },
    chirp(freq = 880, dur = 0.05, type = 'sine') {
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(freq * 1.5, this.ctx.currentTime + dur);
            gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + dur);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + dur);
        } catch(e) {}
    },
    execute() {
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(260, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(75, this.ctx.currentTime + 0.18);
            gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.18);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.18);
        } catch(e) {}
    },
    hover() {
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1400, this.ctx.currentTime);
            gain.gain.setValueAtTime(0.02, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.02);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.02);
        } catch(e) {}
    },
    wakeChime() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            [587, 880, 1175].forEach((freq, idx) => {
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, now + idx * 0.08);
                gain.gain.setValueAtTime(0.08, now + idx * 0.08);
                gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.08 + 0.16);
                osc.connect(gain);
                gain.connect(this.ctx.destination);
                osc.start(now + idx * 0.08);
                osc.stop(now + idx * 0.08 + 0.16);
            });
        } catch(e) {}
    },
    capacitorWhine() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const dur = 0.6;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.exponentialRampToValueAtTime(1800, now + dur);
            gain.gain.setValueAtTime(0.025, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + dur);
        } catch(e) {}
    },
    repulsorBurst() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const dur = 0.35;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.exponentialRampToValueAtTime(45, now + dur);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + dur);
        } catch(e) {}
    },
    servoClick() {
        try {
            this.init();
            if (!this.ctx) return;
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(2400, now);
            gain.gain.setValueAtTime(0.03, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.015);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.015);
        } catch(e) {}
    }
};

window.JarvisAudio = StarkAudio;
window.StarkAudio = StarkAudio;

const S = {
    listening: false, rec: null, synth: window.speechSynthesis,
    voiceTick: 0, chartData: new Array(30).fill(0),
    netUpData: new Array(15).fill(0), netDownData: new Array(15).fill(0),
    gauge: {
        cpu: { current: 0, target: 0 },
        mem: { current: 0, target: 0 },
        sweepAngle: 0,
        time: 0
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initVoice();
    initChat();
    initControls();
    startSystemPolling();
    startVoiceWave();
    startHexStream();
    startHoloCoords();
    
    // Start cinematic gauge animation loop
    animateGauges();
    
    // Initialize settings modal and tabs
    initSettings();
    
    // Marvel Studios FUI Audio Matrix & Telemetry
    initCircularWave();
    initPolarRadar();
    startTelemetryJitter();
    
    // Always-Listening "Hey Jarvis" Wake Word
    initWakeWord();
    initWakeWordButton();
    
    pushMessage('J.A.R.V.I.S. MK V ONLINE. ALL PROTOCOLS NOMINAL.', 'j');
});

// ─── EFFECTS & DECORATIONS ───
function initClock() {
    setInterval(() => {
        const now = new Date();
        document.getElementById('sysDate').innerText = now.toISOString().split('T')[0];
        document.getElementById('sysTime').innerText = now.toTimeString().split(' ')[0];
    }, 1000);
}

function startHexStream() {
    const el = document.getElementById('hexStream');
    setInterval(() => {
        let stream = '';
        for(let i=0; i<80; i++) {
            stream += Math.floor(Math.random()*16).toString(16).toUpperCase() + ' ';
        }
        el.innerText = stream;
    }, 100);
}

function startHoloCoords() {
    const el = document.getElementById('randCoords');
    setInterval(() => {
        const lat = (Math.random() * 90).toFixed(4);
        const lon = (Math.random() * 180).toFixed(4);
        el.innerText = `SYS.COORD // ${lat} - ${lon}`;
    }, 2000);
}

// ─── SYSTEM POLLING ───
function startSystemPolling() {
    fetchStatus(); fetchInfo(); fetchProcs();
    setInterval(fetchInfo, 1000); // 1s for fast live data
    setInterval(fetchProcs, 4000);
    setInterval(fetchStatus, 10000);
}

async function fetchStatus() {
    try {
        const r = await fetch(API_URL + '/status');
        const d = await r.json();
        const aiStatusEl = document.getElementById('aiStatus');
        if (aiStatusEl) aiStatusEl.innerText = d.ai === 'active' ? 'CORE ONLINE' : 'FALLBACK MODE';
        
        const statusBadgeEl = document.getElementById('statusBadge');
        if (statusBadgeEl) {
            if (d.ai === 'active') {
                if (d.provider === 'gemma' || d.provider === 'qwen' || d.provider === 'local') {
                    statusBadgeEl.innerText = 'AI: GEMMA 4 (LOCAL)';
                    statusBadgeEl.style.color = '#00ff88';
                } else {
                    statusBadgeEl.innerText = `AI: ${d.provider ? d.provider.toUpperCase() : 'ONLINE'}`;
                    statusBadgeEl.style.color = '#00e5ff';
                }
                statusBadgeEl.classList.remove('warn');
            } else {
                statusBadgeEl.innerText = 'AI: OFFLINE';
                statusBadgeEl.classList.add('warn');
                statusBadgeEl.style.color = '#ff3366';
            }
        }
    } catch(e) {}
}

async function fetchInfo() {
    try {
        const r = await fetch(API_URL + '/system-info');
        if (!r.ok) return;
        const d = await r.json();
        
        // Set gauge targets (animation loop handles rendering)
        S.gauge.cpu.target = d.cpu.percent;
        S.gauge.mem.target = d.memory.percent;
        document.getElementById('cpuVal').innerText = Math.round(d.cpu.percent);
        document.getElementById('memVal').innerText = Math.round(d.memory.percent);
        
        // Data Bars
        document.getElementById('ramUsed').innerText = `${d.memory.used} GB`;
        document.getElementById('ramBar').style.width = `${d.memory.percent}%`;
        
        document.getElementById('diskUsed').innerText = `${d.disk.used} / ${d.disk.total} GB`;
        document.getElementById('diskBar').style.width = `${d.disk.percent}%`;
        
        // Network
        document.getElementById('netUp').innerText = `${d.network.sent} MB`;
        document.getElementById('netDown').innerText = `${d.network.recv} MB`;
        S.netUpData.shift(); S.netUpData.push(d.network.sent);
        S.netDownData.shift(); S.netDownData.push(d.network.recv);
        drawMiniChart('netUpChart', S.netUpData, '#00e5ff');
        drawMiniChart('netDownChart', S.netDownData, '#1b66f2');
        
        // Main Chart
        S.chartData = d.cpu.history;
        if(S.chartData.length < 30) {
            const pad = new Array(30 - S.chartData.length).fill(0);
            S.chartData = pad.concat(S.chartData);
        } else if(S.chartData.length > 30) {
            S.chartData = S.chartData.slice(S.chartData.length - 30);
        }
        drawMainChart();
    } catch(e) {}
}

async function fetchProcs() {
    try {
        const r = await fetch(API_URL + '/processes');
        if(!r.ok) return;
        const procs = await r.json();
        const html = procs.slice(0, 10).map(p => `
            <div class="proc-row">
                <span class="p-name">${p.name}</span>
                <span class="p-pid">${p.pid}</span>
                <span class="p-cpu">${p.cpu}%</span>
            </div>
        `).join('');
        document.querySelectorAll('.proc-row').forEach(e => e.remove());
        document.getElementById('procList').insertAdjacentHTML('beforeend', html);
    } catch(e) {}
}

// ─── CINEMATIC GAUGE SYSTEM ───

function getGaugeColor(percent) {
    if (percent < 50) return { r: 0, g: 229, b: 255 }; // Cyan
    if (percent < 80) {
        const t = (percent - 50) / 30;
        return { r: Math.round(255 * t), g: Math.round(229 - 46 * t), b: Math.round(255 * (1 - t)) };
    }
    const t = (percent - 80) / 20;
    return { r: 255, g: Math.round(183 * (1 - t) + 51 * t), b: Math.round(102 * t) };
}

function animateGauges() {
    const g = S.gauge;
    g.time = Date.now() / 1000;
    g.sweepAngle += 0.003;
    
    // Smooth interpolation toward targets
    g.cpu.current += (g.cpu.target - g.cpu.current) * 0.06;
    g.mem.current += (g.mem.target - g.mem.current) * 0.06;
    
    drawCinematicGauge('gaugeCpu', g.cpu.current, 'cpu');
    drawCinematicGauge('gaugeMem', g.mem.current, 'mem');
    
    requestAnimationFrame(animateGauges);
}

function drawCinematicGauge(canvasId, percent, type) {
    const cvs = document.getElementById(canvasId);
    if (!cvs) return;
    const ctx = cvs.getContext('2d');
    const w = cvs.width, h = cvs.height;
    const cx = w / 2, cy = h / 2;
    const t = S.gauge.time;
    
    ctx.clearRect(0, 0, w, h);
    
    const color = getGaugeColor(percent);
    const cs = `rgb(${color.r},${color.g},${color.b})`;
    const cg = `rgba(${color.r},${color.g},${color.b},0.5)`;
    const cd = `rgba(${color.r},${color.g},${color.b},0.12)`;
    
    const SA = Math.PI * 0.75;        // Start angle (135°)
    const EA = Math.PI * 2.25;        // End angle (405°)
    const TA = EA - SA;                // Total angle span (270°)
    const VA = SA + (percent / 100) * TA; // Value angle
    
    // ══════ LAYER 1: Outer Fine Tick Ring (120 ticks) ══════
    const oR = 85;
    for (let i = 0; i <= 90; i++) {
        const a = SA + (i / 90) * TA;
        if (a > EA) break;
        const isMajor = i % 10 === 0;
        const isMid = i % 5 === 0;
        const len = isMajor ? 9 : (isMid ? 6 : 3);
        const active = a <= VA;
        
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * oR, cy + Math.sin(a) * oR);
        ctx.lineTo(cx + Math.cos(a) * (oR - len), cy + Math.sin(a) * (oR - len));
        ctx.strokeStyle = active ? cs : `rgba(${color.r},${color.g},${color.b},0.1)`;
        ctx.lineWidth = isMajor ? 2 : 1;
        ctx.globalAlpha = active ? (isMajor ? 1 : 0.7) : 0.4;
        ctx.stroke();
    }
    ctx.globalAlpha = 1;
    
    // ══════ LAYER 2: Outer Dashed Reference Arc ══════
    ctx.beginPath();
    ctx.arc(cx, cy, oR + 3, SA, EA);
    ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b},0.08)`;
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 8]);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // ══════ LAYER 3: Main Value Arc (thick with glow) ══════
    const mR = 70;
    
    // Dark track
    ctx.beginPath();
    ctx.arc(cx, cy, mR, SA, EA);
    ctx.strokeStyle = 'rgba(255,255,255,0.03)';
    ctx.lineWidth = 10;
    ctx.stroke();
    
    // Active arc
    if (percent > 0.5) {
        // Outer glow pass
        ctx.beginPath();
        ctx.arc(cx, cy, mR, SA, VA);
        ctx.strokeStyle = cg;
        ctx.lineWidth = 14;
        ctx.shadowBlur = 20;
        ctx.shadowColor = cs;
        ctx.stroke();
        ctx.shadowBlur = 0;
        
        // Core arc
        ctx.beginPath();
        ctx.arc(cx, cy, mR, SA, VA);
        ctx.strokeStyle = cs;
        ctx.lineWidth = 8;
        ctx.lineCap = 'round';
        ctx.shadowBlur = 8;
        ctx.shadowColor = cs;
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.lineCap = 'butt';
    }
    
    // ══════ LAYER 4: Segmented Inner Arc ══════
    const iR = 57;
    const segs = 36;
    for (let i = 0; i < segs; i++) {
        const ss = SA + (i / segs) * TA;
        const se = SA + ((i + 0.65) / segs) * TA;
        if (ss > EA) break;
        const active = ss <= VA;
        ctx.beginPath();
        ctx.arc(cx, cy, iR, ss, Math.min(se, EA));
        ctx.strokeStyle = active ? `rgba(${color.r},${color.g},${color.b},0.35)` : 'rgba(255,255,255,0.02)';
        ctx.lineWidth = 3;
        ctx.stroke();
    }
    
    // ══════ LAYER 5: Pulsing Inner Reference Circles ══════
    const pulse = 0.5 + 0.5 * Math.sin(t * 2.5);
    
    ctx.beginPath();
    ctx.arc(cx, cy, 48, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b},${0.04 + 0.04 * pulse})`;
    ctx.lineWidth = 1;
    ctx.stroke();
    
    ctx.beginPath();
    ctx.arc(cx, cy, 38, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b},${0.02 + 0.02 * pulse})`;
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // ══════ LAYER 6: Rotating Sweep Line ══════
    const speed = type === 'cpu' ? 1 : 0.7;
    const sweepPos = (S.gauge.sweepAngle * speed) % 1;
    const sweepA = SA + sweepPos * TA;
    
    const sg = ctx.createLinearGradient(
        cx + Math.cos(sweepA) * 35, cy + Math.sin(sweepA) * 35,
        cx + Math.cos(sweepA) * oR, cy + Math.sin(sweepA) * oR
    );
    sg.addColorStop(0, 'transparent');
    sg.addColorStop(1, `rgba(${color.r},${color.g},${color.b},0.25)`);
    
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(sweepA) * 35, cy + Math.sin(sweepA) * 35);
    ctx.lineTo(cx + Math.cos(sweepA) * oR, cy + Math.sin(sweepA) * oR);
    ctx.strokeStyle = sg;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    
    // Sweep dot at tip
    const sdx = cx + Math.cos(sweepA) * oR;
    const sdy = cy + Math.sin(sweepA) * oR;
    ctx.beginPath();
    ctx.arc(sdx, sdy, 2, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${color.r},${color.g},${color.b},0.6)`;
    ctx.fill();
    
    // ══════ LAYER 7: Arc Endpoint Glow ══════
    if (percent > 1) {
        const ex = cx + Math.cos(VA) * mR;
        const ey = cy + Math.sin(VA) * mR;
        
        // Bloom glow
        const eg = ctx.createRadialGradient(ex, ey, 0, ex, ey, 15);
        eg.addColorStop(0, `rgba(255,255,255,0.7)`);
        eg.addColorStop(0.2, cs);
        eg.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(ex, ey, 15, 0, Math.PI * 2);
        ctx.fillStyle = eg;
        ctx.fill();
        
        // Bright core dot
        ctx.beginPath();
        ctx.arc(ex, ey, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.shadowBlur = 6;
        ctx.shadowColor = cs;
        ctx.fill();
        ctx.shadowBlur = 0;
    }
    
    // ══════ LAYER 8: Floating Orbital Particles ══════
    if (percent > 5) {
        for (let i = 0; i < 4; i++) {
            const pA = VA + Math.sin(t * 2.5 + i * 1.57) * 0.35;
            const pR = mR + Math.cos(t * 1.8 + i * 2.1) * 12;
            const px = cx + Math.cos(pA) * pR;
            const py = cy + Math.sin(pA) * pR;
            const pAlpha = 0.2 + 0.3 * Math.sin(t * 3.5 + i * 0.8);
            const pSize = 1 + Math.sin(t * 2 + i) * 0.5;
            
            ctx.beginPath();
            ctx.arc(px, py, pSize, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${color.r},${color.g},${color.b},${pAlpha})`;
            ctx.fill();
        }
    }
}

function drawMainChart() {
    const cvs = document.getElementById('cpuChart');
    if(!cvs) return;
    const ctx = cvs.getContext('2d');
    const w = cvs.width, h = cvs.height;
    
    ctx.clearRect(0,0,w,h);
    
    // Grid
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.1)';
    ctx.lineWidth = 1;
    for(let i=0; i<w; i+=30) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,h); ctx.stroke(); }
    for(let i=0; i<h; i+=25) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(w,i); ctx.stroke(); }
    
    // Y-Axis Labels
    ctx.fillStyle = 'rgba(0, 229, 255, 0.5)';
    ctx.font = '9px "Share Tech Mono"';
    ctx.fillText('100', 2, 10);
    ctx.fillText('50', 2, h/2 + 3);
    ctx.fillText('0', 2, h - 2);
    
    // Line
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 5; ctx.shadowColor = '#00e5ff';
    ctx.beginPath();
    const step = w / (S.chartData.length - 1);
    S.chartData.forEach((val, i) => {
        const x = i * step;
        const y = h - (val / 100 * h);
        if(i===0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Fill
    ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
    const grad = ctx.createLinearGradient(0,0,0,h);
    grad.addColorStop(0, 'rgba(0,229,255,0.4)');
    grad.addColorStop(1, 'rgba(0,229,255,0)');
    ctx.fillStyle = grad;
    ctx.fill();
}

function drawMiniChart(canvasId, data, color) {
    const cvs = document.getElementById(canvasId);
    if(!cvs) return;
    const ctx = cvs.getContext('2d');
    const w = cvs.width, h = cvs.height;
    ctx.clearRect(0,0,w,h);
    
    const max = Math.max(...data, 10); // at least 10 scale
    ctx.strokeStyle = color; ctx.lineWidth = 1.5;
    ctx.beginPath();
    const step = w / (data.length - 1);
    data.forEach((val, i) => {
        const x = i * step;
        const y = h - (val / max * h);
        if(i===0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
}

// ─── CHAT & VOICE ───
function initChat() {
    document.getElementById('sendBtn').addEventListener('click', sendChat);
    document.getElementById('chatInput').addEventListener('keydown', e => {
        if(e.key === 'Enter') sendChat();
    });
}

function pushMessage(text, sender) {
    const list = document.getElementById('chatList');
    const div = document.createElement('div');
    div.className = `msg-node ${sender === 'u' ? 'msg-u' : 'msg-j'}`;
    const formatted = text.replace(/```([\s\S]*?)```/g, '<pre style="background:rgba(0,0,0,0.5);padding:10px;margin:5px 0;color:#00e5ff;font-family:var(--font-mono)">$1</pre>')
                          .replace(/\*\*(.*?)\*\*/g, '<b style="color:#fff">$1</b>');
    
    div.innerHTML = `
        <div class="m-icon"><span>${sender.toUpperCase()}</span></div>
        <div class="m-body">
            <div class="m-sender-badge" style="font-family:var(--font-mono);font-size:9px;color:${sender === 'u' ? 'var(--blue)' : 'var(--cyan)'};letter-spacing:1.5px;margin-bottom:4px;">
                ${sender === 'u' ? 'DIVYANSHU VERMA // BOSS' : 'J.A.R.V.I.S. // AI MATRIX'}
            </div>
            <div class="m-text">${sender === 'j' ? '' : formatted}</div>
        </div>
    `;
    list.appendChild(div);
    list.parentElement.scrollTop = list.parentElement.scrollHeight;

    if (sender === 'j') {
        const textEl = div.querySelector('.m-text');
        let iteration = 0;
        const plain = text.replace(/```[\s\S]*?```/g, '[CODE_BLOCK]').replace(/\*\*/g, '');
        const chars = '0123456789ABCDEF!@#$%&*';
        const interval = setInterval(() => {
            textEl.innerText = plain
                .split('')
                .map((char, index) => {
                    if (index < iteration) return plain[index];
                    if (char === ' ' || char === '\n') return char;
                    return chars[Math.floor(Math.random() * chars.length)];
                })
                .join('');
            
            if (iteration >= plain.length) {
                clearInterval(interval);
                textEl.innerHTML = formatted; // Render rich HTML
            }
            iteration += Math.max(1, Math.floor(plain.length / 22));
        }, 25);
    }
}

async function submitJarvisQuery(msg) {
    if(!msg) return;
    const cleanMsg = msg.trim();
    const lower = cleanMsg.toLowerCase();

    // CLI Command Interception inside HUD
    if (lower === 'clear' || lower === '/clear') {
        document.getElementById('chatList').innerHTML = '';
        pushMessage("Tactical display cleared.", 'j');
        return;
    }
    if (lower === 'health' || lower === '/health' || lower === 'diagnostics') {
        pushMessage(cleanMsg, 'u');
        openHudHealth();
        pushMessage("Opening System Health Audit matrix...", 'j');
        return;
    }
    if (lower === 'test' || lower === '/test' || lower === 'run tests') {
        pushMessage(cleanMsg, 'u');
        openHudTest();
        pushMessage("Initializing Diagnostic Self-Test suite...", 'j');
        return;
    }
    if (cleanMsg.startsWith('/') || lower === 'help' || lower === 'status') {
        pushMessage(cleanMsg, 'u');
        try {
            const res = await fetch(API_URL + '/cli/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cleanMsg.replace(/^\//, '') })
            });
            const d = await res.json();
            pushMessage(d.output || d.error || 'Command processed.', 'j');
            return;
        } catch(e) {
            pushMessage("CLI Execution Error: " + e, 'j');
            return;
        }
    }

    pushMessage(cleanMsg, 'u');
    
    // High-power capacitor charging whine & reactor surge
    StarkAudio.capacitorWhine();
    if (window.HoloReactor) window.HoloReactor.pulse(1.8);
    
    try {
        const r = await fetch(API_URL + '/chat', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message: msg})
        });
        const d = await r.json();
        if(d.response) {
            pushMessage(d.response, 'j');
            StarkAudio.repulsorBurst();
            speakText(d.response);
        }
        if(d.action && d.action.success) {
            toast(`EXEC PROTOCOL: ${d.action.action.toUpperCase()}`);
            if (d.action.action === 'toggle_gestures' && window.toggleGestures) {
                const en = d.action.data && typeof d.action.data.enable === 'boolean' ? d.action.data.enable : true;
                window.toggleGestures(en);
            }
        }
    } catch(e) {
        pushMessage("SYSTEM ERROR: UNABLE TO REACH CORE SERVER.", 'j');
    }
}
window.submitJarvisQuery = submitJarvisQuery;

async function sendChat() {
    const inp = document.getElementById('chatInput');
    const msg = inp.value.trim();
    if(!msg) return;
    inp.value = '';
    await submitJarvisQuery(msg);
}

// ─── ALWAYS-LISTENING "HEY JARVIS" WAKE WORD SYSTEM ───
let wakeWordActive = true;
let wakeRecognizer = null;
const WAKE_WORDS = ['hey jarvis', 'jarvis', 'ok jarvis', 'wake up jarvis', 'hello jarvis'];

function initWakeWord() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    try {
        wakeRecognizer = new SR();
        wakeRecognizer.continuous = true;
        wakeRecognizer.interimResults = true;
        wakeRecognizer.lang = 'en-US';

        wakeRecognizer.onresult = (e) => {
            // Guard: don't trigger when JARVIS is speaking or manual mic is active
            if (isSpeaking || S.listening) return;

            for (let i = e.resultIndex; i < e.results.length; ++i) {
                const transcript = e.results[i][0].transcript.toLowerCase().trim();
                for (const kw of WAKE_WORDS) {
                    if (transcript.includes(kw)) {
                        const kwIndex = transcript.indexOf(kw);
                        const remainder = transcript.slice(kwIndex + kw.length).replace(/^[,.\s]+/, '').trim();

                        StarkAudio.wakeChime();
                        if (window.HoloReactor) window.HoloReactor.pulse(1.6);
                        toast('WAKE SENSOR: "HEY JARVIS" DETECTED');

                        // Pause wake recognizer during processing
                        try { wakeRecognizer.stop(); } catch(err) {}

                        if (remainder.length > 2) {
                            document.getElementById('chatInput').value = remainder;
                            sendChat();
                        } else {
                            speakText("At your service, sir.");
                            setTimeout(() => {
                                if (!S.listening) startHardwareRecording();
                            }, 1100);
                        }
                        return;
                    }
                }
            }
        };

        wakeRecognizer.onerror = (e) => {
            if (e.error !== 'not-allowed') {
                setTimeout(() => {
                    if (wakeWordActive && !S.listening && !isSpeaking && !isRecordingVoice) {
                        try { wakeRecognizer.start(); } catch(err) {}
                    }
                }, 600);
            }
        };

        wakeRecognizer.onend = () => {
            if (wakeWordActive && !S.listening && !isSpeaking && !isRecordingVoice) {
                setTimeout(() => {
                    try { wakeRecognizer.start(); } catch(err) {}
                }, 350);
            }
        };

        if (wakeWordActive) {
            try { wakeRecognizer.start(); } catch(e) {}
        }
    } catch(e) {
        console.warn('Wake recognizer initialization warning:', e);
    }
}

function initWakeWordButton() {
    const btn = document.getElementById('wakeWordBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        wakeWordActive = !wakeWordActive;
        const dot = document.getElementById('wakeWordDot');
        const txt = document.getElementById('wakeWordText');
        if (wakeWordActive) {
            dot.style.background = '#00ff88';
            dot.style.boxShadow = '0 0 8px #00ff88';
            txt.innerText = 'WAKE WORD: ON';
            toast('WAKE SENSOR: ACTIVE ("HEY JARVIS")');
            StarkAudio.chirp(1200, 0.08);
            if (wakeRecognizer) {
                try { wakeRecognizer.start(); } catch(e) {}
            }
        } else {
            dot.style.background = '#ff3366';
            dot.style.boxShadow = '0 0 8px #ff3366';
            txt.innerText = 'WAKE WORD: OFF';
            toast('WAKE SENSOR: STANDBY');
            StarkAudio.chirp(500, 0.08);
            if (wakeRecognizer) {
                try { wakeRecognizer.stop(); } catch(e) {}
            }
        }
    });
}

// ─── HARDWARE MICROPHONE AUDIO RECORDER & MLX WHISPER STT ───
let hardwareMediaRecorder = null;
let recordedAudioChunks = [];
let audioRecordingStream = null;
let vadAudioContext = null;
let vadAnalyser = null;
let vadSilenceTimer = null;
let maxRecordingTimer = null;
let speechDetected = false;
let isRecordingVoice = false;

function initVoice() {
    const micBtn = document.getElementById('micBtn');
    if (!micBtn) return;

    micBtn.addEventListener('click', () => {
        if (isRecordingVoice || S.listening) {
            stopHardwareRecording();
        } else {
            startHardwareRecording();
        }
    });
}

async function startHardwareRecording() {
    const micBtn = document.getElementById('micBtn');
    if (!micBtn) return;

    isRecordingVoice = true;
    S.listening = true;
    micBtn.classList.add('recording');
    micBtn.classList.remove('processing');
    micBtn.title = 'Listening... (click when finished)';

    // Pause wake recognizer to prevent microphone hardware conflicts
    if (wakeWordActive && wakeRecognizer) {
        try { wakeRecognizer.stop(); } catch(e) {}
    }

    try {
        if (!audioRecordingStream || !audioRecordingStream.active) {
            audioRecordingStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1,
                    sampleRate: 16000
                }
            });
        }

        let mimeType = 'audio/webm';
        if (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
        } else if (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
        } else if (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/ogg')) {
            mimeType = 'audio/ogg';
        }

        hardwareMediaRecorder = new MediaRecorder(audioRecordingStream, { mimeType });
        recordedAudioChunks = [];
        speechDetected = false;

        hardwareMediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
                recordedAudioChunks.push(e.data);
            }
        };

        hardwareMediaRecorder.onstart = () => {
            isRecordingVoice = true;
            S.listening = true;
            micBtn.classList.add('recording');
            micBtn.classList.remove('processing');
            micBtn.title = 'Click to finish speaking';
            if (window.HoloReactor) window.HoloReactor.setListening(true);
            toast('MICROPHONE ACTIVE — SPEAK NOW');

            // Setup Voice Activity Detection via Web Audio API
            try {
                if (!vadAudioContext || vadAudioContext.state === 'closed') {
                    vadAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                if (vadAudioContext.state === 'suspended') {
                    vadAudioContext.resume();
                }
                const source = vadAudioContext.createMediaStreamSource(audioRecordingStream);
                vadAnalyser = vadAudioContext.createAnalyser();
                vadAnalyser.fftSize = 512;
                source.connect(vadAnalyser);

                const bufferLength = vadAnalyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);

                let speechFrames = 0;
                let silenceStart = null;
                const checkAudioLevel = () => {
                    if (!isRecordingVoice || !hardwareMediaRecorder || hardwareMediaRecorder.state !== 'recording') return;

                    vadAnalyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) {
                        sum += dataArray[i];
                    }
                    const avg = sum / bufferLength;

                    // Require at least 5 sustained frames of vocal energy before activating silence timer
                    if (avg > 18) {
                        speechFrames++;
                        if (speechFrames >= 5) {
                            speechDetected = true;
                            silenceStart = null;
                            micBtn.title = 'Voice detected... (click to stop)';
                        }
                    } else if (speechDetected) {
                        if (!silenceStart) {
                            silenceStart = Date.now();
                        } else if (Date.now() - silenceStart > 3200) {
                            // 3.2s silence after genuine speech -> auto submit
                            stopHardwareRecording();
                            return;
                        }
                    }

                    requestAnimationFrame(checkAudioLevel);
                };
                requestAnimationFrame(checkAudioLevel);
            } catch (vadErr) {
                console.warn('VAD AudioContext warning:', vadErr);
            }

            // Maximum recording duration cap (30s)
            clearTimeout(maxRecordingTimer);
            maxRecordingTimer = setTimeout(() => {
                if (isRecordingVoice) {
                    stopHardwareRecording();
                }
            }, 30000);
        };

        hardwareMediaRecorder.onstop = async () => {
            clearTimeout(maxRecordingTimer);
            isRecordingVoice = false;
            S.listening = false;
            micBtn.classList.remove('recording');
            micBtn.classList.add('processing');
            if (window.HoloReactor) window.HoloReactor.setListening(false);

            if (recordedAudioChunks.length === 0) {
                micBtn.classList.remove('processing');
                toast('NO AUDIO DETECTED');
                resumeWakeWordIfNeeded();
                return;
            }

            const audioBlob = new Blob(recordedAudioChunks, { type: hardwareMediaRecorder.mimeType || 'audio/webm' });
            if (audioBlob.size < 500) {
                micBtn.classList.remove('processing');
                resumeWakeWordIfNeeded();
                return;
            }

            toast('TRANSCRIBING VIA APPLE SILICON WHISPER...');

            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'command.webm');

                const resp = await fetch('/api/voice/transcribe', {
                    method: 'POST',
                    body: formData
                });

                const data = await resp.json();
                if (data.success && data.text && data.text.trim()) {
                    const cleanText = data.text.trim();
                    toast(`HEARD: "${cleanText}"`);
                    document.getElementById('chatInput').value = cleanText;
                    sendChat();
                } else {
                    toast('NO CLEAR SPEECH DETECTED');
                }
            } catch (err) {
                console.error('[VOICE ERROR] Transcription failed:', err);
                toast('TRANSCRIPTION FAILED');
            } finally {
                micBtn.classList.remove('processing');
                resumeWakeWordIfNeeded();
            }
        };

        hardwareMediaRecorder.start(250);
    } catch (err) {
        console.error('[VOICE ERROR] Microphone access failed:', err);
        isRecordingVoice = false;
        S.listening = false;
        micBtn.classList.remove('recording');
        toast('MICROPHONE ACCESS DENIED');
        resumeWakeWordIfNeeded();
    }
}

function stopHardwareRecording() {
    isRecordingVoice = false;
    if (hardwareMediaRecorder && hardwareMediaRecorder.state === 'recording') {
        try {
            hardwareMediaRecorder.stop();
        } catch (e) {
            console.warn('Error stopping MediaRecorder:', e);
        }
    }
}

function resumeWakeWordIfNeeded() {
    if (wakeWordActive && wakeRecognizer) {
        setTimeout(() => {
            try { wakeRecognizer.start(); } catch(e) {}
        }, 500);
    }
}

function startVoiceWave() {
    const cvs = document.getElementById('voiceWave');
    if (!cvs) return;
    const ctx = cvs.getContext('2d');
    function draw() {
        ctx.clearRect(0,0,cvs.width,cvs.height);
        ctx.beginPath();
        const active = (S.listening || isSpeaking || (window.speechSynthesis && window.speechSynthesis.speaking));
        const amp = active ? 7 : 2;
        const color = active ? '#00e5ff' : 'rgba(0, 229, 255, 0.4)';
        
        for(let x=0; x<cvs.width; x+=2) {
            const normX = (x / cvs.width) * Math.PI;
            const envelope = Math.sin(normX); // taper ends to 0
            const y = cvs.height/2 + (Math.sin(x*0.06 + S.voiceTick)*amp + Math.cos(x*0.02 + S.voiceTick*1.4)*amp*0.5) * envelope;
            if(x===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        }
        ctx.strokeStyle = color;
        ctx.lineWidth = active ? 2.0 : 1.2;
        ctx.stroke();
        S.voiceTick += active ? 0.22 : 0.08;
        requestAnimationFrame(draw);
    }
    draw();
}

let edgeTtsAudio = null;
let isSpeaking = false;

async function speakText(txt) {
    // Stop any currently playing audio
    if (edgeTtsAudio) {
        edgeTtsAudio.pause();
        edgeTtsAudio = null;
    }
    
    const voiceKey = localStorage.getItem('jarvis_voice') || 'jarvis';
    
    try {
        const resp = await fetch(API_URL + '/speak', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: txt, voice: voiceKey })
        });
        
        if (!resp.ok) {
            console.warn('Edge TTS failed, falling back to browser TTS');
            fallbackSpeak(txt);
            return;
        }
        
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        edgeTtsAudio = new Audio(url);
        
        edgeTtsAudio.onplay = () => { 
            isSpeaking = true; 
            if (window.HoloReactor) window.HoloReactor.setSpeaking(true);
        };
        edgeTtsAudio.onended = () => { 
            isSpeaking = false; 
            if (window.HoloReactor) window.HoloReactor.setSpeaking(false);
            URL.revokeObjectURL(url); 
            edgeTtsAudio = null; 
        };
        edgeTtsAudio.onerror = () => { 
            isSpeaking = false; 
            if (window.HoloReactor) window.HoloReactor.setSpeaking(false);
            URL.revokeObjectURL(url); 
            edgeTtsAudio = null; 
        };
        
        edgeTtsAudio.play();
    } catch(e) {
        console.warn('Edge TTS fetch error:', e);
        fallbackSpeak(txt);
    }
}

// Browser fallback if Edge TTS server is down
function fallbackSpeak(txt) {
    if(!S.synth) return;
    S.synth.cancel();
    const clean = txt.replace(/\*/g,'').replace(/`/g,'');
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 1.05; u.pitch = 0.85;
    u.onstart = () => {
        isSpeaking = true;
        if (window.HoloReactor) window.HoloReactor.setSpeaking(true);
    };
    u.onend = () => {
        isSpeaking = false;
        if (window.HoloReactor) window.HoloReactor.setSpeaking(false);
    };
    S.synth.speak(u);
}

// ─── UTILS & CONTROLS ───
function toast(msg) {
    const hub = document.getElementById('toastHub');
    const t = document.createElement('div');
    t.className = 'hud-toast';
    t.innerText = msg;
    hub.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

function initControls() {
    document.querySelectorAll('.tac-btn').forEach(b => {
        b.addEventListener('mouseenter', () => StarkAudio.hover());
        b.addEventListener('click', async () => {
            StarkAudio.chirp(960, 0.05);
            if (window.HoloReactor) window.HoloReactor.pulse(0.8);
            const act = b.dataset.action;
            if (b.id === 'tacAirMouseBtn' || act === 'air_mouse') {
                if (window.toggleGestures) window.toggleGestures();
                return;
            }
            if (act === 'briefing') {
                toast('INITIATING: DAILY BRIEFING');
                submitJarvisQuery("Good morning Jarvis, provide daily briefing.");
                return;
            }
            if (act === 'analyze_screen') {
                toast('INITIATING: COPILOT VISION SCAN');
                submitJarvisQuery("Look at my screen and give me a tactical status analysis.");
                return;
            }

            const paramStr = b.dataset.param;
            let params = {};
            if(act === 'media_control' || act === 'open_app') params = {cmd: paramStr, name: paramStr};
            
            toast(`INITIATING: ${act.toUpperCase()}`);
            try {
                await fetch(API_URL + '/action', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({action: act, params: params})
                });
            } catch(e) {}
        });
    });
    
    document.getElementById('volSlider').addEventListener('change', e => {
        StarkAudio.chirp(700 + parseInt(e.target.value) * 6, 0.03);
        fetch(API_URL + '/action', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({action: 'volume', params: {level: parseInt(e.target.value)}})
        });
    });

    // 3D Holographic Matrix Mode Deck (Core / Mark 85 Suit / Gauntlet)
    document.querySelectorAll('.holo-mode-btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => StarkAudio.hover());
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            document.querySelectorAll('.holo-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (window.HoloReactor) {
                window.HoloReactor.setMode(mode);
            }
            if (window.StarkAudio) {
                window.StarkAudio.servoClick();
            }
        });
    });
}
// ── SETTINGS MODAL ──
async function initSettings() {
    const modal = document.getElementById('settingsModal');
    const openBtn = document.getElementById('openSettingsBtn');
    const closeBtn = document.getElementById('closeSettingsBtn');
    const saveBtn = document.getElementById('saveSettingsBtn');
    
    if(!modal) return;
    
    // Tab Switching Logic
    const tabs = document.querySelectorAll('.s-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.s-tab').forEach(t => {
                t.classList.remove('active');
                t.style.color = '#888';
            });
            document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
            
            tab.classList.add('active');
            tab.style.color = 'var(--theme-primary)';
            document.getElementById('tab_' + tab.dataset.tab).style.display = 'block';
        });
    });
    
    // Auto-fill Model based on Provider
    const providerSelect = document.getElementById('providerSelect');
    const modelInput = document.getElementById('modelInput');
    const localAiBanner = document.getElementById('localAiBanner') || document.getElementById('qwenLocalBanner');
    const cloudKeys = document.getElementById('cloudKeysSection');
    
    const defaultModels = {
        'gemini': 'gemini-3.5-flash',
        'openrouter': 'anthropic/claude-3.5-sonnet',
        'groq': 'llama-3.1-70b-versatile',
        'nvidia': 'meta/llama3-70b-instruct',
        'gemma': 'gemma-4-e2b-it-4bit',
        'qwen': 'gemma-4-e2b-it-4bit'
    };

    function updateProviderUI(provider) {
        if (defaultModels[provider]) {
            modelInput.value = defaultModels[provider];
        }
        if (provider === 'gemma' || provider === 'qwen' || provider === 'local') {
            if (localAiBanner) localAiBanner.style.display = 'block';
            if (cloudKeys) cloudKeys.style.opacity = '0.45';
        } else {
            if (localAiBanner) localAiBanner.style.display = 'none';
            if (cloudKeys) cloudKeys.style.opacity = '1.0';
        }
    }

    providerSelect.addEventListener('change', (e) => {
        updateProviderUI(e.target.value);
    });
    
    // Range sliders output update
    document.getElementById('tempInput').addEventListener('input', e => document.getElementById('tempValOut').innerText = e.target.value);

    openBtn.addEventListener('click', async () => {
        modal.style.display = 'flex';
        try {
            // Check Gemma local status
            fetch(API_URL + '/gemma/status').then(r => r.json()).then(q => {
                const statusText = document.getElementById('localAiStatusText') || document.getElementById('qwenStatusText');
                if (statusText && q.available) {
                    statusText.innerText = `MODEL: ${q.model_name} // ACCELERATION: ${q.device} // STATUS: ${q.status}`;
                }
            }).catch(() => {});

            const r = await fetch(API_URL + '/settings');
            const d = await r.json();
            if(d.provider) {
                document.getElementById('providerSelect').value = d.provider;
                updateProviderUI(d.provider);
            }
            if(d.model) document.getElementById('modelInput').value = d.model;
            if(d.api_keys) {
                if(d.api_keys.gemini) document.getElementById('api_key_gemini').value = d.api_keys.gemini;
                if(d.api_keys.openrouter) document.getElementById('api_key_openrouter').value = d.api_keys.openrouter;
                if(d.api_keys.groq) document.getElementById('api_key_groq').value = d.api_keys.groq;
                if(d.api_keys.nvidia) document.getElementById('api_key_nvidia').value = d.api_keys.nvidia;
            } else if(d.api_key) {
                document.getElementById('api_key_gemini').value = d.api_key;
            }
            if(d.temperature) { document.getElementById('tempInput').value = d.temperature; document.getElementById('tempValOut').innerText = d.temperature; }
            if(d.max_tokens) document.getElementById('tokensInput').value = d.max_tokens;
            if(d.system_prompt) document.getElementById('sysPromptInput').value = d.system_prompt;
        } catch(e) {}
        
        // Load local audio settings
        const localVoice = localStorage.getItem('jarvis_voice') || 'jarvis';
        document.getElementById('voiceSelect').value = localVoice;
    });
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    saveBtn.addEventListener('click', async () => {
        // Save audio settings locally (they run on the frontend)
        localStorage.setItem('jarvis_voice', document.getElementById('voiceSelect').value);
        
        const providerVal = document.getElementById('providerSelect').value;
        const defaultLocal = (providerVal === 'gemma' || providerVal === 'qwen' || providerVal === 'local') ? 'gemma-4-e2b-it-4bit' : 'gemini-3.5-flash';
        const payload = {
            provider: providerVal,
            model: document.getElementById('modelInput').value.trim() || defaultLocal,
            api_keys: {
                gemini: document.getElementById('api_key_gemini').value.trim(),
                openrouter: document.getElementById('api_key_openrouter').value.trim(),
                groq: document.getElementById('api_key_groq').value.trim(),
                nvidia: document.getElementById('api_key_nvidia').value.trim()
            },
            temperature: document.getElementById('tempInput').value,
            max_tokens: document.getElementById('tokensInput').value,
            system_prompt: document.getElementById('sysPromptInput').value.trim()
        };
        try {
            await fetch(API_URL + '/settings', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            modal.style.display = 'none';
            pushMessage('CORE SYNCED. RESTARTING...', 'j');
            setTimeout(() => window.location.reload(), 1000);
        } catch(e) {
            pushMessage('SYNC FAILED', 'j');
        }
    });
}
document.addEventListener('DOMContentLoaded', () => { setTimeout(initSettings, 500); });

// ─── MARVEL STUDIOS / CANTINA CREATIVE AUDIO MATRIX & TELEMETRY ───
function initCircularWave() {
    const cvs = document.getElementById('circularWave');
    if (!cvs) return;
    const ctx = cvs.getContext('2d');
    let angleOffset = 0;

    function draw() {
        ctx.clearRect(0, 0, cvs.width, cvs.height);
        const cx = cvs.width / 2;
        const cy = cvs.height / 2;
        const active = (S.listening || isSpeaking || (window.speechSynthesis && window.speechSynthesis.speaking));
        const numBars = 64;
        const radius = 220;

        // Concentric Holographic Reticle Rings
        ctx.strokeStyle = active ? 'rgba(0, 229, 255, 0.45)' : 'rgba(0, 229, 255, 0.15)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = active ? 'rgba(0, 160, 255, 0.35)' : 'rgba(0, 160, 255, 0.1)';
        ctx.beginPath();
        ctx.arc(cx, cy, radius + 25, 0, Math.PI * 2);
        ctx.stroke();

        // 64 Radial Micro-Bars (Live vocal harmonics)
        for (let i = 0; i < numBars; i++) {
            const angle = (i / numBars) * Math.PI * 2 + angleOffset;
            const barEnergy = active
                ? Math.abs(Math.sin(i * 0.4 + S.voiceTick * 2.2) * 26 + Math.cos(i * 0.8 + S.voiceTick * 1.5) * 14) + 4
                : Math.abs(Math.sin(i * 0.2 + angleOffset * 3) * 5) + 2;

            const x1 = cx + Math.cos(angle) * (radius - 4);
            const y1 = cy + Math.sin(angle) * (radius - 4);
            const x2 = cx + Math.cos(angle) * (radius + barEnergy);
            const y2 = cy + Math.sin(angle) * (radius + barEnergy);

            ctx.strokeStyle = active ? (i % 2 === 0 ? '#00e5ff' : '#ffffff') : 'rgba(0, 229, 255, 0.4)';
            ctx.lineWidth = active ? 2 : 1;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }

        angleOffset += active ? 0.008 : 0.003;
        requestAnimationFrame(draw);
    }
    draw();
}

function initPolarRadar() {
    const cvs = document.getElementById('polarRadar');
    if (!cvs) return;
    const ctx = cvs.getContext('2d');
    let sweepAngle = 0;

    const blips = [
        { r: 38, a: 0.8 },
        { r: 60, a: 2.2 },
        { r: 48, a: 4.0 },
        { r: 26, a: 5.3 }
    ];

    function draw() {
        ctx.clearRect(0, 0, cvs.width, cvs.height);
        const cx = cvs.width / 2;
        const cy = cvs.height / 2;

        // Concentric Range Rings
        ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)';
        ctx.lineWidth = 1;
        [24, 48, 72].forEach(r => {
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();
        });

        // Crosshairs
        ctx.beginPath();
        ctx.moveTo(cx - 72, cy); ctx.lineTo(cx + 72, cy);
        ctx.moveTo(cx, cy - 72); ctx.lineTo(cx, cy + 72);
        ctx.stroke();

        // Rotating Sweep Arc
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 72);
        grad.addColorStop(0, 'rgba(0, 229, 255, 0.3)');
        grad.addColorStop(1, 'rgba(0, 229, 255, 0.02)');
        
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, 72, sweepAngle - 0.45, sweepAngle);
        ctx.closePath();
        ctx.fill();

        // Sweep Line
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(sweepAngle) * 72, cy + Math.sin(sweepAngle) * 72);
        ctx.stroke();

        // Blips
        blips.forEach(b => {
            const bx = cx + Math.cos(b.a) * b.r;
            const by = cy + Math.sin(b.a) * b.r;
            const diff = (sweepAngle - b.a + Math.PI * 2) % (Math.PI * 2);
            const intensity = diff < 0.6 ? 1.0 - (diff / 0.6) : 0.2;

            ctx.fillStyle = `rgba(0, 229, 255, ${intensity})`;
            ctx.beginPath();
            ctx.arc(bx, by, 3, 0, Math.PI * 2);
            ctx.fill();
        });

        sweepAngle += 0.04;
        requestAnimationFrame(draw);
    }
    draw();
}

function startTelemetryJitter() {
    const fluxEl = document.getElementById('tFlux');
    const heatEl = document.getElementById('tHeat');
    const gridEl = document.getElementById('tGrid');
    
    setInterval(() => {
        if (fluxEl) fluxEl.innerText = (4.80 + (Math.random() * 0.06)).toFixed(2) + ' T';
        if (heatEl) heatEl.innerText = (311.8 + (Math.random() * 1.6)).toFixed(1) + ' K';
        if (gridEl) gridEl.innerText = (3.22 + (Math.random() * 0.05)).toFixed(2) + ' GW';
    }, 1200);
}

// ─── INTEGRATED HUD HEALTH, SELF-TEST & CLI MODALS ───
const hudHealthModal = document.getElementById('hudHealthModal');
const hudTestModal = document.getElementById('hudTestModal');
const hudCliModal = document.getElementById('hudCliModal');

function openHudHealth() {
    if (hudHealthModal) {
        hudHealthModal.style.display = 'flex';
        loadHudHealth();
    }
}
function closeHudHealth() {
    if (hudHealthModal) hudHealthModal.style.display = 'none';
}

function openHudTest() {
    if (hudTestModal) {
        hudTestModal.style.display = 'flex';
        runHudTests();
    }
}
function closeHudTest() {
    if (hudTestModal) hudTestModal.style.display = 'none';
}

function openHudCli() {
    if (hudCliModal) {
        hudCliModal.style.display = 'flex';
        const inp = document.getElementById('hudCliInput');
        if (inp) inp.focus();
    }
}
function closeHudCli() {
    if (hudCliModal) hudCliModal.style.display = 'none';
}

async function loadHudHealth() {
    const body = document.getElementById('hudHealthBody');
    if (!body) return;
    body.innerHTML = '<div style="text-align:center;color:var(--theme-primary);padding:20px;">Fetching system diagnostics...</div>';
    try {
        const res = await fetch(API_URL + '/system/health');
        const d = await res.json();
        let subHtml = '';
        if (d.subsystems) {
            for (const [sub, items] of Object.entries(d.subsystems)) {
                subHtml += `<div style="margin-top:10px;font-weight:bold;color:var(--cyan);border-bottom:1px solid rgba(0,229,255,0.2);padding-bottom:4px;">[${sub.toUpperCase()}]</div>`;
                for (const [k, v] of Object.entries(items)) {
                    const isOk = String(v).toLowerCase().includes('ok') || String(v).toLowerCase().includes('normal') || String(v).toLowerCase().includes('enforc');
                    subHtml += `<div style="display:flex;justify-content:space-between;padding:3px 0;"><span style="color:#aaa;">${k}</span><span style="color:${isOk ? '#00ff88' : '#ffaa00'};">${v}</span></div>`;
                }
            }
        }
        body.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;background:rgba(0,0,0,0.4);padding:10px;border-radius:4px;border:1px solid rgba(0,229,255,0.2);">
                <div>OVERALL: <span style="color:${d.operational ? '#00ff88' : '#ff3366'};font-weight:bold;">${d.overall_status || 'OPERATIONAL'}</span></div>
                <div>RAM FREE: <span style="color:#00e5ff;">${d.free_ram_gb || '--'} GB</span></div>
                <div>RAM USED: <span style="color:#00e5ff;">${d.memory_usage_pct || '--'}%</span></div>
                <div>DISK FREE: <span style="color:#00e5ff;">${d.disk_free_gb || '--'} GB</span></div>
            </div>
            ${subHtml}
        `;
    } catch(err) {
        body.innerHTML = `<div style="color:#ff3366;padding:20px;">Failed to inspect health: ${err}</div>`;
    }
}

async function runHudTests() {
    const body = document.getElementById('hudTestBody');
    if (!body) return;
    body.innerHTML = '<div style="text-align:center;color:var(--theme-primary);padding:20px;">Executing diagnostic unit tests across all subsystems...</div>';
    try {
        const res = await fetch(API_URL + '/system/test', { method: 'POST' });
        const d = await res.json();
        body.innerHTML = `
            <div style="background:rgba(0,0,0,0.4);padding:14px;border-radius:4px;border:1px solid ${d.was_successful ? '#00ff88' : '#ff3366'};margin-bottom:12px;">
                <div style="font-size:16px;font-weight:bold;color:${d.was_successful ? '#00ff88' : '#ff3366'};margin-bottom:8px;">
                    ${d.was_successful ? '✅ ALL UNIT TESTS PASSED' : '⚠️ TEST FAILURES DETECTED'}
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
                    <div>TOTAL TESTS: <b style="color:#fff;">${d.tests_run}</b></div>
                    <div>PASSED: <b style="color:#00ff88;">${d.passed}</b></div>
                    <div>FAILURES: <b style="color:#ff3366;">${d.failures}</b></div>
                    <div>ERRORS: <b style="color:#ffaa00;">${d.errors}</b></div>
                    <div>DURATION: <b style="color:var(--cyan);">${d.elapsed_seconds}s</b></div>
                    <div>TIMESTAMP: <span style="color:#888;">${d.timestamp}</span></div>
                </div>
            </div>
        `;
    } catch(err) {
        body.innerHTML = `<div style="color:#ff3366;padding:20px;">Failed to run tests: ${err}</div>`;
    }
}

async function sendHudCliCommand() {
    const inp = document.getElementById('hudCliInput');
    const term = document.getElementById('hudCliTerminal');
    if (!inp || !term) return;
    const cmd = inp.value.trim();
    if (!cmd) return;
    inp.value = '';

    if (cmd.toLowerCase() === 'clear') {
        term.textContent = '';
        return;
    }

    term.textContent += `\nDIVYANSHU [CLI] > ${cmd}\n`;
    term.scrollTop = term.scrollHeight;

    try {
        const res = await fetch(API_URL + '/cli/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd })
        });
        const d = await res.json();
        term.textContent += `${d.output || d.error || 'Done.'}\n`;
    } catch (err) {
        term.textContent += `CLI Connection Error: ${err}\n`;
    }
    term.scrollTop = term.scrollHeight;
}

// WhatsApp Tactical Comms Modal Handlers
function openHudWa() {
    const m = document.getElementById('hudWaModal');
    if (m) {
        m.style.display = 'flex';
        const r = document.getElementById('waRecipient');
        if (r) r.focus();
    }
}

function closeHudWa() {
    const m = document.getElementById('hudWaModal');
    if (m) m.style.display = 'none';
}

function setWaStatus(msg, isError = false) {
    const out = document.getElementById('waStatusOutput');
    if (!out) return;
    out.textContent = msg;
    out.style.color = isError ? '#ff3366' : '#25d366';
}

async function sendWaMessage() {
    const recipient = document.getElementById('waRecipient')?.value.trim();
    const message = document.getElementById('waMessage')?.value.trim();
    if (!recipient) {
        setWaStatus('ERROR: Specify recipient contact name or phone number.', true);
        return;
    }
    if (!message) {
        setWaStatus('ERROR: Message content cannot be empty.', true);
        return;
    }

    setWaStatus(`Transmitting message to ${recipient}...`);
    try {
        const res = await fetch(API_URL + '/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'whatsapp', params: { contact: recipient, message: message } })
        });
        const d = await res.json();
        if (d.success) {
            setWaStatus(`✅ TRANSMISSION CONFIRMED: Message delivered to ${recipient}.`);
            const msgBox = document.getElementById('waMessage');
            if (msgBox) msgBox.value = '';
        } else {
            setWaStatus(`⚠️ TRANSMISSION FAILED: ${d.data || d.error || 'Check WhatsApp state'}`, true);
        }
    } catch (err) {
        setWaStatus(`COMMUNICATION ERROR: ${err}`, true);
    }
}

async function sendWaMedia() {
    const recipient = document.getElementById('waRecipient')?.value.trim();
    const mediaPath = document.getElementById('waMediaPath')?.value.trim();
    const caption = document.getElementById('waMediaCaption')?.value.trim();
    if (!recipient) {
        setWaStatus('ERROR: Specify recipient contact name or phone number.', true);
        return;
    }
    if (!mediaPath) {
        setWaStatus('ERROR: Specify media file path on filesystem.', true);
        return;
    }

    setWaStatus(`Attaching and transmitting media to ${recipient}...`);
    try {
        const res = await fetch(API_URL + '/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'whatsapp_media',
                params: { contact: recipient, file_path: mediaPath, caption: caption }
            })
        });
        const d = await res.json();
        if (d.success) {
            setWaStatus(`✅ ATTACHMENT DELIVERED: Media sent to ${recipient}.`);
        } else {
            setWaStatus(`⚠️ MEDIA SEND FAILED: ${d.data || d.error || 'Check file path and WhatsApp state'}`, true);
        }
    } catch (err) {
        setWaStatus(`COMMUNICATION ERROR: ${err}`, true);
    }
}

async function initiateWaCall(video = false) {
    const recipient = document.getElementById('waRecipient')?.value.trim();
    if (!recipient) {
        setWaStatus('ERROR: Specify recipient contact name or phone number.', true);
        return;
    }

    setWaStatus(`Initiating ${video ? 'video' : 'voice'} call with ${recipient}...`);
    try {
        const res = await fetch(API_URL + '/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'whatsapp_call',
                params: { contact: recipient, video: video }
            })
        });
        const d = await res.json();
        if (d.success) {
            setWaStatus(`📞 CALL ACTIVE: Handshake initiated with ${recipient}.`);
        } else {
            setWaStatus(`⚠️ CALL FAILED: ${d.data || d.error || 'Unable to connect'}`, true);
        }
    } catch (err) {
        setWaStatus(`COMMUNICATION ERROR: ${err}`, true);
    }
}

async function readWaChat() {
    const recipient = document.getElementById('waRecipient')?.value.trim();
    if (!recipient) {
        setWaStatus('ERROR: Specify recipient contact name or phone number.', true);
        return;
    }

    setWaStatus(`Retrieving recent chat history with ${recipient}...`);
    try {
        const res = await fetch(API_URL + '/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'whatsapp_read',
                params: { contact: recipient }
            })
        });
        const d = await res.json();
        if (d.success) {
            setWaStatus(`📨 RECENT CHAT: ${d.data}`);
        } else {
            setWaStatus(`⚠️ READ FAILED: ${d.data || d.error || 'No messages retrieved'}`, true);
        }
    } catch (err) {
        setWaStatus(`COMMUNICATION ERROR: ${err}`, true);
    }
}

// Wire buttons
document.addEventListener('DOMContentLoaded', () => {
    // Header buttons
    const hudHealthBtn = document.getElementById('hudHealthBtn');
    if (hudHealthBtn) hudHealthBtn.addEventListener('click', openHudHealth);

    const hudTestBtn = document.getElementById('hudTestBtn');
    if (hudTestBtn) hudTestBtn.addEventListener('click', openHudTest);

    const hudCliBtn = document.getElementById('hudCliBtn');
    if (hudCliBtn) hudCliBtn.addEventListener('click', openHudCli);

    const hudCommsBtn = document.getElementById('hudCommsBtn');
    if (hudCommsBtn) hudCommsBtn.addEventListener('click', openHudWa);

    const screenWatchBtn = document.getElementById('screenWatchBtn');
    if (screenWatchBtn) {
        screenWatchBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/screen/toggle', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: '{}'
                });
                const data = await res.json();
                const dot = document.getElementById('screenWatchDot');
                const txt = document.getElementById('screenWatchBtnText');
                if (data.monitoring) {
                    if (dot) {
                        dot.style.background = '#00ff88';
                        dot.style.boxShadow = '0 0 8px #00ff88';
                    }
                    if (txt) txt.innerText = 'SCREEN: ON';
                    toast('SCREEN AWARENESS: ACTIVE');
                    StarkAudio.chirp(1200, 0.08);
                } else {
                    if (dot) {
                        dot.style.background = '#ff3366';
                        dot.style.boxShadow = '0 0 8px #ff3366';
                    }
                    if (txt) txt.innerText = 'SCREEN: OFF';
                    toast('SCREEN AWARENESS: STANDBY');
                    StarkAudio.chirp(600, 0.08);
                }
            } catch (err) {
                console.warn('Screen toggle error:', err);
            }
        });
    }

    // ─── Tactical Screen Share & Live Optical Feed ───
    let screenShareStream = null;
    let screenFrameInterval = null;

    async function stopScreenShare() {
        if (screenFrameInterval) {
            clearInterval(screenFrameInterval);
            screenFrameInterval = null;
        }
        if (screenShareStream) {
            screenShareStream.getTracks().forEach(track => track.stop());
            screenShareStream = null;
        }
        const video = document.getElementById('screenShareVideo');
        if (video) video.srcObject = null;

        const deck = document.getElementById('screenShareDeck');
        if (deck) deck.classList.add('hidden');

        const dot = document.getElementById('screenShareDot');
        const txt = document.getElementById('screenShareBtnText');
        if (dot) {
            dot.style.background = '#555';
            dot.style.boxShadow = 'none';
        }
        if (txt) txt.innerText = 'SHARE SCREEN';
        toast('OPTICAL STREAM: TERMINATED');
        StarkAudio.chirp(500, 0.1);
    }

    async function captureAndSendScreenFrame() {
        const video = document.getElementById('screenShareVideo');
        const canvas = document.getElementById('screenShareCanvas');
        if (!video || !canvas || !screenShareStream || video.videoWidth === 0) return;

        canvas.width = Math.min(video.videoWidth, 1280);
        canvas.height = Math.min(video.videoHeight, 720);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL('image/jpeg', 0.65);
        try {
            await fetch('/api/screen/frame', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ frame: dataUrl })
            });
        } catch (e) {
            // Background frame sync
        }
    }

    async function startScreenShare() {
        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    displaySurface: 'monitor',
                    cursor: 'always'
                },
                audio: false
            });

            screenShareStream = stream;
            const video = document.getElementById('screenShareVideo');
            if (video) {
                video.srcObject = stream;
                await video.play();
            }

            const deck = document.getElementById('screenShareDeck');
            if (deck) deck.classList.remove('hidden');

            const dot = document.getElementById('screenShareDot');
            const txt = document.getElementById('screenShareBtnText');
            if (dot) {
                dot.style.background = '#00e5ff';
                dot.style.boxShadow = '0 0 8px #00e5ff';
            }
            if (txt) txt.innerText = 'SHARING: LIVE';

            toast('OPTICAL PERCEPTION: STREAMING LIVE');
            StarkAudio.chirp(1400, 0.12);

            const track = stream.getVideoTracks()[0];
            if (track) {
                track.onended = () => {
                    stopScreenShare();
                };
            }

            setTimeout(captureAndSendScreenFrame, 800);
            screenFrameInterval = setInterval(captureAndSendScreenFrame, 4000);

        } catch (err) {
            console.warn('Screen share cancelled or failed:', err);
            if (err.name !== 'NotAllowedError') {
                toast('SCREEN SHARE ERROR: ' + (err.message || 'Access denied'));
            }
        }
    }

    const screenShareBtn = document.getElementById('screenShareBtn');
    if (screenShareBtn) {
        screenShareBtn.addEventListener('click', () => {
            if (screenShareStream) {
                stopScreenShare();
            } else {
                startScreenShare();
            }
        });
    }

    const screenShareCloseBtn = document.getElementById('screenShareCloseBtn');
    if (screenShareCloseBtn) {
        screenShareCloseBtn.addEventListener('click', stopScreenShare);
    }

    const screenAnalyzeBtn = document.getElementById('screenAnalyzeBtn');
    if (screenAnalyzeBtn) {
        screenAnalyzeBtn.addEventListener('click', async () => {
            await captureAndSendScreenFrame();
            const input = document.getElementById('chatInput');
            if (input) {
                input.value = "What am I watching on my screen right now?";
                const sendBtn = document.getElementById('sendBtn');
                if (sendBtn) sendBtn.click();
            }
        });
    }

    // Tactical panel buttons
    const tacHealthBtn = document.getElementById('tacHealthBtn');
    if (tacHealthBtn) tacHealthBtn.addEventListener('click', openHudHealth);

    const tacTestBtn = document.getElementById('tacTestBtn');
    if (tacTestBtn) tacTestBtn.addEventListener('click', openHudTest);

    const tacCliBtn = document.getElementById('tacCliBtn');
    if (tacCliBtn) tacCliBtn.addEventListener('click', openHudCli);

    const tacCommsBtn = document.getElementById('tacCommsBtn');
    if (tacCommsBtn) tacCommsBtn.addEventListener('click', openHudWa);

    // Health modal buttons
    const closeHudHealthBtn = document.getElementById('closeHudHealthBtn');
    if (closeHudHealthBtn) closeHudHealthBtn.addEventListener('click', closeHudHealth);
    const dismissHudHealthBtn = document.getElementById('dismissHudHealthBtn');
    if (dismissHudHealthBtn) dismissHudHealthBtn.addEventListener('click', closeHudHealth);
    const refreshHudHealthBtn = document.getElementById('refreshHudHealthBtn');
    if (refreshHudHealthBtn) refreshHudHealthBtn.addEventListener('click', loadHudHealth);

    // Test modal buttons
    const closeHudTestBtn = document.getElementById('closeHudTestBtn');
    if (closeHudTestBtn) closeHudTestBtn.addEventListener('click', closeHudTest);
    const dismissHudTestBtn = document.getElementById('dismissHudTestBtn');
    if (dismissHudTestBtn) dismissHudTestBtn.addEventListener('click', closeHudTest);
    const runHudTestBtn = document.getElementById('runHudTestBtn');
    if (runHudTestBtn) runHudTestBtn.addEventListener('click', runHudTests);

    // CLI modal buttons
    const closeHudCliBtn = document.getElementById('closeHudCliBtn');
    if (closeHudCliBtn) closeHudCliBtn.addEventListener('click', closeHudCli);
    const hudCliExecBtn = document.getElementById('hudCliExecBtn');
    if (hudCliExecBtn) hudCliExecBtn.addEventListener('click', sendHudCliCommand);
    const hudCliClearBtn = document.getElementById('hudCliClearBtn');
    if (hudCliClearBtn) hudCliClearBtn.addEventListener('click', () => {
        const term = document.getElementById('hudCliTerminal');
        if (term) term.textContent = '';
    });
    const hudCliInput = document.getElementById('hudCliInput');
    if (hudCliInput) {
        hudCliInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendHudCliCommand();
        });
    }

    // WhatsApp Comms modal buttons
    const closeHudWaBtn = document.getElementById('closeHudWaBtn');
    if (closeHudWaBtn) closeHudWaBtn.addEventListener('click', closeHudWa);
    const dismissHudWaBtn = document.getElementById('dismissHudWaBtn');
    if (dismissHudWaBtn) dismissHudWaBtn.addEventListener('click', closeHudWa);

    const waSendMsgBtn = document.getElementById('waSendMsgBtn');
    if (waSendMsgBtn) waSendMsgBtn.addEventListener('click', sendWaMessage);

    const waSendMediaBtn = document.getElementById('waSendMediaBtn');
    if (waSendMediaBtn) waSendMediaBtn.addEventListener('click', sendWaMedia);

    const waVoiceCallBtn = document.getElementById('waVoiceCallBtn');
    if (waVoiceCallBtn) waVoiceCallBtn.addEventListener('click', () => initiateWaCall(false));

    const waVideoCallBtn = document.getElementById('waVideoCallBtn');
    if (waVideoCallBtn) waVideoCallBtn.addEventListener('click', () => initiateWaCall(true));

    const waReadBtn = document.getElementById('waReadBtn');
    if (waReadBtn) waReadBtn.addEventListener('click', readWaChat);

    // WhatsApp Tabs
    const tabTransmit = document.getElementById('waTabTransmitBtn');
    const tabIntel = document.getElementById('waTabIntelBtn');
    const tabSec = document.getElementById('waTabSecurityBtn');

    if (tabTransmit) tabTransmit.addEventListener('click', () => switchWaTab('transmit'));
    if (tabIntel) tabIntel.addEventListener('click', () => switchWaTab('intel'));
    if (tabSec) tabSec.addEventListener('click', () => switchWaTab('security'));

    // Intelligence triggers
    const btnSum = document.getElementById('waIntelSummarizeBtn');
    if (btnSum) btnSum.addEventListener('click', () => queryWaIntel('summarize'));
    const btnSenders = document.getElementById('waIntelSendersBtn');
    if (btnSenders) btnSenders.addEventListener('click', () => queryWaIntel('senders'));
    const btnNeeds = document.getElementById('waIntelNeedsReplyBtn');
    if (btnNeeds) btnNeeds.addEventListener('click', () => queryWaIntel('needs_reply'));
    const btnDelta = document.getElementById('waIntelDeltaBtn');
    if (btnDelta) btnDelta.addEventListener('click', () => queryWaIntel('delta'));

    // Governance & Security
    const btnSavePerms = document.getElementById('waSavePermsBtn');
    if (btnSavePerms) btnSavePerms.addEventListener('click', saveWaPermissions);
    const btnMock = document.getElementById('waMockToggleBtn');
    if (btnMock) btnMock.addEventListener('click', toggleWaMock);
    const btnAudit = document.getElementById('waRunHealthBtn');
    if (btnAudit) btnAudit.addEventListener('click', runWaHealthAudit);

    // Emoji chips
    document.querySelectorAll('.wa-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const emoji = chip.getAttribute('data-emoji');
            const msgBox = document.getElementById('waMessage');
            if (msgBox && emoji) {
                const start = msgBox.selectionStart || msgBox.value.length;
                const end = msgBox.selectionEnd || msgBox.value.length;
                msgBox.value = msgBox.value.substring(0, start) + emoji + msgBox.value.substring(end);
                msgBox.focus();
                msgBox.setSelectionRange(start + emoji.length, start + emoji.length);
            }
        });
    });
});

// WhatsApp Agent Intelligence & Tab Handlers
function switchWaTab(tab) {
    const paneT = document.getElementById('waPaneTransmit');
    const paneI = document.getElementById('waPaneIntel');
    const paneS = document.getElementById('waPaneSecurity');

    const btnT = document.getElementById('waTabTransmitBtn');
    const btnI = document.getElementById('waTabIntelBtn');
    const btnS = document.getElementById('waTabSecurityBtn');

    if (paneT) paneT.style.display = (tab === 'transmit') ? 'flex' : 'none';
    if (paneI) paneI.style.display = (tab === 'intel') ? 'flex' : 'none';
    if (paneS) paneS.style.display = (tab === 'security') ? 'flex' : 'none';

    if (btnT) {
        btnT.style.background = (tab === 'transmit') ? 'rgba(37, 211, 102, 0.2)' : 'transparent';
        btnT.style.border = (tab === 'transmit') ? '1px solid #25d366' : '1px solid rgba(37, 211, 102, 0.4)';
    }
    if (btnI) {
        btnI.style.background = (tab === 'intel') ? 'rgba(0, 229, 255, 0.2)' : 'transparent';
        btnI.style.border = (tab === 'intel') ? '1px solid #00e5ff' : '1px solid rgba(0, 229, 255, 0.4)';
    }
    if (btnS) {
        btnS.style.background = (tab === 'security') ? 'rgba(255, 170, 0, 0.2)' : 'transparent';
        btnS.style.border = (tab === 'security') ? '1px solid #ffaa00' : '1px solid rgba(255, 170, 0, 0.4)';
    }

    if (tab === 'intel') queryWaIntel('summarize');
    if (tab === 'security') loadWaGovernance();
}

let currentWaMockState = false;

async function loadWaGovernance() {
    try {
        const [pRes, mRes] = await Promise.all([
            fetch(API_URL + '/whatsapp/permissions'),
            fetch(API_URL + '/whatsapp/mock')
        ]);
        if (pRes.ok) {
            const pData = await pRes.json();
            const perms = pData.status?.permissions || {};
            if (document.getElementById('waPermRead')) document.getElementById('waPermRead').checked = !!perms.read_messages;
            if (document.getElementById('waPermSend')) document.getElementById('waPermSend').checked = !!perms.send_messages;
            if (document.getElementById('waPermCall')) document.getElementById('waPermCall').checked = !!perms.call;
            if (document.getElementById('waPermVideo')) document.getElementById('waPermVideo').checked = !!perms.video_call;
            if (document.getElementById('waPermSummarize')) document.getElementById('waPermSummarize').checked = !!perms.summarize;
        }
        if (mRes.ok) {
            const mData = await mRes.json();
            currentWaMockState = !!mData.mock_mode;
            updateMockUI(currentWaMockState);
        }
    } catch (e) {
        console.warn('Could not load WhatsApp governance info', e);
    }
}

function updateMockUI(isMock) {
    const badge = document.getElementById('waMockBadge');
    const btn = document.getElementById('waMockToggleBtn');
    if (badge) {
        badge.textContent = isMock ? 'SIMULATION MODE' : 'LOCAL AGENT';
        badge.style.borderColor = isMock ? '#ffaa00' : '#00e5ff';
        badge.style.color = isMock ? '#ffaa00' : '#00e5ff';
    }
    if (btn) {
        btn.textContent = isMock ? 'SIMULATION: ON' : 'SIMULATION: OFF';
        btn.style.borderColor = isMock ? '#25d366' : '#ffaa00';
        btn.style.color = isMock ? '#25d366' : '#ffaa00';
    }
}

async function toggleWaMock() {
    try {
        const res = await fetch(API_URL + '/whatsapp/mock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mock: !currentWaMockState })
        });
        const d = await res.json();
        currentWaMockState = !!d.mock_mode;
        updateMockUI(currentWaMockState);
    } catch (e) {
        alert('Failed to toggle mock simulation: ' + e);
    }
}

async function saveWaPermissions() {
    const perms = {
        read_messages: document.getElementById('waPermRead')?.checked ?? true,
        send_messages: document.getElementById('waPermSend')?.checked ?? true,
        call: document.getElementById('waPermCall')?.checked ?? true,
        video_call: document.getElementById('waPermVideo')?.checked ?? true,
        summarize: document.getElementById('waPermSummarize')?.checked ?? true
    };
    try {
        const res = await fetch(API_URL + '/whatsapp/permissions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ permissions: perms })
        });
        if (res.ok) {
            alert('WhatsApp permissions saved successfully, Sir.');
        }
    } catch (e) {
        alert('Failed to save permissions: ' + e);
    }
}

async function queryWaIntel(queryType) {
    const out = document.getElementById('waIntelOutput');
    if (!out) return;
    out.textContent = 'Analyzing WhatsApp communication telemetry...';

    try {
        let text = '';
        if (queryType === 'summarize') {
            const res = await fetch(API_URL + '/whatsapp/summarize');
            const d = await res.json();
            text = d.summary || 'No activity recorded.';
        } else {
            let prompt = '';
            if (queryType === 'senders') prompt = 'Who messaged me?';
            else if (queryType === 'needs_reply') prompt = 'Who needs a reply?';
            else if (queryType === 'delta') prompt = "What's new since I left?";

            const res = await fetch(API_URL + '/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: prompt })
            });
            const d = await res.json();
            text = d.response || 'No updates available.';
        }
        out.textContent = text;
    } catch (e) {
        out.textContent = 'Error querying WhatsApp intelligence: ' + e;
    }
}

async function runWaHealthAudit() {
    const out = document.getElementById('waHealthOutput');
    if (!out) return;
    out.textContent = 'Inspecting macOS Catalyst process, Accessibility tree, and IPC...';

    try {
        const res = await fetch(API_URL + '/whatsapp/health');
        const d = await res.json();
        const h = d.health || {};
        const lines = [
            `OVERALL STATUS: ${h.summary || 'COMPLETE'}`,
            `APP INSTALLED: ${h.app_installed ? 'YES' : 'NO'} (${h.app_path || 'N/A'})`,
            `PROCESS RUNNING: ${h.process_running ? 'YES' : 'NO'}`,
            `ACCESSIBILITY PERMISSION: ${h.accessibility_granted ? 'GRANTED' : 'DENIED'}`,
            `SIMULATION MODE: ${h.mock_mode ? 'ACTIVE' : 'INACTIVE'}`,
            `LOCAL FIRST PRIVACY: ${h.privacy_mode || 'STRICT_LOCAL'}`
        ];
        out.textContent = lines.join('\n');
    } catch (e) {
        out.textContent = 'Diagnostic error: ' + e;
    }
}


