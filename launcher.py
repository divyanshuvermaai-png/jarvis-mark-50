#!/usr/bin/env python3
"""
J.A.R.V.I.S. Production System Launcher & Dispatcher
Entry point for CLI, 3D HUD, Remote Isolated Server, Voice Loop, and macOS Daemon.
"""
import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path

# ── 0. Virtual Environment Self-Bootstrap ──
_ROOT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _ROOT_DIR / ".venv" / "bin" / "python"
if not getattr(sys, "frozen", False) and _VENV_PYTHON.exists() and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PYTHON):
    try:
        os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)
    except Exception as e:
        print(f"[LAUNCHER ERROR] Failed to switch to virtual environment: {e}", file=sys.stderr)

LAUNCHAGENT_PLIST = Path.home() / "Library" / "LaunchAgents" / "com.divyanshu.jarvis.plist"
LOG_DIR = Path.home() / ".jarvis_system"


def run_diagnostics() -> int:
    """Run system health check and exit with appropriate status code."""
    from app.bootstrap import bootstrap_jarvis
    from core.diagnostics import SystemHealthCheck
    container = bootstrap_jarvis()
    report = SystemHealthCheck.inspect(container=container)

    print(f"\n=======================================================")
    print(f" J.A.R.V.I.S. DIAGNOSTIC HEALTH REPORT — {report.overall_status.value}")
    print(f"=======================================================")
    print(f"Unified RAM Usage: {report.memory_usage_pct}% ({report.free_ram_gb} GB available)")
    print(f"Disk Storage:      {report.disk_free_gb} GB free")
    print("\n[Subsystems]")
    for sub, det in report.subsystems.items():
        st = det.get("status", "UNKNOWN")
        det_str = ", ".join(f"{k}: {v}" for k, v in det.items() if k != "status")
        print(f"  • {sub.title():<18}: [{st}] {det_str}")

    if report.alerts:
        print("\n[Active Warnings/Alerts]")
        for a in report.alerts:
            print(f"  ⚠️  {a}")
    print("=======================================================\n")
    return 0 if report.is_operational() else 1


def run_telemetry():
    """Print a snapshot of system vitals and agent telemetry."""
    from app.bootstrap import bootstrap_jarvis
    from interfaces.telemetry import telemetry_engine
    import json
    container = bootstrap_jarvis()
    snap = telemetry_engine.get_snapshot(container=container)
    print(json.dumps(snap, indent=2))


def run_tests() -> int:
    """Execute complete test suite across all subsystems."""
    print("Executing full J.A.R.V.I.S. test suite...")
    cmd = [str(_VENV_PYTHON), "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    res = subprocess.run(cmd, cwd=str(_ROOT_DIR))
    return res.returncode


def manage_service(action: str) -> int:
    """Manage macOS LaunchAgent background service."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    plist_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.divyanshu.jarvis</string>
    <key>ProgramArguments</key>
    <array>
        <string>{_VENV_PYTHON}</string>
        <string>{_ROOT_DIR}/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{_ROOT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>{LOG_DIR}/jarvis_daemon.log</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR}/jarvis_daemon_err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""
    if action == "install":
        LAUNCHAGENT_PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(LAUNCHAGENT_PLIST, "w") as f:
            f.write(plist_template)
        print(f"✅ Created LaunchAgent at: {LAUNCHAGENT_PLIST}")
        subprocess.run(["launchctl", "load", "-w", str(LAUNCHAGENT_PLIST)])
        print("✅ J.A.R.V.I.S. service loaded and registered to run on login.")
        return 0

    elif action == "uninstall":
        if LAUNCHAGENT_PLIST.exists():
            subprocess.run(["launchctl", "unload", str(LAUNCHAGENT_PLIST)], stderr=subprocess.DEVNULL)
            LAUNCHAGENT_PLIST.unlink()
            print("✅ J.A.R.V.I.S. service uninstalled.")
        else:
            print("Notice: No service plist found.")
        return 0

    elif action == "start":
        if not LAUNCHAGENT_PLIST.exists():
            print("Error: LaunchAgent not installed. Run 'jarvis --service install' first.")
            return 1
        subprocess.run(["launchctl", "start", "com.divyanshu.jarvis"])
        print("✅ J.A.R.V.I.S. background daemon started.")
        return 0

    elif action == "stop":
        subprocess.run(["launchctl", "stop", "com.divyanshu.jarvis"])
        print("✅ J.A.R.V.I.S. background daemon stopped.")
        return 0

    elif action == "status":
        res = subprocess.run(["launchctl", "list", "com.divyanshu.jarvis"], capture_output=True, text=True)
        if res.returncode == 0:
            print("Status: J.A.R.V.I.S. LaunchAgent is REGISTERED & ACTIVE")
            print(res.stdout)
        else:
            print("Status: J.A.R.V.I.S. LaunchAgent is NOT running")
        return res.returncode

    else:
        print(f"Unknown service action: {action}. Use install|uninstall|start|stop|status")
        return 1


def start_hud():
    """Start local backend and open Electron HUD."""
    import socket
    # Check if port 5001 is already active
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_running = s.connect_ex(("127.0.0.1", 5001)) == 0
    s.close()

    backend_proc = None
    if not is_running:
        print("Starting J.A.R.V.I.S. Core backend on port 5001...")
        backend_proc = subprocess.Popen([str(_VENV_PYTHON), str(_ROOT_DIR / "main.py")], cwd=str(_ROOT_DIR))
        time.sleep(1.5)

    print("Launching Holographic 3D Visor / Electron...")
    try:
        subprocess.run(["npm", "start"], cwd=str(_ROOT_DIR))
    except KeyboardInterrupt:
        pass
    finally:
        if backend_proc:
            backend_proc.terminate()


def start_voice():
    """Start interactive hands-free voice loop."""
    from app.bootstrap import bootstrap_jarvis
    print("Initializing J.A.R.V.I.S. Neural Voice Pipeline...")
    container = bootstrap_jarvis()
    container.voice.start_interactive_session()


def main():
    parser = argparse.ArgumentParser(
        description="J.A.R.V.I.S. Autonomous AI Operating System — Master Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Unified Interfaces:
  jarvis                 Launch J.A.R.V.I.S. HUD (Default: Local 3D Visor, Voice, CLI, & Mac Automation)
  jarvis --hud           Launch J.A.R.V.I.S. HUD (Local 3D Visor, Voice, CLI, & Mac Automation)
  jarvis --remote        Launch J.A.R.V.I.S. Remote (Secure Internet Gateway with Passcode Gate)
  jarvis --service <cmd> Manage macOS background autostart (install|start|stop|status)
"""
    )
    parser.add_argument("--hud", "--gui", action="store_true", help="Launch J.A.R.V.I.S. HUD (default)")
    parser.add_argument("--remote", action="store_true", help="Launch J.A.R.V.I.S. Remote Gateway (port 5002)")
    parser.add_argument("--service", choices=["install", "uninstall", "start", "stop", "status"], help="Manage macOS LaunchAgent daemon")
    
    # Internal developer / test execution flags
    parser.add_argument("--test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--health", "--diagnostics", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--telemetry", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--voice", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.health:
        sys.exit(run_diagnostics())
    elif args.telemetry:
        run_telemetry()
        sys.exit(0)
    elif args.test:
        sys.exit(run_tests())
    elif args.service:
        sys.exit(manage_service(args.service))
    elif args.remote:
        print("Starting J.A.R.V.I.S. Remote Isolated Q&A Server (port 5002)...")
        try:
            subprocess.run([str(_VENV_PYTHON), str(_ROOT_DIR / "main_2.py")], cwd=str(_ROOT_DIR))
        except KeyboardInterrupt:
            pass
    elif args.cli:
        from interfaces.cli import run_cli
        run_cli()
    elif args.voice:
        start_voice()
    else:
        # Default: J.A.R.V.I.S. HUD (Local Mode)
        start_hud()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

