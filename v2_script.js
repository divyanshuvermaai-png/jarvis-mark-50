const API_URL = 'http://localhost:5001/api';

const S = {
    listening: false, rec: null, synth: window.speechSynthesis,
    voiceTick: 0, chartData: new Array(30).fill(0),
    netUpData: new Array(15).fill(0), netDownData: new Array(15).fill(0)
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
    
    // Draw initial empty gauges
    drawComplexGauge('gaugeCpu', 0, '#00e5ff');
    drawComplexGauge('gaugeMem', 0, '#1b66f2');
    
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
        document.getElementById('aiStatus').innerText = d.ai === 'active' ? 'CORE ONLINE' : 'FALLBACK MODE';
    } catch(e) {}
}

async function fetchInfo() {
    try {
        const r = await fetch(API_URL + '/system-info');
        if (!r.ok) return;
        const d = await r.json();
        
        // Complex Gauges
        drawComplexGauge('gaugeCpu', d.cpu.percent, '#00e5ff');
        drawComplexGauge('gaugeMem', d.memory.percent, '#1b66f2');
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

// ─── COMPLEX CANVAS DRAWING ───
function drawComplexGauge(canvasId, percent, color) {
    const cvs = document.getElementById(canvasId);
    if(!cvs) return;
    const ctx = cvs.getContext('2d');
    const w = cvs.width, h = cvs.height, cx = w/2, cy = h/2;
    
    ctx.clearRect(0,0,w,h);
    
    // Outer tick marks
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)';
    for(let i=0; i<60; i++) {
        const angle = (i/60) * Math.PI * 2;
        const r1 = 70, r2 = i%5===0 ? 76 : 73;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle)*r1, cy + Math.sin(angle)*r1);
        ctx.lineTo(cx + Math.cos(angle)*r2, cy + Math.sin(angle)*r2);
        ctx.stroke();
    }
    
    // Inner track
    ctx.beginPath();
    ctx.arc(cx, cy, 60, Math.PI*0.75, Math.PI*2.25);
    ctx.lineWidth = 6;
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.stroke();
    
    // Value Arc
    const valAngle = Math.PI*0.75 + (percent/100) * (Math.PI*1.5);
    ctx.beginPath();
    ctx.arc(cx, cy, 60, Math.PI*0.75, valAngle);
    ctx.lineWidth = 6;
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.shadowBlur = 10;
    ctx.shadowColor = color;
    ctx.stroke();
    ctx.shadowBlur = 0; // reset
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
            <div class="m-text">${formatted}</div>
        </div>
    `;
    list.appendChild(div);
    list.parentElement.scrollTop = list.parentElement.scrollHeight;
}

async function sendChat() {
    const inp = document.getElementById('chatInput');
    const msg = inp.value.trim();
    if(!msg) return;
    inp.value = '';
    pushMessage(msg, 'u');
    
    try {
        const r = await fetch(API_URL + '/chat', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({message: msg})
        });
        const d = await r.json();
        if(d.response) {
            pushMessage(d.response, 'j');
            speakText(d.response);
        }
        if(d.action && d.action.success) {
            toast(`EXEC PROTOCOL: ${d.action.action.toUpperCase()}`);
        }
    } catch(e) {
        pushMessage("SYSTEM ERROR: UNABLE TO REACH CORE SERVER.", 'j');
    }
}

function initVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(SR) {
        S.rec = new SR();
        S.rec.continuous = false;
        S.rec.interimResults = false;
        
        S.rec.onstart = () => { S.listening = true; document.getElementById('micBtn').classList.add('recording'); };
        S.rec.onresult = e => { document.getElementById('chatInput').value = e.results[0][0].transcript; sendChat(); };
        S.rec.onend = () => { S.listening = false; document.getElementById('micBtn').classList.remove('recording'); };
        S.rec.onerror = () => { S.listening = false; document.getElementById('micBtn').classList.remove('recording'); };
        
        document.getElementById('micBtn').addEventListener('click', () => {
            if(S.listening) S.rec.stop(); else S.rec.start();
        });
    }
}

function startVoiceWave() {
    const cvs = document.getElementById('voiceWave');
    const ctx = cvs.getContext('2d');
    function draw() {
        ctx.clearRect(0,0,cvs.width,cvs.height);
        ctx.beginPath();
        const amp = (S.listening || window.speechSynthesis.speaking) ? 18 : 3;
        for(let x=0; x<cvs.width; x+=2) {
            const y = cvs.height/2 + Math.sin(x*0.05 + S.voiceTick)*amp + Math.cos(x*0.01 + S.voiceTick)*amp*0.5;
            if(x===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        }
        ctx.strokeStyle = 'rgba(0, 229, 255, 0.8)'; ctx.lineWidth = 1.5; ctx.stroke();
        S.voiceTick += 0.15;
        requestAnimationFrame(draw);
    }
    draw();
}

function speakText(txt) {
    if(!S.synth) return;
    S.synth.cancel();
    const clean = txt.replace(/\*/g,'').replace(/`/g,'');
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 1.05; u.pitch = 0.85;
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
        b.addEventListener('click', async () => {
            const act = b.dataset.action;
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
        fetch(API_URL + '/action', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({action: 'volume', params: {level: parseInt(e.target.value)}})
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

    openBtn.addEventListener('click', async () => {
        modal.style.display = 'flex';
        try {
            const r = await fetch(API_URL + '/settings');
            const d = await r.json();
            if(d.provider) document.getElementById('providerSelect').value = d.provider;
            if(d.model) document.getElementById('modelInput').value = d.model;
            if(d.api_keys) {
                if(d.api_keys.gemini) document.getElementById('api_key_gemini').value = d.api_keys.gemini;
                if(d.api_keys.openrouter) document.getElementById('api_key_openrouter').value = d.api_keys.openrouter;
                if(d.api_keys.groq) document.getElementById('api_key_groq').value = d.api_keys.groq;
                if(d.api_keys.nvidia) document.getElementById('api_key_nvidia').value = d.api_keys.nvidia;
            } else if(d.api_key) {
                document.getElementById('api_key_gemini').value = d.api_key;
            }
        } catch(e) {}
    });
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    saveBtn.addEventListener('click', async () => {
        const payload = {
            provider: document.getElementById('providerSelect').value,
            model: document.getElementById('modelInput').value.trim(),
            api_key: document.getElementById('apiKeyInput').value.trim()
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

