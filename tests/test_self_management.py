"""
Unit and Integration Tests for J.A.R.V.I.S. Phase 6 Controlled Self-Management & Self-Healing:
- SystemHealthCheck (Subsystem auditing & hardware health metrics)
- SandboxedToolVerifier (AST security analysis & subprocess validation sandbox)
- RecoveryManager (Transactional rollback hooks & provider degradation tracking)
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import time

from core.diagnostics.health_check import SystemHealthCheck, SubsystemStatus
from core.diagnostics.tool_verifier import SandboxedToolVerifier
from core.diagnostics.recovery import RecoveryManager
from app.config import JarvisConfig
from intelligence.router.model_router import ModelRouter
from security.kill_switch import KillSwitchManager



class TestSystemHealthCheck(unittest.TestCase):
    def test_inspect_healthy_system(self):
        container = MagicMock()
        container.kill_switch.is_active.return_value = False
        container.router.providers = {"local_gemma": MagicMock()}
        container.tools.list_tools.return_value = [MagicMock()] * 6
        container.semantic_memory.count.return_value = 10
        container.episodic_memory.count.return_value = 5
        container.procedural_memory.list_procedures.return_value = [MagicMock()] * 3

        report = SystemHealthCheck.inspect(container)
        self.assertIsNotNone(report)
        self.assertIn("memory", report.subsystems)
        self.assertIn("disk", report.subsystems)
        self.assertIn("security", report.subsystems)
        self.assertIn("intelligence", report.subsystems)
        self.assertEqual(report.subsystems["security"]["kill_switch"], "NORMAL")
        self.assertTrue(report.free_ram_gb > 0)
        self.assertTrue(report.disk_free_gb > 0)

    def test_inspect_kill_switch_active_triggers_critical(self):
        container = MagicMock()
        container.kill_switch.is_active.return_value = True
        report = SystemHealthCheck.inspect(container)
        self.assertEqual(report.subsystems["security"]["status"], SubsystemStatus.CRITICAL)
        self.assertEqual(report.overall_status, SubsystemStatus.CRITICAL)
        self.assertTrue(any("kill switch" in a.lower() for a in report.alerts))


class TestSandboxedToolVerifier(unittest.TestCase):
    def test_reject_forbidden_eval_exec(self):
        bad_code = """
from tools.base import BaseTool, ToolResult

class MaliciousTool(BaseTool):
    id = "malicious"
    name = "Malicious"
    description = "bad"
    parameters_schema = {}
    def execute(self, params):
        exec("import os; os.system('echo hacked')")
        return ToolResult(success=True)
"""
        res = SandboxedToolVerifier.verify(bad_code)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("forbidden security primitive" in iss.lower() for iss in res.issues))

    def test_reject_forbidden_import_ctypes(self):
        bad_code = """
import ctypes
from tools.base import BaseTool, ToolResult

class BadTool(BaseTool):
    id = "bad"
    name = "Bad"
    description = "bad"
    parameters_schema = {}
    def execute(self, params):
        return ToolResult(success=True)
"""
        res = SandboxedToolVerifier.verify(bad_code)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("forbidden module import" in iss.lower() for iss in res.issues))

    def test_reject_missing_base_tool(self):
        raw_class = """
class StandaloneClass:
    def hello(self):
        return "hi"
"""
        res = SandboxedToolVerifier.verify(raw_class)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("basetool" in iss.lower() for iss in res.issues))

    def test_accept_valid_custom_tool(self):
        good_code = """
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel

class MathSquareTool(BaseTool):
    @property
    def id(self): return "math_square"
    @property
    def name(self): return "Square Number"
    @property
    def description(self): return "Calculates the square of a number"
    @property
    def parameters_schema(self):
        return {"type": "object", "properties": {"val": {"type": "number"}}, "required": ["val"]}
    @property
    def required_capability(self): return Capability.SYSTEM_INFO_READ
    @property
    def risk_tier(self): return RiskLevel.LOW
    def execute(self, params):
        v = params.get("val", 0)
        return ToolResult(success=True, data=v * v)
"""
        res = SandboxedToolVerifier.verify(good_code, sample_params={"val": 5})
        self.assertTrue(res.is_valid, msg=f"Issues: {res.issues} Stderr: {res.stderr}")
        self.assertEqual(res.tool_id, "math_square")


class TestRecoveryManager(unittest.TestCase):
    def setUp(self):
        self.episodic = MagicMock()
        self.recovery = RecoveryManager(episodic_memory=self.episodic)

    def test_rollback_lifo_execution(self):
        events = []
        self.recovery.register_rollback("step1", "Create File", lambda: events.append("Deleted File"))
        self.recovery.register_rollback("step2", "Open Socket", lambda: events.append("Closed Socket"))

        results = self.recovery.execute_rollbacks()

        # Must execute in LIFO order
        self.assertEqual(events, ["Closed Socket", "Deleted File"])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "ROLLED_BACK")
        self.episodic.record_episode.assert_called_once()

    def test_clear_rollbacks(self):
        events = []
        self.recovery.register_rollback("step1", "Action", lambda: events.append(1))
        self.recovery.clear_rollbacks()
        self.assertEqual(len(self.recovery._rollback_stack), 0)

        # Nothing executed
        self.recovery.execute_rollbacks()
        self.assertEqual(len(events), 0)

    def test_provider_degradation_cooldown(self):
        self.assertFalse(self.recovery.is_provider_degraded("groq"))
        self.recovery.mark_provider_degraded("groq", cooldown_seconds=0.1)
        self.assertTrue(self.recovery.is_provider_degraded("groq"))

        time.sleep(0.12)
        self.assertFalse(self.recovery.is_provider_degraded("groq"))


if __name__ == "__main__":
    unittest.main()
