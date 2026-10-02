"""
J.A.R.V.I.S. macOS Mouse Automation Tool
High-precision Quartz CoreGraphics cursor positioning, clicks, drags, and scrolling.
"""
from typing import Dict, Any
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from desktop_controller.mouse import MouseController

class MacOSMouseTool(BaseTool):
    @property
    def id(self) -> str:
        return "macos_mouse"

    @property
    def name(self) -> str:
        return "macOS Mouse Controller"

    @property
    def description(self) -> str:
        return (
            "Control macOS mouse cursor and clicks via Quartz CoreGraphics. "
            "Supports actions: 'click' (x, y), 'double_click' (x, y), 'right_click' (x, y), "
            "'move' (x, y), 'drag' (x, y), 'scroll' (direction='up'/'down', amount=3), "
            "'position' (get cursor pos), and 'screen_size'."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["click", "double_click", "right_click", "move", "drag", "scroll", "position", "screen_size"],
                    "description": "Mouse operation to perform."
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate in screen points."
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate in screen points."
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "default": "down",
                    "description": "Scroll direction (for action='scroll')."
                },
                "amount": {
                    "type": "integer",
                    "default": 3,
                    "description": "Scroll lines/steps (for action='scroll')."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.MOUSE_CONTROL

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.HIGH

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        x = params.get("x")
        y = params.get("y")

        try:
            if action == "position":
                res = MouseController.get_position()
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "screen_size":
                res = MouseController.get_screen_size()
                return ToolResult(success=res["success"], data=res["data"])

            elif action in ("click", "double_click", "right_click", "move", "drag"):
                if x is None or y is None:
                    # If x, y omitted for click, get current position
                    if action in ("click", "double_click", "right_click"):
                        pos = MouseController.get_position()
                        if pos["success"]:
                            x = pos["data"]["x"]
                            y = pos["data"]["y"]
                        else:
                            return ToolResult(success=False, error="Coordinates (x, y) must be specified.")
                    else:
                        return ToolResult(success=False, error="Coordinates (x, y) must be specified.")

                x_int, y_int = int(x), int(y)
                if action == "click":
                    res = MouseController.click(x_int, y_int)
                elif action == "double_click":
                    res = MouseController.double_click(x_int, y_int)
                elif action == "right_click":
                    res = MouseController.right_click(x_int, y_int)
                elif action == "move":
                    res = MouseController.move(x_int, y_int)
                elif action == "drag":
                    res = MouseController.drag(x_int, y_int)

                return ToolResult(success=res["success"], data=res["data"])

            elif action == "scroll":
                direction = params.get("direction", "down")
                amount = int(params.get("amount", 3))
                res = MouseController.scroll(direction=direction, amount=amount)
                return ToolResult(success=res["success"], data=res["data"])

            else:
                return ToolResult(success=False, error=f"Unknown mouse action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"Mouse operation failed: {e}")
