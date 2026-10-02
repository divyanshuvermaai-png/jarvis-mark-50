"""
Unit and Integration Tests for J.A.R.V.I.S. Phase 3 macOS Computer Control & Perception:
- MacOSWindowTool (Window placement, focus, snapping)
- MacOSKeyboardTool (Text typing, keycodes, hotkeys)
- MacOSMouseTool (Quartz CoreGraphics cursor positioning, clicks, scrolling)
- MacOSVisionTool (Screenshot capture, Apple Vision OCR)
- ComputerAgent (Perceive -> Act -> Verify loop)
- Security Kernel capability and trust-level gating
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from tools.macos.window_tool import MacOSWindowTool
from tools.macos.keyboard_tool import MacOSKeyboardTool
from tools.macos.mouse_tool import MacOSMouseTool
from tools.macos.vision_tool import MacOSVisionTool
from agents.computer import ComputerAgent
from tools.registry import ToolRegistry
from security.trust import TrustLevel
from security.capabilities import Capability, RiskLevel
from intelligence.router.model_router import ModelRouter
from app.config import JarvisConfig


class TestMacOSWindowTool(unittest.TestCase):
    def setUp(self):
        self.tool = MacOSWindowTool()

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "macos_window")
        self.assertEqual(self.tool.required_capability, Capability.WINDOW_CONTROL)
        self.assertEqual(self.tool.risk_tier, RiskLevel.MODERATE)

    @patch("desktop_controller.window.WindowController.focus_app")
    def test_focus_app(self, mock_focus):
        mock_focus.return_value = {"success": True, "data": "Focused: Finder"}
        res = self.tool.execute({"action": "focus", "app": "Finder"})
        self.assertTrue(res.success)
        self.assertEqual(res.data, "Focused: Finder")
        mock_focus.assert_called_once_with("Finder")

    def test_focus_missing_app_fails(self):
        res = self.tool.execute({"action": "focus"})
        self.assertFalse(res.success)
        self.assertIn("required", res.error.lower())

    @patch("desktop_controller.window.WindowController.snap_window")
    def test_snap_window(self, mock_snap):
        mock_snap.return_value = {"success": True, "data": "Window snapped to left"}
        res = self.tool.execute({"action": "snap", "position": "left"})
        self.assertTrue(res.success)
        mock_snap.assert_called_once_with(position="left")

    def test_invalid_action(self):
        res = self.tool.execute({"action": "destroy_all_windows"})
        self.assertFalse(res.success)
        self.assertIn("unknown", res.error.lower())


class TestMacOSKeyboardTool(unittest.TestCase):
    def setUp(self):
        self.tool = MacOSKeyboardTool()

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "macos_keyboard")
        self.assertEqual(self.tool.required_capability, Capability.KEYBOARD_CONTROL)
        self.assertEqual(self.tool.risk_tier, RiskLevel.HIGH)

    @patch("desktop_controller.keyboard.KeyboardController.type_text")
    def test_type_text(self, mock_type):
        mock_type.return_value = {"success": True, "data": "Typed: Hello World..."}
        res = self.tool.execute({"action": "type", "text": "Hello World"})
        self.assertTrue(res.success)
        mock_type.assert_called_once_with("Hello World")

    def test_type_empty_fails(self):
        res = self.tool.execute({"action": "type", "text": ""})
        self.assertFalse(res.success)

    @patch("desktop_controller.keyboard.KeyboardController.hotkey")
    def test_hotkey(self, mock_hotkey):
        mock_hotkey.return_value = {"success": True, "data": "Hotkey: command + c"}
        res = self.tool.execute({"action": "hotkey", "keys": ["command", "c"]})
        self.assertTrue(res.success)
        mock_hotkey.assert_called_once_with("command", "c")


class TestMacOSMouseTool(unittest.TestCase):
    def setUp(self):
        self.tool = MacOSMouseTool()

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "macos_mouse")
        self.assertEqual(self.tool.required_capability, Capability.MOUSE_CONTROL)
        self.assertEqual(self.tool.risk_tier, RiskLevel.HIGH)

    @patch("desktop_controller.mouse.MouseController.move")
    def test_move_mouse(self, mock_move):
        mock_move.return_value = {"success": True, "data": "Moved to (500, 300)"}
        res = self.tool.execute({"action": "move", "x": 500, "y": 300})
        self.assertTrue(res.success)
        mock_move.assert_called_once_with(500, 300)

    @patch("desktop_controller.mouse.MouseController.click")
    def test_click_mouse(self, mock_click):
        mock_click.return_value = {"success": True, "data": "Clicked at (100, 200)"}
        res = self.tool.execute({"action": "click", "x": 100, "y": 200})
        self.assertTrue(res.success)
        mock_click.assert_called_once_with(100, 200)

    @patch("desktop_controller.mouse.MouseController.scroll")
    def test_scroll(self, mock_scroll):
        mock_scroll.return_value = {"success": True, "data": "Scrolled down by 5"}
        res = self.tool.execute({"action": "scroll", "direction": "down", "amount": 5})
        self.assertTrue(res.success)
        mock_scroll.assert_called_once_with(direction="down", amount=5)


class TestMacOSVisionTool(unittest.TestCase):
    def setUp(self):
        self.tool = MacOSVisionTool()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "macos_vision")
        self.assertEqual(self.tool.required_capability, Capability.VISION)
        self.assertEqual(self.tool.risk_tier, RiskLevel.MODERATE)

    @patch("desktop_controller.screen.ScreenController.capture_full")
    def test_screenshot(self, mock_capture):
        fake_path = str(Path(self.test_dir) / "shot.png")
        mock_capture.return_value = {"success": True, "data": fake_path}
        res = self.tool.execute({"action": "screenshot", "save_path": fake_path})
        self.assertTrue(res.success)
        self.assertEqual(res.data, fake_path)

    @patch("desktop_controller.screen.ScreenController.ocr_screen")
    def test_ocr(self, mock_ocr):
        mock_ocr.return_value = {"success": True, "data": "Apple Silicon M5\n32GB Unified Memory"}
        res = self.tool.execute({"action": "ocr"})
        self.assertTrue(res.success)
        self.assertIn("Apple Silicon", res.data)


class TestComputerAgent(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        cfg = JarvisConfig(system_name="JARVIS-TEST", version="5.1.0-test")
        self.router = ModelRouter(config=cfg)
        self.registry = ToolRegistry()
        self.registry.register(MacOSWindowTool())
        self.registry.register(MacOSVisionTool())
        self.agent = ComputerAgent(router=self.router, tools=self.registry)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("desktop_controller.window.WindowController.get_frontmost_app")
    @patch("desktop_controller.screen.ScreenController.get_screen_size")
    @patch("desktop_controller.window.WindowController.list_windows")
    def test_perceive_state(self, mock_list, mock_size, mock_front):
        mock_front.return_value = {"success": True, "data": "Terminal"}
        mock_size.return_value = {"success": True, "data": "1440x900"}
        mock_list.return_value = {"success": True, "data": ["Terminal | bash", "Finder | Documents"]}

        state = self.agent.perceive_state()
        self.assertEqual(state["frontmost_app"], "Terminal")
        self.assertEqual(state["screen_resolution"], "1440x900")
        self.assertEqual(len(state["open_windows"]), 2)

    @patch("desktop_controller.window.WindowController.focus_app")
    @patch("desktop_controller.window.WindowController.get_frontmost_app")
    def test_perform_action_with_verification(self, mock_front, mock_focus):
        mock_focus.return_value = {"success": True, "data": "Focused: Finder"}
        mock_front.return_value = {"success": True, "data": "Finder"}

        res = self.agent.perform_action(
            tool_name="macos_window",
            params={"action": "focus", "app": "Finder"},
            trust_level=TrustLevel.LOCAL_OWNER
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["verified"])
        self.assertIn("Finder", res["verification_detail"])

    def test_untrusted_cannot_execute_macos_tools(self):
        # Security kernel must block REMOTE_PUBLIC from executing WINDOW_CONTROL
        res = self.agent.perform_action(
            tool_name="macos_window",
            params={"action": "list"},
            trust_level=TrustLevel.REMOTE_PUBLIC
        )
        self.assertFalse(res["success"])
        self.assertTrue("authorized" in res["error"].lower() or "denied" in res["error"].lower())



if __name__ == "__main__":
    unittest.main()
