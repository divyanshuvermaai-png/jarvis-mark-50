"""
J.A.R.V.I.S. Subsystem Diagnostic Engine
Probes real system readiness across:
- Local Gemma MLX GPU
- Long-term Memory & Soul
- Desktop Automation (Swift mouse_helper & controllers)
- Vision Framework & OCR
- MediaPipe Gesture Engine
- Live Hardware Telemetry
"""
import os
import psutil
import shutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.expanduser("~/.jarvis_system")

def probe_subsystems():
    """Verify live status of each J.A.R.V.I.S. subsystem using actual file/hardware checks."""
    diagnostics = {}

    # 1. AI Model & Apple Silicon MLX GPU
    try:
        import gemma_local
        if gemma_local.is_gemma_available():
            diagnostics['ai_status'] = 'READY'
            diagnostics['ai_engine'] = 'Apple MLX (GPU Accelerated)'
            diagnostics['ai_model'] = 'Gemma 4 E2B 4-bit'
        else:
            diagnostics['ai_status'] = 'UNAVAILABLE'
            diagnostics['ai_engine'] = 'Cloud Fallback'
            diagnostics['ai_model'] = 'Gemini 2.5 Flash'
    except Exception as e:
        diagnostics['ai_status'] = 'ERROR'
        diagnostics['ai_engine'] = str(e)
        diagnostics['ai_model'] = 'None'

    # 2. Memory & Soul
    soul_file = os.path.join(CONFIG_DIR, "soul.md")
    memory_file = os.path.join(CONFIG_DIR, "memory.md")
    if os.path.exists(soul_file) and os.path.exists(memory_file):
        diagnostics['memory_status'] = 'LOADED'
    else:
        diagnostics['memory_status'] = 'INITIALIZING'

    # 3. Desktop Automation & Native Swift Mouse Helper
    mouse_binary = os.path.join(BASE_DIR, "mouse_helper")
    has_mouse = os.path.exists(mouse_binary) and os.access(mouse_binary, os.X_OK)
    has_controller = os.path.exists(os.path.join(BASE_DIR, "desktop_controller", "__init__.py"))
    if has_mouse and has_controller:
        diagnostics['desktop_status'] = 'READY'
    else:
        diagnostics['desktop_status'] = 'PARTIAL'

    # 4. System Integration
    has_osascript = shutil.which("osascript") is not None
    diagnostics['system_integration'] = 'READY' if has_osascript else 'LIMITED'

    # 5. Vision Engine (Apple Vision OCR & Screencapture)
    has_screencapture = shutil.which("screencapture") is not None
    diagnostics['vision_status'] = 'READY' if has_screencapture else 'DISABLED'

    # 6. Gesture Engine (MediaPipe & Electron hooks)
    gesture_file = os.path.join(BASE_DIR, "gesture_controller.js")
    node_mp = os.path.exists(os.path.join(BASE_DIR, "node_modules", "@mediapipe", "hands"))
    diagnostics['gesture_status'] = 'READY' if os.path.exists(gesture_file) else 'STANDBY'

    # 7. Hardware Telemetry
    diagnostics['cpu_percent'] = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    diagnostics['ram_percent'] = mem.percent
    diagnostics['ram_used_gb'] = round(mem.used / (1024 ** 3), 1)
    diagnostics['ram_total_gb'] = round(mem.total / (1024 ** 3), 1)

    battery = psutil.sensors_battery()
    diagnostics['battery_percent'] = battery.percent if battery else 100
    diagnostics['battery_charging'] = battery.power_plugged if battery else True

    # 8. Overall Status Determination
    critical_ok = (
        diagnostics['ai_status'] == 'READY' and
        diagnostics['memory_status'] == 'LOADED' and
        diagnostics['desktop_status'] == 'READY' and
        diagnostics['system_integration'] == 'READY'
    )
    diagnostics['overall_status'] = 'FULL POWER' if critical_ok else 'ONLINE (REDUCED)'

    return diagnostics

def format_remote_banner(diagnostics, local_url=None, gateway_url=None, passcode=None):
    """Format the official J.A.R.V.I.S. Remote Q&A Mode startup dashboard."""
    ai_model = diagnostics.get('ai_model', 'Gemma 4 E2B 4-bit')
    remote_access = "SECURE (TUNNEL ACTIVE)" if gateway_url else "STANDBY"

    banner = f"""========================================================
J.A.R.V.I.S. v5.0.0
REMOTE Q&A MODE
========================================================

AI:                 {ai_model}
ENGINE:             Apple MLX
BACKEND:            ONLINE
MEMORY:             ISOLATED (READ-ONLY / LOCAL ONLY)
SYSTEM INTEGRATION: STANDBY
DESKTOP AUTOMATION: DISABLED (ZERO MAC ACCESS)
VISION:             DISABLED (ZERO MAC ACCESS)
REMOTE ACCESS:      {remote_access}
CAPABILITY:         Q&A ONLY (NO MAC AUTOMATION)
STATUS:             ONLINE
========================================================"""

    if local_url:
        banner += f"\n\n[LOCAL GATEWAY]     {local_url}"
    if gateway_url:
        banner += f"\n[SECURE TUNNEL]     {gateway_url}"
    if passcode:
        banner += f"\n[SESSION PASSCODE]  {passcode}"

    return banner


