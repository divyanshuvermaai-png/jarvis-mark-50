"""
J.A.R.V.I.S. macOS System Control & Utilities Tool
Provides direct native control for audio volume, screen locking, WiFi status,
clipboard manipulation, and desktop notifications.
"""
import subprocess
import logging
from typing import Dict, Any

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier

logger = logging.getLogger("jarvis.tools.system_control")


class SystemControlTool(BaseTool):
    @property
    def id(self) -> str:
        return "system_control"

    @property
    def name(self) -> str:
        return "macOS System Control"

    @property
    def description(self) -> str:
        return "Control macOS system state: adjust volume (0-100), lock screen, query WiFi status, get/set clipboard, or trigger native notifications."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set_volume", "get_volume", "lock_screen", "wifi_status", "get_clipboard", "set_clipboard", "notify"],
                    "description": "System control action to execute."
                },
                "value": {
                    "type": "string",
                    "description": "Volume level (0-100), clipboard text, or notification message depending on action."
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for native notification (defaults to 'J.A.R.V.I.S.')."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.SYSTEM_ADMIN

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        val = str(params.get("value", "")).strip()
        title = params.get("title", "J.A.R.V.I.S.").strip()

        try:
            if action == "set_volume":
                try:
                    vol = max(0, min(100, int(val)))
                except ValueError:
                    return ToolResult(success=False, error="Volume value must be an integer between 0 and 100.")
                script = f"set volume output volume {vol}"
                subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
                return ToolResult(success=True, data=f"System volume set to {vol}%.")

            elif action == "get_volume":
                script = "output volume of (get volume settings)"
                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
                vol = res.stdout.strip()
                return ToolResult(success=True, data=f"Current system volume is {vol}%.", metadata={"volume": vol})

            elif action == "lock_screen":
                # Instant macOS screen lock via CoreGraphics Session
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"], capture_output=True)
                return ToolResult(success=True, data="macOS screen locked.")

            elif action == "wifi_status":
                res = subprocess.run(["networksetup", "-getairportnetwork", "en0"], capture_output=True, text=True)
                out = res.stdout.strip()
                if "Current Wi-Fi Network:" in out:
                    ssid = out.replace("Current Wi-Fi Network:", "").strip()
                    return ToolResult(success=True, data=f"Connected to Wi-Fi: '{ssid}'.", metadata={"ssid": ssid})
                return ToolResult(success=True, data=out or "Wi-Fi is disconnected or device en0 unavailable.")

            elif action == "get_clipboard":
                res = subprocess.run(["pbpaste"], capture_output=True, text=True)
                clip_text = res.stdout
                return ToolResult(success=True, data=clip_text if clip_text else "(Clipboard is empty)")

            elif action == "set_clipboard":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                proc.communicate(input=val.encode("utf-8"))
                return ToolResult(success=True, data=f"Copied {len(val)} characters to clipboard.")

            elif action == "notify":
                escaped_msg = val.replace('\\', '\\\\').replace('"', '\\"')
                escaped_title = title.replace('\\', '\\\\').replace('"', '\\"')
                script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
                subprocess.run(["osascript", "-e", script], capture_output=True, check=True)
                return ToolResult(success=True, data=f"Notification dispatched: '{escaped_title}' - '{escaped_msg}'")

            else:
                return ToolResult(success=False, error=f"Unknown system control action: '{action}'")

        except Exception as e:
            logger.error(f"SystemControl error ({action}): {e}")
            return ToolResult(success=False, error=f"System control failed: {str(e)}")
