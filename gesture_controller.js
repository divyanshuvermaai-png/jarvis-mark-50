/**
 * gesture_controller.js - JARVIS Air Mouse & Holographic Gesture Engine
 * Dual-Engine Interaction:
 * 1. AIR MOUSE MODE (Default):
 *    - Point index finger to control macOS desktop mouse cursor with speed-adaptive EMA smoothing
 *    - Pinch (thumb + index) to Click
 *    - Quick double pinch to Double-Click
 *    - Pinch & hold to Drag & Drop
 *    - Two-finger (index + middle) vertical swipe to Scroll
 *    - Open palm thrust to fire Repulsor shockwave
 * 2. 3D MATRIX MODE:
 *    - 1-to-1 wrist dial rotation (no runaway spin)
 *    - Distance-normalized pinch-to-zoom (0.55x to 2.3x)
 *    - Mid-air 3D hologram position tracking
 *    - High-energy repulsor pulse
 */

(function() {
    let hands = null;
    let isTracking = false;
    let videoStream = null;
    let animId = null;
    let repulsorCooldown = false;
    let currentScale = 1.0;
    let lastFrameTime = performance.now();
    let frameCount = 0;
    const handHistory = [];

    // Mode state: 'air_mouse' | 'hologram'
    let gestureMode = 'air_mouse';

    // Air mouse state
    let screenW = 1280;
    let screenH = 832;
    let smoothX = 640;
    let smoothY = 416;
    let isDragging = false;
    let inPinchState = false;
    let inRightPinchState = false;
    let pinchStartTime = 0;
    let rightPinchStartTime = 0;
    let lastClickTime = 0;
    let lastScrollY = 0;
    let isScrolling = false;
    let frameTimer = null;

    // Electron IPC Renderer resolution
    let ipcRenderer = null;
    try {
        if (window.nodeRequire) ipcRenderer = window.nodeRequire('electron').ipcRenderer;
        else if (typeof require === 'function') ipcRenderer = require('electron').ipcRenderer;
    } catch(e) {}

    const HAND_CONNECTIONS = [
        [0,1],[1,2],[2,3],[3,4],        // Thumb
        [0,5],[5,6],[6,7],[7,8],        // Index
        [0,9],[9,10],[10,11],[11,12],   // Middle
        [0,13],[13,14],[14,15],[15,16], // Ring
        [0,17],[17,18],[18,19],[19,20], // Pinky
        [5,9],[9,13],[13,17]            // Palm base
    ];

    function getDist(p1, p2) {
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    async function syncScreenSize() {
        if (ipcRenderer) {
            try {
                const sz = await ipcRenderer.invoke('get-screen-size');
                if (sz && sz.width) { screenW = sz.width; screenH = sz.height; }
            } catch(e) {}
        } else {
            try {
                const r = await fetch('/api/desktop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'screen_size' })
                });
                const d = await r.json();
                if (d.success && d.data) {
                    screenW = d.data.width;
                    screenH = d.data.height;
                }
            } catch(e) {}
        }
    }

    function sendMouse(cmd) {
        if (ipcRenderer) {
            ipcRenderer.send('air-mouse-cmd', cmd);
        } else {
            const parts = cmd.split(' ');
            const c = parts[0];
            let body = {};
            if (c === 'M') body = { action: 'move', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'C') body = { action: 'click', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'RC') body = { action: 'right_click', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'DC') body = { action: 'double_click', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'D') body = { action: 'down', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'DR') body = { action: 'drag', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'U') body = { action: 'up', x: parseFloat(parts[1]), y: parseFloat(parts[2]) };
            else if (c === 'S') body = { action: 'scroll', direction: parseInt(parts[1]) > 0 ? 'up' : 'down', amount: Math.abs(parseInt(parts[1])) };
            fetch('/api/desktop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            }).catch(() => {});
        }
    }

    function setGestureMode(newMode) {
        gestureMode = newMode;
        const modeBtn = document.getElementById('gestureModeToggle');
        if (modeBtn) {
            if (gestureMode === 'air_mouse') {
                modeBtn.innerText = 'MODE: AIR MOUSE';
                modeBtn.style.background = 'rgba(0, 229, 255, 0.25)';
                modeBtn.style.color = '#00e5ff';
                modeBtn.style.borderColor = '#00e5ff';
                if (window.toast) window.toast('AIR MOUSE ENGAGED // POINT TO NAVIGATE');
            } else {
                modeBtn.innerText = 'MODE: 3D MATRIX';
                modeBtn.style.background = 'rgba(255, 170, 0, 0.25)';
                modeBtn.style.color = '#ffaa00';
                modeBtn.style.borderColor = '#ffaa00';
                if (window.toast) window.toast('3D MATRIX CONTROL ENGAGED');
            }
        }
        if (window.StarkAudio) window.StarkAudio.servoClick();
    }

    function resolveHandsClass() {
        if (window.Hands) return window.Hands;
        if (typeof window.nodeRequire === 'function') {
            try { return window.nodeRequire('@mediapipe/hands').Hands; } catch(e) {}
        }
        if (typeof require === 'function') {
            try { return require('@mediapipe/hands').Hands; } catch(e) {}
        }
        return null;
    }

    function initGestureSystem() {
        const btn = document.getElementById('gestureBtn');
        const dot = document.getElementById('gestureDot');
        const btnText = document.getElementById('gestureBtnText');
        const pipContainer = document.getElementById('gesturePipContainer');
        const videoEl = document.getElementById('gestureVideo');
        const canvasEl = document.getElementById('gestureCanvas');
        const modeBtn = document.getElementById('gestureModeToggle');
        if (!btn || !canvasEl || !videoEl) return;

        const ctx = canvasEl.getContext('2d');

        if (modeBtn) {
            modeBtn.addEventListener('click', () => {
                setGestureMode(gestureMode === 'air_mouse' ? 'hologram' : 'air_mouse');
            });
        }

        window.toggleGestures = function(force) {
            const target = typeof force === 'boolean' ? force : !isTracking;
            if (target && !isTracking) {
                startTracking();
            } else if (!target && isTracking) {
                stopTracking();
            }
            return isTracking;
        };

        window.setGestureMode = setGestureMode;

        // Global hotkeys: 'G' toggles camera sensor, 'M' toggles Air Mouse / 3D Matrix
        window.addEventListener('keydown', (e) => {
            if (['input', 'textarea'].includes(document.activeElement.tagName.toLowerCase())) return;
            if (e.key === 'g' || e.key === 'G') {
                window.toggleGestures();
            } else if (e.key === 'm' || e.key === 'M') {
                if (isTracking) {
                    setGestureMode(gestureMode === 'air_mouse' ? 'hologram' : 'air_mouse');
                }
            }
        });

        async function startTracking() {
            try {
                await syncScreenSize();
                const HandsClass = resolveHandsClass();
                if (!HandsClass) {
                    console.error("MediaPipe Hands class unresolved.");
                    if (window.toast) window.toast("GESTURE ENGINE ERROR: MEDIAPIPE UNRESOLVED");
                    return;
                }

                try {
                    videoStream = await navigator.mediaDevices.getUserMedia({
                        video: {
                            width: { ideal: 640 },
                            height: { ideal: 480 },
                            facingMode: 'user'
                        },
                        audio: false
                    });
                } catch (camErr) {
                    console.error("Camera access denied:", camErr);
                    if (window.toast) window.toast("CAMERA ACCESS DENIED // CHECK PERMISSIONS");
                    stopTracking();
                    return;
                }

                videoEl.srcObject = videoStream;
                await videoEl.play();

                // Wait for video stream dimensions to be ready
                await new Promise((resolve) => {
                    if (videoEl.videoWidth > 0 && videoEl.readyState >= 2) return resolve();
                    videoEl.onloadedmetadata = () => resolve();
                    setTimeout(resolve, 500);
                });

                pipContainer.style.display = 'block';
                dot.style.background = '#00e5ff';
                dot.style.boxShadow = '0 0 10px #00e5ff';
                btnText.innerText = 'GESTURES: ACTIVE';
                if (window.toast) window.toast('OPTIC GESTURE SENSOR ENGAGED // AIR MOUSE ONLINE');
                if (window.StarkAudio) window.StarkAudio.chirp(1400, 0.08);

                const isHttp = window.location.protocol.startsWith('http');
                const baseUri = isHttp ? `${window.location.origin}/vendor/mediapipe/` : 'vendor/mediapipe/';
                hands = new HandsClass({
                    locateFile: (file) => `${baseUri}${file}`
                });

                hands.setOptions({
                    maxNumHands: 1,
                    modelComplexity: 0,
                    minDetectionConfidence: 0.55,
                    minTrackingConfidence: 0.55
                });

                hands.onResults(onHandResults);
                isTracking = true;

                let isProcessing = false;

                function scheduleNextFrame() {
                    if (!isTracking) return;
                    if (frameTimer) { clearTimeout(frameTimer); frameTimer = null; }
                    if (animId) { cancelAnimationFrame(animId); animId = null; }

                    if (document.hidden || !document.hasFocus()) {
                        frameTimer = setTimeout(processFrame, 16);
                    } else {
                        animId = requestAnimationFrame(processFrame);
                    }
                }

                async function processFrame() {
                    if (!isTracking) return;
                    if (videoEl && videoEl.readyState >= 2 && videoEl.videoWidth > 0 && hands && !isProcessing) {
                        try {
                            isProcessing = true;
                            await hands.send({ image: videoEl });
                        } catch(err) {
                            console.warn("MediaPipe processing frame error:", err);
                        } finally {
                            isProcessing = false;
                        }
                    }
                    scheduleNextFrame();
                }

                scheduleNextFrame();

                window.addEventListener('focus', () => { if (isTracking) scheduleNextFrame(); });
                window.addEventListener('blur', () => { if (isTracking) scheduleNextFrame(); });
            } catch (err) {
                console.error("Gesture engine initialization failed:", err);
                stopTracking();
                if (window.toast) window.toast("GESTURE SENSOR UNAVAILABLE");
            }
        }

        function stopTracking() {
            isTracking = false;
            if (animId) {
                cancelAnimationFrame(animId);
                animId = null;
            }
            if (frameTimer) {
                clearTimeout(frameTimer);
                frameTimer = null;
            }
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
                videoStream = null;
            }
            if (videoEl) {
                videoEl.srcObject = null;
            }
            if (pipContainer) pipContainer.style.display = 'none';
            dot.style.background = '#555';
            dot.style.boxShadow = 'none';
            btnText.innerText = 'GESTURES: OFF';
            if (window.toast) window.toast('GESTURE SENSOR STANDBY');
            if (window.StarkAudio) window.StarkAudio.chirp(450, 0.08);
            if (window.HoloReactor) {
                window.HoloReactor.setGestureScale(1.0);
                window.HoloReactor.setGestureRotation(0, 0);
                window.HoloReactor.setGesturePosition(0, 0);
            }
            if (isDragging) {
                isDragging = false;
                sendMouse(`U ${Math.round(smoothX)} ${Math.round(smoothY)}`);
            }
        }

        btn.addEventListener('click', () => {
            if (isTracking) {
                stopTracking();
            } else {
                startTracking();
            }
        });

        function onHandResults(results) {
            frameCount++;
            const now = performance.now();
            if (now - lastFrameTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (now - lastFrameTime));
                const fpsEl = document.getElementById('gestureFps');
                if (fpsEl) fpsEl.innerText = `${fps} FPS`;
                frameCount = 0;
                lastFrameTime = now;
            }

            ctx.save();
            ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

            // Cybernetic HUD background with scanline grid
            ctx.fillStyle = 'rgba(0, 10, 24, 0.95)';
            ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);

            ctx.strokeStyle = 'rgba(0, 229, 255, 0.08)';
            ctx.lineWidth = 1;
            for (let x = 0; x < canvasEl.width; x += 18) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasEl.height); ctx.stroke();
            }
            for (let y = 0; y < canvasEl.height; y += 18) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvasEl.width, y); ctx.stroke();
            }

            const statusEl = document.getElementById('gestureStatusText');
            const metricEl = document.getElementById('gestureMetric');

            if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
                if (statusEl) statusEl.innerText = 'STATUS: SCANNING FOR HAND...';
                if (metricEl) metricEl.innerText = '0.00';
                handHistory.length = 0;
                if (isDragging) {
                    isDragging = false;
                    sendMouse(`U ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                }
                ctx.restore();
                return;
            }

            const lm = results.multiHandLandmarks[0];

            // ─── 1. DRAW TACTICAL HOLOGRAPHIC HAND SKELETON ───
            ctx.shadowBlur = 6;
            ctx.shadowColor = '#00e5ff';

            // Connect hand bones
            ctx.strokeStyle = '#00e5ff';
            ctx.lineWidth = 2.0;
            for (const [i, j] of HAND_CONNECTIONS) {
                const x1 = (1 - lm[i].x) * canvasEl.width; // mirror X for natural feel
                const y1 = lm[i].y * canvasEl.height;
                const x2 = (1 - lm[j].x) * canvasEl.width;
                const y2 = lm[j].y * canvasEl.height;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }

            // Draw joint nodes
            for (let i = 0; i < lm.length; i++) {
                const x = (1 - lm[i].x) * canvasEl.width;
                const y = lm[i].y * canvasEl.height;
                ctx.beginPath();
                ctx.arc(x, y, [4, 8, 12, 16, 20].includes(i) ? 3.8 : 2.0, 0, Math.PI * 2);
                ctx.fillStyle = [4, 8, 12, 16, 20].includes(i) ? '#00ff88' : '#ff7700';
                ctx.fill();
            }

            // Palm center coordinate (midpoint of wrist 0 and knuckles 5 & 17)
            const palmX = (1 - (lm[0].x + lm[5].x + lm[17].x) / 3) * canvasEl.width;
            const palmY = ((lm[0].y + lm[5].y + lm[17].y) / 3) * canvasEl.height;

            const wrist = lm[0];
            const thumbTip = lm[4];
            const indexTip = lm[8];
            const middleTip = lm[12];
            const ringTip = lm[16];
            const pinkyTip = lm[20];

            // Hand Length for distance normalization
            const handLength = Math.max(0.08, getDist(wrist, lm[9]));

            // Finger extension states
            const isIndexOpen = getDist(indexTip, wrist) > getDist(lm[6], wrist) * 1.12;
            const isMiddleOpen = getDist(middleTip, wrist) > getDist(lm[10], wrist) * 1.12;
            const isRingOpen = getDist(ringTip, wrist) > getDist(lm[14], wrist) * 1.12;
            const isPinkyOpen = getDist(pinkyTip, wrist) > getDist(lm[18], wrist) * 1.12;
            const isThumbOpen = getDist(thumbTip, wrist) > getDist(lm[2], wrist) * 1.12;
            const openCount = [isIndexOpen, isMiddleOpen, isRingOpen, isPinkyOpen, isThumbOpen].filter(Boolean).length;
            const isOpenPalm = openCount >= 4;

            // Distance between thumb tip and index tip normalized by hand length
            const normalizedPinch = getDist(thumbTip, indexTip) / handLength;
            const normalizedMiddlePinch = getDist(thumbTip, middleTip) / handLength;

            // Hysteresis for rock-solid left click / pinch detection
            if (!inPinchState && normalizedPinch < 0.44) {
                inPinchState = true;
            } else if (inPinchState && normalizedPinch > 0.52) {
                inPinchState = false;
            }

            // Hysteresis for right click (thumb + middle finger pinch)
            if (!inRightPinchState && normalizedMiddlePinch < 0.44 && normalizedPinch > 0.48) {
                inRightPinchState = true;
            } else if (inRightPinchState && (normalizedMiddlePinch > 0.52 || normalizedPinch < 0.44)) {
                inRightPinchState = false;
            }

            // Record hand size history for repulsor shockwave detection
            handHistory.push({ length: handLength, time: now });
            if (handHistory.length > 8) handHistory.shift();

            // ── GESTURE: PALM REPULSOR SHOCKWAVE (COMMON TO BOTH MODES) ──
            if (isOpenPalm && !repulsorCooldown && handHistory.length >= 4) {
                const oldest = handHistory[0];
                const deltaSize = handLength - oldest.length;
                const deltaTime = (now - oldest.time) / 1000;
                const velocity = deltaSize / Math.max(0.05, deltaTime);

                if (velocity > 0.45 || handLength > 0.38) {
                    repulsorCooldown = true;
                    if (statusEl) statusEl.innerText = '⚡ REPULSOR DISCHARGE!';
                    if (metricEl) metricEl.innerText = 'MAX SHOCKWAVE';

                    if (window.HoloReactor) window.HoloReactor.pulse(3.5);
                    if (window.JarvisAudio) window.JarvisAudio.repulsorBurst();
                    if (window.toast) window.toast('TACTICAL REPULSOR SHOCKWAVE FIRED');

                    ctx.fillStyle = 'rgba(0, 229, 255, 0.45)';
                    ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);

                    setTimeout(() => { repulsorCooldown = false; }, 1200);
                    ctx.restore();
                    return;
                }
            }

            // ═══════════════════════════════════════════════════════════════
            // MODE 1: JARVIS AIR MOUSE (DESKTOP CURSOR CONTROL)
            // ═══════════════════════════════════════════════════════════════
            if (gestureMode === 'air_mouse') {
                const camX = 1 - indexTip.x;
                const camY = indexTip.y;

                // Active interaction window mapping (covers natural reach to all 4 screen edges)
                const normX = Math.max(0, Math.min(1, (camX - 0.12) / 0.76));
                const normY = Math.max(0, Math.min(1, (camY - 0.12) / 0.76));

                const targetX = normX * screenW;
                const targetY = normY * screenH;

                // Adaptive Exponential Moving Average smoothing
                const deltaDist = Math.hypot(targetX - smoothX, targetY - smoothY);
                const alpha = deltaDist > 45 ? 0.65 : (deltaDist > 12 ? 0.42 : 0.26);
                smoothX += (targetX - smoothX) * alpha;
                smoothY += (targetY - smoothY) * alpha;

                // 1. Two-Finger Scroll Mode (peace sign ✌️)
                const isTwoFingerScroll = isIndexOpen && isMiddleOpen && !inPinchState && !inRightPinchState && (getDist(indexTip, middleTip) / handLength < 0.50);
                if (isTwoFingerScroll) {
                    const currentScrollY = (indexTip.y + middleTip.y) / 2;
                    if (!isScrolling) {
                        isScrolling = true;
                        lastScrollY = currentScrollY;
                    } else {
                        const diff = currentScrollY - lastScrollY;
                        if (Math.abs(diff) > 0.012) {
                            const delta = diff > 0 ? -3 : 3;
                            sendMouse(`S ${delta}`);
                            lastScrollY = currentScrollY;
                        }
                    }
                    if (statusEl) statusEl.innerText = '⚡ TWO-FINGER SCROLL';
                    if (metricEl) metricEl.innerText = 'SCROLL';
                } else {
                    isScrolling = false;

                    // 2. Right-Click: Thumb to Middle Finger Pinch
                    if (inRightPinchState) {
                        if (!rightPinchStartTime) {
                            rightPinchStartTime = now;
                        }
                        if (statusEl) statusEl.innerText = '⚡ RIGHT PINCH';
                        if (metricEl) metricEl.innerText = 'RIGHT';
                    } else {
                        if (rightPinchStartTime > 0) {
                            const rDuration = now - rightPinchStartTime;
                            if (rDuration < 400) {
                                sendMouse(`RC ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                if (window.JarvisAudio) window.JarvisAudio.chirp(850, 0.06);
                                if (statusEl) statusEl.innerText = '⚡ RIGHT CLICK!';
                            }
                            rightPinchStartTime = 0;
                        }

                        // 3. Left Click, Double Click & Drag: Thumb to Index Pinch
                        if (inPinchState) {
                            if (!pinchStartTime) {
                                pinchStartTime = now;
                            } else if (now - pinchStartTime > 260 && !isDragging) {
                                isDragging = true;
                                sendMouse(`D ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                if (window.JarvisAudio) window.JarvisAudio.chirp(700, 0.04);
                            }

                            if (isDragging) {
                                sendMouse(`DR ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                if (statusEl) statusEl.innerText = '⚡ DRAGGING...';
                                if (metricEl) metricEl.innerText = 'DRAG';
                            } else {
                                if (statusEl) statusEl.innerText = '⚡ PINCH DETECTED';
                                if (metricEl) metricEl.innerText = 'PINCH';
                            }
                        } else {
                            if (pinchStartTime > 0) {
                                const duration = now - pinchStartTime;
                                if (isDragging) {
                                    isDragging = false;
                                    sendMouse(`U ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                    if (window.JarvisAudio) window.JarvisAudio.chirp(550, 0.04);
                                } else if (duration < 260) {
                                    if (now - lastClickTime < 380) {
                                        sendMouse(`DC ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                        if (window.JarvisAudio) {
                                            window.JarvisAudio.chirp(1200, 0.03);
                                            setTimeout(() => window.JarvisAudio && window.JarvisAudio.chirp(1450, 0.03), 80);
                                        }
                                        if (statusEl) statusEl.innerText = '⚡ DOUBLE CLICK!';
                                        lastClickTime = 0;
                                    } else {
                                        sendMouse(`C ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                        if (window.JarvisAudio) window.JarvisAudio.servoClick();
                                        if (statusEl) statusEl.innerText = '⚡ CLICK!';
                                        lastClickTime = now;
                                    }
                                }
                                pinchStartTime = 0;
                            } else {
                                // Normal cursor movement
                                sendMouse(`M ${Math.round(smoothX)} ${Math.round(smoothY)}`);
                                if (statusEl) statusEl.innerText = 'AIR MOUSE: TRACKING';
                                if (metricEl) metricEl.innerText = `${Math.round(smoothX)}, ${Math.round(smoothY)}`;
                            }
                        }
                    }
                }

                // Draw laser pointer reticle on index finger tip
                const tipCanvasX = camX * canvasEl.width;
                const tipCanvasY = camY * canvasEl.height;
                const thumbCanvasX = (1 - thumbTip.x) * canvasEl.width;
                const thumbCanvasY = thumbTip.y * canvasEl.height;
                const middleCanvasX = (1 - middleTip.x) * canvasEl.width;
                const middleCanvasY = middleTip.y * canvasEl.height;

                // Draw glowing laser connector between pinched fingers
                if (inPinchState) {
                    ctx.strokeStyle = '#00ff88';
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.moveTo(tipCanvasX, tipCanvasY);
                    ctx.lineTo(thumbCanvasX, thumbCanvasY);
                    ctx.stroke();
                } else if (inRightPinchState) {
                    ctx.strokeStyle = '#ff9900';
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.moveTo(middleCanvasX, middleCanvasY);
                    ctx.lineTo(thumbCanvasX, thumbCanvasY);
                    ctx.stroke();
                }

                ctx.strokeStyle = inPinchState ? '#00ff88' : (inRightPinchState ? '#ff9900' : '#00e5ff');
                ctx.lineWidth = inPinchState || inRightPinchState ? 2.5 : 1.8;
                ctx.beginPath();
                ctx.arc(tipCanvasX, tipCanvasY, inPinchState ? 10 : 6, 0, Math.PI * 2);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(tipCanvasX - 12, tipCanvasY); ctx.lineTo(tipCanvasX + 12, tipCanvasY);
                ctx.moveTo(tipCanvasX, tipCanvasY - 12); ctx.lineTo(tipCanvasX, tipCanvasY + 12);
                ctx.stroke();

                ctx.restore();
                return;
            }

            // ═══════════════════════════════════════════════════════════════
            // MODE 2: 3D MATRIX CONTROL (HOLOGRAM ARC REACTOR & MARK SUIT)
            // ═══════════════════════════════════════════════════════════════
            const normPalmX = (palmX / canvasEl.width) - 0.5;
            const normPalmY = (palmY / canvasEl.height) - 0.5;
            if (window.HoloReactor) {
                window.HoloReactor.setGesturePosition(normPalmX * 2.2, -normPalmY * 1.6);
            }

            // Pinch Zoom
            if (isPinching) {
                const ix = (1 - indexTip.x) * canvasEl.width;
                const iy = indexTip.y * canvasEl.height;
                const tx = (1 - thumbTip.x) * canvasEl.width;
                const ty = thumbTip.y * canvasEl.height;

                ctx.strokeStyle = '#00ff88';
                ctx.lineWidth = 2.5;
                ctx.beginPath();
                ctx.moveTo(ix, iy);
                ctx.lineTo(tx, ty);
                ctx.stroke();

                const targetScale = Math.max(0.55, Math.min(2.3, 0.45 + normalizedPinch * 2.8));
                currentScale += (targetScale - currentScale) * 0.2;

                if (window.HoloReactor) window.HoloReactor.setGestureScale(currentScale);

                if (statusEl) statusEl.innerText = 'GESTURE: PINCH ZOOM';
                if (metricEl) metricEl.innerText = `x${currentScale.toFixed(2)}`;
                ctx.restore();
                return;
            }

            // 1-to-1 Wrist Dial Rotation
            const deltaX = (1 - middleTip.x) - (1 - wrist.x);
            const deltaY = middleTip.y - wrist.y;
            const wristAngle = Math.atan2(deltaY, deltaX) + Math.PI / 2;

            if (window.HoloReactor) {
                window.HoloReactor.setGestureRotation(-wristAngle * 1.5, normPalmX * 0.4);
            }

            if (statusEl) statusEl.innerText = 'GESTURE: DIAL ROTATE';
            const degrees = Math.round((-wristAngle * 180) / Math.PI);
            if (metricEl) metricEl.innerText = `${degrees}°`;

            ctx.restore();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGestureSystem);
    } else {
        initGestureSystem();
    }
})();
