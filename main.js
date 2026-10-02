const { app, BrowserWindow, session, systemPreferences, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

// Enable autoplay without requiring user interaction
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

let mainWindow;
let startupWindow;
let pythonProcess;
let startupAudioProcess = null;

// ── Startup Audio Helper ──
function playStartupSound() {
    if (startupAudioProcess) {
        try { startupAudioProcess.kill(); } catch (e) {}
        startupAudioProcess = null;
    }

    const isDev = !app.isPackaged;
    let soundPath = path.join(__dirname, 'start up sound', 'jarvis.wav');
    if (!fs.existsSync(soundPath)) {
        soundPath = path.join(__dirname, 'startup', 'dist', 'jarvis.wav');
    }
    if (!fs.existsSync(soundPath) && !isDev) {
        soundPath = path.join(process.resourcesPath, 'start up sound', 'jarvis.wav');
    }

    if (fs.existsSync(soundPath)) {
        console.log('[MAIN AUDIO] Playing startup sound via afplay:', soundPath);
        try {
            startupAudioProcess = spawn('afplay', [soundPath]);
            startupAudioProcess.on('error', (err) => console.error('[MAIN AUDIO ERROR]:', err));
            startupAudioProcess.on('exit', (code) => {
                console.log('[MAIN AUDIO] Playback finished with code:', code);
                startupAudioProcess = null;
            });
        } catch (err) {
            console.error('[MAIN AUDIO] Failed to spawn afplay:', err);
        }
    } else {
        console.warn('[MAIN AUDIO] Startup sound file not found at:', soundPath);
    }
}

function stopStartupSound() {
    if (startupAudioProcess) {
        console.log('[MAIN AUDIO] Stopping startup sound playback...');
        try { startupAudioProcess.kill(); } catch (e) {}
        startupAudioProcess = null;
    }
}

// ── Native High-Speed CoreGraphics Mouse Helper ──
let mouseHelperProcess = null;
let screenResolution = { width: 1280, height: 832 };

function initMouseHelper() {
    let helperPath = path.join(__dirname, 'mouse_helper');
    if (!fs.existsSync(helperPath) && process.resourcesPath) {
        const alt = path.join(process.resourcesPath, 'mouse_helper');
        if (fs.existsSync(alt)) helperPath = alt;
    }
    if (fs.existsSync(helperPath)) {
        try {
            if (mouseHelperProcess) {
                try { mouseHelperProcess.kill(); } catch(e) {}
            }
            mouseHelperProcess = spawn(helperPath, [], { stdio: ['pipe', 'pipe', 'inherit'] });
            mouseHelperProcess.stdout.on('data', (data) => {
                const str = data.toString().trim();
                if (str.startsWith('READY')) {
                    const parts = str.split(' ');
                    screenResolution.width = parseInt(parts[1]) || 1280;
                    screenResolution.height = parseInt(parts[2]) || 832;
                    console.log('[MAIN MOUSE] Native CoreGraphics engine online. Screen:', screenResolution);
                }
            });
            mouseHelperProcess.on('error', (err) => console.warn('[MAIN MOUSE ERROR]:', err));
            mouseHelperProcess.on('exit', () => { mouseHelperProcess = null; });
        } catch(e) {
            console.warn('[MAIN MOUSE] Failed to spawn mouse_helper:', e);
        }
    } else {
        console.warn('[MAIN MOUSE] Binary not found at:', helperPath);
    }
}

ipcMain.on('air-mouse-cmd', (event, cmd) => {
    if (!mouseHelperProcess || !mouseHelperProcess.stdin.writable) {
        initMouseHelper();
    }
    if (mouseHelperProcess && mouseHelperProcess.stdin.writable) {
        mouseHelperProcess.stdin.write(cmd + '\n');
    }
});

ipcMain.handle('get-screen-size', () => {
    return screenResolution;
});

// ── Startup Window (Cinematic Boot Sequence) ──
function createStartupWindow() {
    startupWindow = new BrowserWindow({
        fullscreen: true,
        frame: false,
        transparent: false,
        backgroundColor: '#000000',
        show: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false, // Allow loading local audio files
        },
    });

    // Load the built startup sequence
    const isDev = !app.isPackaged;
    if (isDev) {
        // In dev, load from the Vite build output
        const startupPath = path.join(__dirname, 'startup', 'dist', 'index.html');
        startupWindow.loadFile(startupPath);
    } else {
        const startupPath = path.join(process.resourcesPath, 'startup', 'index.html');
        startupWindow.loadFile(startupPath);
    }

    startupWindow.once('ready-to-show', () => {
        startupWindow.show();
        // Play the startup sound right when the window displays
        playStartupSound();
    });

    startupWindow.on('closed', () => {
        startupWindow = null;
        stopStartupSound();
    });
}

// ── Main JARVIS Window ──
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        frame: false, // Frameless window
        transparent: true, // Glass effect capability
        show: false, // Don't show until ready
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            // Enable media stream (microphone) for speech recognition
            webSecurity: true,
            backgroundThrottling: false // Keep camera, AI, and gestures running at full 60 FPS in background
        },
        icon: path.join(__dirname, 'icon.icns')
    });

    // Check if the python server is up before loading
    // IMPORTANT: Load via HTTP URL (not file://) so webkitSpeechRecognition works
    const checkServer = () => {
        http.get('http://127.0.0.1:5001/api/status', (res) => {
            if (res.statusCode === 200) {
                mainWindow.loadURL('http://127.0.0.1:5001');
                mainWindow.once('ready-to-show', () => {
                    mainWindow.show();
                    // Close startup window with a slight delay for smooth transition
                    if (startupWindow && !startupWindow.isDestroyed()) {
                        setTimeout(() => {
                            if (startupWindow && !startupWindow.isDestroyed()) {
                                startupWindow.close();
                            }
                        }, 500);
                    }
                });
            } else {
                setTimeout(checkServer, 500);
            }
        }).on('error', () => {
            setTimeout(checkServer, 500);
        });
    };

    checkServer();

    // Auto-grant microphone and camera permissions for voice and gesture tracking
    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
        const allowedPermissions = ['media', 'microphone', 'audioCapture', 'camera', 'videoCapture'];
        if (allowedPermissions.includes(permission)) {
            callback(true);
        } else {
            callback(false);
        }
    });
    
    session.defaultSession.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
        const allowedPermissions = ['media', 'microphone', 'audioCapture', 'camera', 'videoCapture'];
        if (allowedPermissions.includes(permission)) {
            return true;
        }
        return false;
    });

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

// ── IPC: Startup Audio and Completion ──
ipcMain.on('play-startup-sound', () => {
    playStartupSound();
});

ipcMain.on('stop-startup-sound', () => {
    stopStartupSound();
});

ipcMain.on('startup-complete', () => {
    console.log('[JARVIS] Startup sequence complete. Loading main interface...');
    stopStartupSound();
    createWindow();
});

app.whenReady().then(async () => {
    // Request macOS microphone & camera permissions
    if (process.platform === 'darwin') {
        const micAccess = await systemPreferences.askForMediaAccess('microphone');
        console.log('Microphone OS access:', micAccess);
        try {
            const camAccess = await systemPreferences.askForMediaAccess('camera');
            console.log('Camera OS access:', camAccess);
        } catch(e) {
            console.warn('Camera permission check warning:', e);
        }
    }

    // Determine if we are running the compiled binary or the python script
    const isPackaged = app.isPackaged;
    
    if (isPackaged) {
        // Run the PyInstaller executable from resources
        const coreDir = path.join(process.resourcesPath, 'jarvis_core');
        const executablePath = path.join(coreDir, 'jarvis_backend');
        pythonProcess = spawn(executablePath, [], { shell: true, cwd: coreDir });
    } else {
        // Run via .venv python if present, else fallback to python3
        const venvPython = path.join(__dirname, '.venv', 'bin', 'python');
        const pythonCmd = fs.existsSync(venvPython) ? venvPython : 'python3';
        pythonProcess = spawn(pythonCmd, ['main.py'], { cwd: __dirname });
    }

    pythonProcess.stdout.on('data', (data) => console.log(`[CORE]: ${data}`));
    pythonProcess.stderr.on('data', (data) => console.error(`[CORE ERR]: ${data}`));

    // Initialize native CoreGraphics air mouse engine
    initMouseHelper();

    // Show startup sequence first (instead of going directly to main window)
    createStartupWindow();

    app.on('activate', function () {
        if (mainWindow === null && startupWindow === null) createStartupWindow();
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
    stopStartupSound();
    if (mouseHelperProcess) {
        try { mouseHelperProcess.stdin.write('Q\n'); mouseHelperProcess.kill(); } catch (e) {}
        mouseHelperProcess = null;
    }
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
