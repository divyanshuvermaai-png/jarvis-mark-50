/**
 * visor_hud.js - Divyanshu Industries Cinema-Grade Visor HUD Mode
 * Transforms your macOS desktop into an authentic Iron Man in-helmet holographic HUD:
 * - Dynamic Artificial Horizon & Pitch Ladder responding to head/mouse orientation
 * - Animated Azimuth Compass Ribbon with live degree readouts
 * - Supersonic Velocity (Mach 2.4) & Barometric Altitude Flight Tapes
 * - Gimbal Target Acquisition Reticle following cursor with audio lock pings
 * - Transparent Glassmorphism Mode (Cmd+Shift+V or Cmd+Shift+H)
 */

(function() {
    let isVisorActive = false;
    let canvas = null;
    let ctx = null;
    let animId = null;
    let mouse = { x: window.innerWidth / 2, y: window.innerHeight / 2, targetX: window.innerWidth / 2, targetY: window.innerHeight / 2 };
    let pitch = 0;
    let roll = 0;
    let heading = 42;
    let altitude = 18450;
    let machSpeed = 2.4;
    let lockPings = [];
    let time = 0;

    function initVisorHUD() {
        canvas = document.createElement('canvas');
        canvas.id = 'visorHudCanvas';
        canvas.style.position = 'fixed';
        canvas.style.inset = '0';
        canvas.style.width = '100vw';
        canvas.style.height = '100vh';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '9999';
        canvas.style.display = 'none';
        document.body.appendChild(canvas);

        ctx = canvas.getContext('2d');
        resizeCanvas();

        window.addEventListener('resize', resizeCanvas);
        window.addEventListener('mousemove', (e) => {
            mouse.targetX = e.clientX;
            mouse.targetY = e.clientY;
        });

        // Click to fire target lock pulse in Visor Mode
        window.addEventListener('mousedown', (e) => {
            if (!isVisorActive) return;
            lockPings.push({
                x: e.clientX,
                y: e.clientY,
                radius: 10,
                maxRadius: 85,
                opacity: 1.0,
                id: '0x' + Math.floor(Math.random() * 0xFFF).toString(16).toUpperCase()
            });
            if (window.StarkAudio) {
                window.StarkAudio.chirp(1900, 0.06);
                window.StarkAudio.repulsorBurst();
            }
            if (window.HoloReactor) {
                window.HoloReactor.pulse(1.2);
            }
        });

        // Global hotkey: Cmd+Shift+V or Cmd+Shift+H
        window.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'V' || e.key === 'v' || e.key === 'H' || e.key === 'h')) {
                e.preventDefault();
                toggleVisorMode();
            }
        });

        // Header button listener
        const visorBtn = document.getElementById('visorBtn');
        if (visorBtn) {
            visorBtn.addEventListener('click', toggleVisorMode);
        }

        // Expose to window
        window.StarkVisor = {
            toggle: toggleVisorMode,
            isActive: () => isVisorActive
        };
    }

    function resizeCanvas() {
        if (!canvas) return;
        canvas.width = window.innerWidth * window.devicePixelRatio;
        canvas.height = window.innerHeight * window.devicePixelRatio;
        if (ctx) ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }

    function toggleVisorMode() {
        isVisorActive = !isVisorActive;
        const visorBtn = document.getElementById('visorBtn');
        const visorDot = document.getElementById('visorDot');
        const visorText = document.getElementById('visorBtnText');

        if (isVisorActive) {
            canvas.style.display = 'block';
            document.body.classList.add('visor-mode-active');
            if (visorDot) {
                visorDot.style.background = '#00e5ff';
                visorDot.style.boxShadow = '0 0 10px #00e5ff';
            }
            if (visorText) visorText.innerText = 'VISOR HUD: ACTIVE';
            if (window.toast) window.toast('MARK 85 VISOR HUD ENGAGED (CMD+SHIFT+V)');
            if (window.StarkAudio) {
                window.StarkAudio.wakeChime();
                window.StarkAudio.capacitorWhine();
            }
            startVisorRender();
        } else {
            canvas.style.display = 'none';
            document.body.classList.remove('visor-mode-active');
            if (visorDot) {
                visorDot.style.background = '#555';
                visorDot.style.boxShadow = 'none';
            }
            if (visorText) visorText.innerText = 'VISOR HUD: OFF';
            if (window.toast) window.toast('VISOR HUD DISENGAGED');
            if (window.StarkAudio) window.StarkAudio.chirp(500, 0.08);
            if (animId) {
                cancelAnimationFrame(animId);
                animId = null;
            }
        }
    }

    function startVisorRender() {
        if (animId) return;

        function render() {
            if (!isVisorActive) return;
            time += 0.016;

            const w = window.innerWidth;
            const h = window.innerHeight;
            const cx = w / 2;
            const cy = h / 2;

            ctx.save();
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.restore();

            // Smooth mouse follow
            mouse.x += (mouse.targetX - mouse.x) * 0.1;
            mouse.y += (mouse.targetY - mouse.y) * 0.1;

            // Pitch & Roll orientation
            const normX = (mouse.x - cx) / cx;
            const normY = (mouse.y - cy) / cy;
            roll = normX * 0.12;
            pitch = -normY * 60;
            heading = (heading + normX * 0.25 + 360) % 360;

            // ── 1. HELMET VISOR CURVATURE BRACKETS ──
            drawHelmetVignette(w, h);

            // ── 2. CENTRAL ARTIFICIAL HORIZON & PITCH LADDER ──
            drawPitchLadder(cx, cy, pitch, roll);

            // ── 3. TOP AZIMUTH COMPASS TAPE ──
            drawCompassTape(cx, 45, heading);

            // ── 4. VERTICAL FLIGHT TAPES (ALTITUDE & SPEED) ──
            drawFlightTapes(w, h, altitude + normY * 120, machSpeed + Math.sin(time * 0.8) * 0.05);

            // ── 5. GIMBAL TARGET TRACKER (CURSOR) ──
            drawTargetGimbal(mouse.x, mouse.y, time);

            // ── 6. LOCK PINGS & SHOCKWAVES ──
            drawLockPings();

            // ── 7. PERIPHERAL CORNER TELEMETRY ──
            drawPeripheralTelemetry(w, h);

            animId = requestAnimationFrame(render);
        }

        animId = requestAnimationFrame(render);
    }

    function drawHelmetVignette(w, h) {
        ctx.save();
        ctx.strokeStyle = 'rgba(0, 229, 255, 0.45)';
        ctx.lineWidth = 1.5;

        // Top-left curved bracket
        ctx.beginPath();
        ctx.moveTo(60, 40); ctx.lineTo(24, 40); ctx.lineTo(24, 180);
        ctx.stroke();

        // Top-right curved bracket
        ctx.beginPath();
        ctx.moveTo(w - 60, 40); ctx.lineTo(w - 24, 40); ctx.lineTo(w - 24, 180);
        ctx.stroke();

        // Bottom-left bracket
        ctx.beginPath();
        ctx.moveTo(24, h - 180); ctx.lineTo(24, h - 40); ctx.lineTo(120, h - 40);
        ctx.stroke();

        // Bottom-right bracket
        ctx.beginPath();
        ctx.moveTo(w - 24, h - 180); ctx.lineTo(w - 24, h - 40); ctx.lineTo(w - 120, h - 40);
        ctx.stroke();

        ctx.restore();
    }

    function drawPitchLadder(cx, cy, pitchOffset, rollAngle) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(rollAngle);

        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 1.4;
        ctx.fillStyle = '#00e5ff';
        ctx.font = '10px "Share Tech Mono", monospace';
        ctx.textAlign = 'center';

        // Horizon Center Line
        const horizonY = pitchOffset;
        ctx.beginPath();
        ctx.moveTo(-110, horizonY); ctx.lineTo(-25, horizonY);
        ctx.moveTo(25, horizonY); ctx.lineTo(110, horizonY);
        ctx.stroke();

        // Central crosshair
        ctx.beginPath();
        ctx.moveTo(-8, horizonY); ctx.lineTo(8, horizonY);
        ctx.moveTo(0, horizonY - 8); ctx.lineTo(0, horizonY + 8);
        ctx.stroke();

        // Ladder rungs (+10, +20, -10, -20)
        const step = 42;
        [-2, -1, 1, 2].forEach(level => {
            const rungY = horizonY + level * step;
            const deg = -level * 10;
            const sign = deg > 0 ? `+${deg}°` : `${deg}°`;
            const width = Math.abs(level) === 1 ? 65 : 45;

            ctx.beginPath();
            ctx.moveTo(-width, rungY); ctx.lineTo(-width + 15, rungY);
            ctx.moveTo(width - 15, rungY); ctx.lineTo(width, rungY);
            ctx.stroke();

            ctx.fillText(sign, -width - 18, rungY + 4);
            ctx.fillText(sign, width + 18, rungY + 4);
        });

        ctx.restore();
    }

    function drawCompassTape(cx, y, hdg) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 15, 35, 0.7)';
        ctx.fillRect(cx - 180, y - 22, 360, 32);
        ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
        ctx.strokeRect(cx - 180, y - 22, 360, 32);

        // Center pointer triangle
        ctx.fillStyle = '#00ff88';
        ctx.beginPath();
        ctx.moveTo(cx, y + 14); ctx.lineTo(cx - 5, y + 22); ctx.lineTo(cx + 5, y + 22);
        ctx.fill();

        ctx.font = '10px "Share Tech Mono", monospace';
        ctx.fillStyle = '#00e5ff';
        ctx.textAlign = 'center';

        const cardinalMap = { 0: 'N', 90: 'E', 180: 'S', 270: 'W' };

        for (let deg = -60; deg <= 60; deg += 10) {
            const cur = (Math.round(hdg + deg) + 360) % 360;
            const px = cx + deg * 2.8;
            ctx.beginPath();
            ctx.moveTo(px, y - 10);
            ctx.lineTo(px, y - (deg % 30 === 0 ? 2 : 6));
            ctx.strokeStyle = '#00e5ff';
            ctx.stroke();

            if (deg % 30 === 0) {
                const label = cardinalMap[cur] || `${cur}°`;
                ctx.fillText(label, px, y - 13);
            }
        }

        ctx.fillStyle = '#00ff88';
        ctx.fillText(`HDG: ${Math.round(hdg).toString().padStart(3, '0')}°`, cx, y + 6);
        ctx.restore();
    }

    function drawFlightTapes(w, h, alt, mach) {
        ctx.save();
        ctx.fillStyle = 'rgba(0, 15, 35, 0.65)';
        ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
        ctx.font = '10px "Share Tech Mono", monospace';

        // Altitude Tape (Left)
        const leftX = 40;
        const tapeY = h / 2 - 120;
        ctx.fillRect(leftX, tapeY, 65, 240);
        ctx.strokeRect(leftX, tapeY, 65, 240);
        ctx.fillStyle = '#00e5ff';
        ctx.fillText('ALT (FT)', leftX + 8, tapeY - 8);

        for (let i = -4; i <= 4; i++) {
            const yPos = h / 2 + i * 26;
            ctx.beginPath();
            ctx.moveTo(leftX + 50, yPos);
            ctx.lineTo(leftX + 65, yPos);
            ctx.stroke();
            ctx.fillText(Math.round(alt + i * -500), leftX + 8, yPos + 3);
        }

        // Airspeed Tape (Right)
        const rightX = w - 105;
        ctx.fillStyle = 'rgba(0, 15, 35, 0.65)';
        ctx.fillRect(rightX, tapeY, 65, 240);
        ctx.strokeRect(rightX, tapeY, 65, 240);
        ctx.fillStyle = '#00e5ff';
        ctx.fillText('SPEED', rightX + 8, tapeY - 8);

        for (let i = -4; i <= 4; i++) {
            const yPos = h / 2 + i * 26;
            ctx.beginPath();
            ctx.moveTo(rightX, yPos);
            ctx.lineTo(rightX + 15, yPos);
            ctx.stroke();
            const curMach = Math.max(0, (mach + i * -0.2)).toFixed(1);
            ctx.fillText(`M ${curMach}`, rightX + 22, yPos + 3);
        }

        ctx.restore();
    }

    function drawTargetGimbal(tx, ty, t) {
        ctx.save();
        ctx.translate(tx, ty);

        // Outer Rotating Segmented Reticle
        ctx.rotate(t * 1.5);
        ctx.strokeStyle = '#00e5ff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, 36, 0, Math.PI * 0.4);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(0, 0, 36, Math.PI, Math.PI * 1.4);
        ctx.stroke();

        // Inner Counter-Rotating Reticle
        ctx.rotate(-t * 2.8);
        ctx.strokeStyle = '#00ff88';
        ctx.beginPath();
        ctx.arc(0, 0, 22, 0, Math.PI * 0.6);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(0, 0, 22, Math.PI, Math.PI * 1.6);
        ctx.stroke();

        // Center crosshair
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(-5, 0); ctx.lineTo(5, 0);
        ctx.moveTo(0, -5); ctx.lineTo(0, 5);
        ctx.stroke();

        // Target HUD label
        ctx.rotate(t * 1.3);
        ctx.font = '9px "Share Tech Mono", monospace';
        ctx.fillStyle = '#00ff88';
        ctx.fillText('LOCK: ACQUIRED', 42, -6);
        ctx.fillStyle = '#00e5ff';
        ctx.fillText('RNG: 4.8M', 42, 6);
        ctx.fillText('ID: 0x8F4', 42, 18);

        ctx.restore();
    }

    function drawLockPings() {
        for (let i = lockPings.length - 1; i >= 0; i--) {
            const p = lockPings[i];
            p.radius += 3.8;
            p.opacity -= 0.04;

            if (p.opacity <= 0 || p.radius >= p.maxRadius) {
                lockPings.splice(i, 1);
                continue;
            }

            ctx.save();
            ctx.strokeStyle = `rgba(0, 229, 255, ${p.opacity})`;
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = `rgba(0, 255, 136, ${p.opacity})`;
            ctx.font = '10px "Share Tech Mono", monospace';
            ctx.fillText(`TARGET LOCKED [${p.id}]`, p.x + p.radius + 6, p.y);
            ctx.restore();
        }
    }

    function drawPeripheralTelemetry(w, h) {
        ctx.save();
        ctx.font = '10px "Share Tech Mono", monospace';

        // Top Left
        ctx.fillStyle = '#00e5ff';
        ctx.fillText('J.A.R.V.I.S. // DIVYANSHU INDUSTRIES', 36, 68);
        ctx.fillStyle = 'rgba(0, 229, 255, 0.7)';
        ctx.fillText('NANOTECH SHIELD: 98.4%', 36, 84);
        ctx.fillText('STABILIZERS: ACTIVE', 36, 100);

        // Top Right
        ctx.textAlign = 'right';
        ctx.fillStyle = '#00ff88';
        ctx.fillText('IFF: DIVYANSHU VERMA // ALLIED', w - 36, 68);
        ctx.fillStyle = 'rgba(0, 229, 255, 0.7)';
        ctx.fillText('RADAR: AIR_SEARCH_ACTIVE', w - 36, 84);
        ctx.fillText('HEAT DISSIPATION: 894 K', w - 36, 100);

        // Bottom Left
        ctx.textAlign = 'left';
        ctx.fillStyle = '#00e5ff';
        ctx.fillText('KINETIC DEFENSE: CHARGED', 36, h - 68);
        ctx.fillStyle = 'rgba(0, 229, 255, 0.6)';
        ctx.fillText('REPULSORS: 100% READY', 36, h - 52);

        // Bottom Right
        ctx.textAlign = 'right';
        ctx.fillStyle = '#00ff88';
        ctx.fillText('HOTKEY: CMD+SHIFT+V [EXIT]', w - 36, h - 68);
        ctx.fillStyle = 'rgba(0, 229, 255, 0.6)';
        ctx.fillText('VISOR: SECURE PROTOCOL', w - 36, h - 52);

        ctx.restore();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initVisorHUD);
    } else {
        initVisorHUD();
    }
})();
