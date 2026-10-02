"""
J.A.R.V.I.S. macOS Window Management Tool
Manages window placement, application focus, snapping, and open window listing.
"""
from typing import Dict, Any
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from desktop_controller.window import WindowController

class MacOSWindowTool(BaseTool):
    @property
    def id(self) -> str:
        return "macos_window"

    @property
    def name(self) -> str:
        return "macOS Window Controller"

    @property
    def description(self) -> str:
        return (
            "Control macOS application windows. "
            "Supports actions: 'focus' (bring app to front), 'snap' (snap to 'left', 'right', 'maximize'), "
            "'minimize', 'close', 'list' (list open windows), and 'frontmost' (get active app)."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["focus", "snap", "minimize", "close", "list", "frontmost"],
                    "description": "The window operation to perform."
                },
                "app": {
                    "type": "string",
                    "description": "The name of the application (required for 'focus', optional for others)."
                },
                "position": {
                    "type": "string",
                    "enum": ["left", "right", "maximize"],
                    "default": "maximize",
                    "description": "Snap position if action is 'snap'."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.WINDOW_CONTROL

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        app = params.get("app", "").strip()
        position = params.get("position", "maximize").lower().strip()

        try:
            if action == "focus":
                if not app:
                    return ToolResult(success=False, error="Parameter 'app' is required for focus action.")
                res = WindowController.focus_app(app)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "snap":
                res = WindowController.snap_window(position=position)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "minimize":
                res = WindowController.minimize_window()
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "close":
                res = WindowController.close_window()
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "list":
                res = WindowController.list_windows()
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "frontmost":
                res = WindowController.get_frontmost_app()
                return ToolResult(success=res["success"], data=res["data"])

            else:
                return ToolResult(success=False, error=f"Unknown window action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"Window operation failed: {e}")
