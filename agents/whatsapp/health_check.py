"""
J.A.R.V.I.S. WhatsApp Agent - Health Check Diagnostics
Verifies application installation, process status, accessibility permissions,
and automation bridge readiness.
"""
import os
import subprocess
from typing import Dict, Any


class WhatsAppHealthCheck:
    """
    Diagnostics provider for the WhatsApp subsystem.
    """

    APP_PATHS = [
        "/Applications/WhatsApp.app",
        os.path.expanduser("~/Applications/WhatsApp.app")
    ]

    @classmethod
    def check_installed(cls) -> bool:
        """Checks if WhatsApp Desktop is installed on the Mac."""
        return any(os.path.exists(p) for p in cls.APP_PATHS)

    @classmethod
    def check_running(cls) -> bool:
        """Checks if WhatsApp is currently running."""
        try:
            res = subprocess.run(['pgrep', '-f', 'WhatsApp'], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def check_accessibility(cls) -> bool:
        """Verifies if macOS Accessibility scripting is permitted."""
        script = 'tell application "System Events" to return count of processes'
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def inspect(cls, is_mock_mode: bool = False) -> Dict[str, Any]:
        """
        Executes full health check inspection and returns structured telemetry.
        """
        if is_mock_mode:
            return {
                "healthy": True,
                "installed": True,
                "app_installed": True,
                "running": True,
                "process_running": True,
                "accessibility_granted": True,
                "mock_mode": True,
                "mode": "MOCK_SIMULATION",
                "privacy_mode": "STRICT_LOCAL",
                "summary": "WhatsApp Mock Simulation active. All communication tests running safely offline."
            }

        installed = cls.check_installed()
        running = cls.check_running()
        accessibility = cls.check_accessibility()

        healthy = installed and accessibility

        if not installed:
            summary = "WhatsApp Desktop is not installed in standard macOS application directories."
        elif not accessibility:
            summary = "WhatsApp is installed, but J.A.R.V.I.S. does not currently have macOS Accessibility permission."
        elif not running:
            summary = "WhatsApp Desktop is installed and permissions are granted (App is currently idle/closed)."
        else:
            summary = "WhatsApp Desktop is installed, running, and desktop automation is fully operational."

        return {
            "healthy": healthy,
            "installed": installed,
            "app_installed": installed,
            "running": running,
            "process_running": running,
            "accessibility_granted": accessibility,
            "mock_mode": False,
            "mode": "NATIVE_DESKTOP",
            "privacy_mode": "STRICT_LOCAL",
            "summary": summary
        }
