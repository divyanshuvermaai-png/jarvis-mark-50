"""
J.A.R.V.I.S. macOS Keyboard Automation Tool
Executes typing, single keystrokes, and keyboard shortcuts safely on macOS.
"""
from typing import Dict, Any, List
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from desktop_controller.keyboard import KeyboardController

class MacOSKeyboardTool(BaseTool):
    @property
    def id(self) -> str:
        return "macos_keyboard"

    @property
    def name(self) -> str:
        return "macOS Keyboard Controller"

    @property
    def description(self) -> str:
        return (
            "Control macOS keyboard input. "
            "Supports actions: 'type' (enter text), 'press' (single key e.g. 'return', 'tab', 'escape'), "
            "and 'hotkey' (shortcut combo e.g. keys=['command', 'c'])."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["type", "press", "hotkey"],
                    "description": "Keyboard operation to execute."
                },
                "text": {
                    "type": "string",
                    "description": "Text string to type (required for 'type')."
                },
                "key": {
                    "type": "string",
                    "description": "Key name to press (required for 'press', e.g. 'return', 'tab', 'f5')."
                },
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of keys for shortcut combination (e.g. ['command', 'space'])."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.KEYBOARD_CONTROL

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.HIGH

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()

        try:
            if action == "type":
                text = params.get("text", "")
                if not text:
                    return ToolResult(success=False, error="Parameter 'text' cannot be empty for type action.")
                res = KeyboardController.type_text(text)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "press":
                key = params.get("key", "").strip()
                if not key:
                    return ToolResult(success=False, error="Parameter 'key' cannot be empty for press action.")
                res = KeyboardController.press_key(key)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "hotkey":
                keys = params.get("keys", [])
                if not keys and "key" in params:
                    # Allow 'command+c' format
                    keys = [k.strip() for k in params["key"].split("+") if k.strip()]
                if not keys:
                    return ToolResult(success=False, error="Parameter 'keys' must be provided for hotkey action.")
                res = KeyboardController.hotkey(*keys)
                return ToolResult(success=res["success"], data=res["data"])

            else:
                return ToolResult(success=False, error=f"Unknown keyboard action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"Keyboard operation failed: {e}")
