"""
Unit and Integration Tests for J.A.R.V.I.S. Phase 4 Integrations & Background Scheduler:
- TaskScheduler (Persistent SQLite delayed & recurring task runner)
- AppleSuiteTool (iMessage, Notes, Reminders, Mail via safe AppleScript)
- WhatsAppTool (WhatsApp macOS client automation)
- Security policy capability gating
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import time

from core.scheduler.scheduler import TaskScheduler
from integrations.apple_suite import AppleSuiteTool
from integrations.whatsapp import WhatsAppTool
from tools.registry import ToolRegistry
from security.trust import TrustLevel
from security.capabilities import Capability, RiskLevel


class TestTaskScheduler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_scheduler.db"
        self.dispatched_actions = []
        self.scheduler = TaskScheduler(
            db_path=self.db_path,
            dispatcher=lambda act, params: self.dispatched_actions.append((act, params)),
            tick_rate=0.1
        )

    def tearDown(self):
        self.scheduler.stop()
        shutil.rmtree(self.test_dir)

    def test_schedule_in_and_tick(self):
        # Schedule task to run after 0.1s
        jid = self.scheduler.schedule_in(
            delay_seconds=0.1,
            action="system_diagnostics",
            params={"mode": "full"},
            name="Run System Diagnostics"
        )
        self.assertIsNotNone(jid)
        job = self.scheduler.get_job(jid)
        self.assertEqual(job.status, "scheduled")
        self.assertEqual(job.job_type, "one_time")

        # Before delay expires: tick does nothing
        self.scheduler.tick()
        self.assertEqual(len(self.dispatched_actions), 0)

        # Wait past delay and tick
        time.sleep(0.15)
        self.scheduler.tick()

        self.assertEqual(len(self.dispatched_actions), 1)
        self.assertEqual(self.dispatched_actions[0][0], "system_diagnostics")
        self.assertEqual(self.dispatched_actions[0][1]["mode"], "full")

        updated_job = self.scheduler.get_job(jid)
        self.assertEqual(updated_job.status, "completed")

    def test_schedule_every_recurring(self):
        jid = self.scheduler.schedule_every(
            interval_seconds=0.1,
            action="heartbeat",
            params={"ping": 1}
        )
        time.sleep(0.12)
        self.scheduler.tick()
        self.assertEqual(len(self.dispatched_actions), 1)

        time.sleep(0.12)
        self.scheduler.tick()
        self.assertEqual(len(self.dispatched_actions), 2)

        job = self.scheduler.get_job(jid)
        self.assertEqual(job.status, "scheduled")

    def test_cancel_job(self):
        jid = self.scheduler.schedule_in(delay_seconds=10.0, action="delayed_alert")
        self.assertEqual(self.scheduler.get_job(jid).status, "scheduled")

        cancelled = self.scheduler.cancel_job(jid)
        self.assertTrue(cancelled)
        self.assertEqual(self.scheduler.get_job(jid).status, "cancelled")

    def test_list_jobs(self):
        self.scheduler.schedule_in(delay_seconds=5.0, action="job1")
        self.scheduler.schedule_in(delay_seconds=10.0, action="job2")

        jobs = self.scheduler.list_jobs()
        self.assertEqual(len(jobs), 2)


class TestAppleSuiteTool(unittest.TestCase):
    def setUp(self):
        self.tool = AppleSuiteTool()

    def test_metadata(self):
        self.assertEqual(self.tool.id, "apple_suite")
        self.assertEqual(self.tool.required_capability, Capability.APP_CONTROL)
        self.assertEqual(self.tool.risk_tier, RiskLevel.MODERATE)

    @patch("subprocess.run")
    def test_imessage_dispatch(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.tool.execute({
            "action": "imessage",
            "contact": "Bruce Wayne",
            "content": "Meeting confirmed."
        })
        self.assertTrue(res.success)
        self.assertIn("Bruce Wayne", res.data)

    @patch("subprocess.run")
    def test_create_note(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.tool.execute({
            "action": "note",
            "content": "Project Antigravity architecture notes"
        })
        self.assertTrue(res.success)
        self.assertIn("Note created", res.data)

    @patch("subprocess.run")
    def test_create_reminder(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.tool.execute({
            "action": "reminder",
            "task": "Review flight telemetry"
        })
        self.assertTrue(res.success)
        self.assertIn("Reminder created", res.data)

    @patch("subprocess.run")
    def test_check_mail(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="3\n")
        res = self.tool.execute({"action": "mail"})
        self.assertTrue(res.success)
        self.assertIn("3 unread", res.data)


class TestWhatsAppTool(unittest.TestCase):
    def setUp(self):
        self.tool = WhatsAppTool()

    def test_metadata(self):
        self.assertEqual(self.tool.id, "whatsapp_automation")
        self.assertEqual(self.tool.required_capability, Capability.WHATSAPP_AUTOMATION)
        self.assertEqual(self.tool.risk_tier, RiskLevel.HIGH)

    @patch("whatsapp_controller.tools.WhatsAppTools.send_message")
    def test_send_message(self, mock_send):
        mock_send.return_value = {"success": True, "status": "completed", "contact": "Pepper Potts"}
        res = self.tool.execute({
            "action": "send_message",
            "contact": "Pepper Potts",
            "message": "Arriving in 10 minutes"
        })
        self.assertTrue(res.success)
        self.assertEqual(res.data["status"], "completed")

    @patch("whatsapp_controller.tools.WhatsAppTools.read_chat")
    def test_read_chat(self, mock_read):
        mock_read.return_value = {"success": True, "messages": ["Hello", "Can you send the report?"]}
        res = self.tool.execute({
            "action": "read_chat",
            "contact": "Tony Stark"
        })
        self.assertTrue(res.success)
        self.assertEqual(len(res.data["messages"]), 2)

    def test_missing_contact_fails(self):
        res = self.tool.execute({
            "action": "send_message",
            "message": "Hello"
        })
        self.assertFalse(res.success)
        self.assertIn("contact", res.error.lower())


class TestIntegrationSecurityBoundaries(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(AppleSuiteTool())
        self.registry.register(WhatsAppTool())

    def test_remote_public_blocked_from_apple_suite(self):
        res = self.registry.execute_tool(
            "apple_suite",
            {"action": "imessage", "contact": "Eve", "content": "hello"},
            trust_level=TrustLevel.REMOTE_PUBLIC
        )
        self.assertFalse(res.success)
        self.assertTrue("authorized" in res.error.lower() or "denied" in res.error.lower())

    def test_remote_public_blocked_from_whatsapp(self):
        res = self.registry.execute_tool(
            "whatsapp_automation",
            {"action": "send_message", "contact": "Eve", "message": "hello"},
            trust_level=TrustLevel.REMOTE_PUBLIC
        )
        self.assertFalse(res.success)
        self.assertTrue("authorized" in res.error.lower() or "denied" in res.error.lower())


if __name__ == "__main__":
    unittest.main()
