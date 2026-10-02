"""
J.A.R.V.I.S. macOS Native Perception & Vision Tool
Leverages macOS screencapture and Apple Silicon Vision Framework for native on-device OCR.
"""
import os
import tempfile
from typing import Dict, Any
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from desktop_controller.screen import ScreenController

class MacOSVisionTool(BaseTool):
    @property
    def id(self) -> str:
        return "macos_vision"

    @property
    def name(self) -> str:
        return "macOS Vision & Perception"

    @property
    def description(self) -> str:
        return (
            "Capture screenshots and perform Apple Silicon native OCR perception. "
            "Supports actions: 'screenshot' (full screen), 'ocr' (extract text from screen or image via Apple Vision), "
            "'region' (capture region x, y, w, h), 'window' (capture front window), and 'screen_size'."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["screenshot", "ocr", "region", "window", "screen_size"],
                    "description": "Perception operation to perform."
                },
                "image_path": {
                    "type": "string",
                    "description": "Path to an existing image for OCR (optional, defaults to live screenshot)."
                },
                "save_path": {
                    "type": "string",
                    "description": "Optional destination path to save screenshot."
                },
                "x": {"type": "integer", "description": "Region X origin"},
                "y": {"type": "integer", "description": "Region Y origin"},
                "w": {"type": "integer", "description": "Region width"},
                "h": {"type": "integer", "description": "Region height"}
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.VISION

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()
        save_path = params.get("save_path")

        try:
            if action == "screenshot":
                res = ScreenController.capture_full(save_path=save_path)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "ocr":
                image_path = params.get("image_path")
                res = ScreenController.ocr_screen(image_path=image_path)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "window":
                res = ScreenController.capture_window(save_path=save_path)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "region":
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                w = int(params.get("w", 100))
                h = int(params.get("h", 100))
                res = ScreenController.capture_region(x, y, w, h, save_path=save_path)
                return ToolResult(success=res["success"], data=res["data"])

            elif action == "screen_size":
                res = ScreenController.get_screen_size()
                return ToolResult(success=res["success"], data=res["data"])

            else:
                return ToolResult(success=False, error=f"Unknown vision action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"Vision operation failed: {e}")
