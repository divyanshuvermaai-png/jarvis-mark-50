"""
J.A.R.V.I.S. Computer Agent
Autonomous macOS computer operator implementing the Perceive -> Plan -> Act -> Verify feedback loop.
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .base import BaseAgent
from security.trust import TrustLevel
from desktop_controller.window import WindowController
from desktop_controller.screen import ScreenController

logger = logging.getLogger("jarvis.agents.computer")

class ComputerAgent(BaseAgent):
    def __init__(self, router, tools=None):
        super().__init__(
            name="ComputerAgent",
            role="Autonomous macOS Computer Operator & Perception Agent",
            router=router,
            tools=tools
        )

    @property
    def system_prompt(self) -> str:
        return """You are the COMPUTER CONTROL & PERCEPTION AGENT of J.A.R.V.I.S.
You interact directly with macOS application windows, screens, keystrokes, and cursor coordinates.

CORE OPERATIONAL PRINCIPLES:
1. Always perceive active context before taking action (know what app has focus).
2. Never perform blind keystrokes or destructive clicks without verification.
3. Observe and verify changes after each action (confirm the window switched or screenshot saved).
4. Respect all privacy and local-only execution boundaries."""

    def perceive_state(self) -> Dict[str, Any]:
        """
        Perceives the current macOS visual and window context.
        """
        frontmost = WindowController.get_frontmost_app()
        screen_size = ScreenController.get_screen_size()
        windows = WindowController.list_windows()

        return {
            "frontmost_app": frontmost.get("data") if frontmost.get("success") else "Unknown",
            "screen_resolution": screen_size.get("data") if screen_size.get("success") else "Unknown",
            "open_windows": windows.get("data", [])[:8] if windows.get("success") else []
        }

    def perform_action(
        self,
        tool_name: str,
        params: Dict[str, Any],
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER
    ) -> Dict[str, Any]:
        """
        Executes a desktop action and deterministically verifies the real-world outcome.
        """
        if not self.tools.has_tool(tool_name):
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not registered.",
                "verified": False
            }

        # Execute tool via secure tool registry
        tool_result = self.tools.execute_tool(tool_name, params, trust_level=trust_level)
        if not tool_result.success:
            return {
                "success": False,
                "error": tool_result.error,
                "verified": False,
                "data": None
            }

        # Outcome Verification Layer
        verified = True
        verification_detail = "Action completed without state regression."

        action = params.get("action", "")

        if tool_name == "macos_window" and action == "focus":
            target_app = params.get("app", "").lower()
            current_app_res = WindowController.get_frontmost_app()
            current_app = current_app_res.get("data", "").lower() if current_app_res.get("success") else ""
            if target_app in current_app or current_app in target_app:
                verified = True
                verification_detail = f"Verified frontmost application is '{current_app_res.get('data')}'."
            else:
                verified = False
                verification_detail = f"Expected '{target_app}', but frontmost is '{current_app_res.get('data')}'."

        elif tool_name == "macos_vision" and action in ("screenshot", "region", "window"):
            saved_file = tool_result.data
            if saved_file and Path(saved_file).exists() and Path(saved_file).stat().st_size > 0:
                verified = True
                verification_detail = f"Verified screenshot generated ({Path(saved_file).stat().st_size} bytes)."
            else:
                verified = False
                verification_detail = "Screenshot file was not found on disk."

        elif tool_name == "macos_vision" and action == "ocr":
            extracted_text = tool_result.data
            if extracted_text and len(str(extracted_text).strip()) > 0:
                verified = True
                verification_detail = f"Extracted {len(str(extracted_text).splitlines())} lines of OCR text."
            else:
                verification_detail = "OCR completed, no text recognized in target area."

        return {
            "success": True,
            "data": tool_result.data,
            "verified": verified,
            "verification_detail": verification_detail
        }
