"""
Unit and Integration Tests for Dream Communications & Protocols (Milestone 2 - Track 2):
- GmailTool (IMAP / SMTP)
- TelegramTool (Telegram Bot API)
- CalendarTool (macOS Calendar AppleScript)
- MorningProtocolTool (Stark Morning Briefing Routine)
"""
import unittest
from unittest.mock import patch, MagicMock
import os
from email.mime.text import MIMEText

from integrations.email_engine import GmailTool
from integrations.telegram_engine import TelegramTool
from integrations.calendar_tool import CalendarTool
from core.protocols.morning_protocol import MorningProtocolTool
from app.bootstrap import bootstrap_jarvis


class TestGmailTool(unittest.TestCase):
    def setUp(self):
        self.tool = GmailTool()

    def test_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            res = self.tool.execute({"action": "send", "to": "test@example.com", "body": "Hello"})
            self.assertFalse(res.success)
            self.assertIn("credentials not configured", res.error.lower())

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        env = {"GMAIL_ADDRESS": "jarvis@example.com", "GMAIL_APP_PASSWORD": "password123"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({
                "action": "send",
                "to": "boss@example.com",
                "subject": "System Status",
                "body": "All systems nominal."
            })
            self.assertTrue(res.success)
            self.assertIn("delivered", res.data.lower())
            mock_server.login.assert_called_once_with("jarvis@example.com", "password123")
            mock_server.sendmail.assert_called_once()

    @patch("imaplib.IMAP4_SSL")
    def test_read_emails_success(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value.__enter__.return_value = mock_imap
        mock_imap.search.return_value = ("OK", [b"1 2"])

        msg1 = MIMEText("First message content")
        msg1["From"] = "alice@example.com"
        msg1["Subject"] = "Project Alpha"
        msg1["Date"] = "Mon, 07 Sep 2026 10:00:00"

        msg2 = MIMEText("Second message content")
        msg2["From"] = "bob@example.com"
        msg2["Subject"] = "Weekly Sync"
        msg2["Date"] = "Mon, 07 Sep 2026 11:00:00"

        mock_imap.fetch.side_effect = [
            ("OK", [(b"1", msg2.as_bytes())]),
            ("OK", [(b"2", msg1.as_bytes())])
        ]

        env = {"GMAIL_ADDRESS": "jarvis@example.com", "GMAIL_APP_PASSWORD": "password123"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({"action": "read", "count": 2})
            self.assertTrue(res.success)
            self.assertIn("Project Alpha", res.data)
            self.assertIn("Weekly Sync", res.data)

    @patch("imaplib.IMAP4_SSL")
    def test_status_success(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value.__enter__.return_value = mock_imap
        mock_imap.search.return_value = ("OK", [b"1 2 3"])

        env = {"GMAIL_ADDRESS": "jarvis@example.com", "GMAIL_APP_PASSWORD": "password123"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({"action": "status"})
            self.assertTrue(res.success)
            self.assertIn("3 unread messages", res.data)
            self.assertEqual(res.metadata.get("unread_count"), 3)


class TestTelegramTool(unittest.TestCase):
    def setUp(self):
        self.tool = TelegramTool()

    def test_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            res = self.tool.execute({"action": "send", "message": "Alert!"})
            self.assertFalse(res.success)
            self.assertIn("token not configured", res.error.lower())

    @patch("requests.post")
    def test_send_telegram_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 99}}
        mock_post.return_value = mock_resp

        env = {"TELEGRAM_BOT_TOKEN": "bot12345:ABCDEF", "TELEGRAM_CHAT_ID": "12345678"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({"action": "send", "message": "Perimeter breach detected"})
            self.assertTrue(res.success)
            self.assertIn("sent to chat", res.data.lower())
            self.assertIn("12345678", res.data)

    @patch("requests.get")
    def test_receive_telegram_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ok": True,
            "result": [
                {
                    "message": {
                        "date": 1788700000,
                        "from": {"first_name": "Divyanshu", "username": "divyanshu"},
                        "text": "Status report please"
                    }
                }
            ]
        }
        mock_get.return_value = mock_resp

        env = {"TELEGRAM_BOT_TOKEN": "bot12345:ABCDEF"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({"action": "receive", "limit": 5})
            self.assertTrue(res.success)
            self.assertIn("Status report please", res.data)
            self.assertIn("Divyanshu", res.data)

    @patch("requests.get")
    def test_status_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ok": True,
            "result": {"username": "JarvisAiBot", "first_name": "J.A.R.V.I.S."}
        }
        mock_get.return_value = mock_resp

        env = {"TELEGRAM_BOT_TOKEN": "bot12345:ABCDEF", "TELEGRAM_CHAT_ID": "12345678"}
        with patch.dict(os.environ, env):
            res = self.tool.execute({"action": "status"})
            self.assertTrue(res.success)
            self.assertIn("@JarvisAiBot", res.data)


class TestCalendarTool(unittest.TestCase):
    def setUp(self):
        self.tool = CalendarTool()

    @patch("subprocess.run")
    def test_calendar_create_success(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=0, stdout="", stderr="")
        res = self.tool.execute({
            "action": "create",
            "title": "Quantum Physics Review",
            "start_time": "2026-09-10 14:00",
            "duration_minutes": 45
        })
        self.assertTrue(res.success)
        self.assertIn("Quantum Physics Review", res.data)

    @patch("subprocess.run")
    def test_calendar_today_success(self, mock_sub):
        mock_sub.return_value = MagicMock(
            returncode=0,
            stdout="10:00 AM - 11:00 AM: Team Sync\n02:00 PM - 03:00 PM: Architecture Review",
            stderr=""
        )
        res = self.tool.execute({"action": "today"})
        self.assertTrue(res.success)
        self.assertIn("Team Sync", res.data)
        self.assertIn("Architecture Review", res.data)

    @patch("subprocess.run")
    def test_calendar_empty_schedule(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=0, stdout="", stderr="")
        res = self.tool.execute({"action": "today"})
        self.assertTrue(res.success)
        self.assertIn("no events scheduled", res.data.lower())


class TestMorningProtocolTool(unittest.TestCase):
    @patch("psutil.virtual_memory")
    @patch("psutil.sensors_battery")
    def test_morning_briefing_execution(self, mock_battery, mock_vmem):
        mock_vmem_obj = MagicMock()
        mock_vmem_obj.percent = 32.5
        mock_vmem_obj.available = 22 * (1024 ** 3)
        mock_vmem.return_value = mock_vmem_obj

        mock_batt_obj = MagicMock()
        mock_batt_obj.percent = 95
        mock_batt_obj.power_plugged = True
        mock_battery.return_value = mock_batt_obj

        mock_weather = MagicMock()
        mock_weather.execute.return_value = MagicMock(
            success=True,
            data="Jaipur: 27°C, Sunny. Humidity 40%."
        )

        mock_news = MagicMock()
        mock_news.execute.return_value = MagicMock(
            success=True,
            data="1. Apple announces M5 Ultra chip.\n2. Quantum teleportation record set."
        )

        mock_calendar = MagicMock()
        mock_calendar.execute.return_value = MagicMock(
            success=True,
            data="11:00 AM - Project Kickoff"
        )

        protocol = MorningProtocolTool(
            weather_tool=mock_weather,
            news_tool=mock_news,
            calendar_tool=mock_calendar
        )

        res = protocol.execute({"location": "Jaipur"})
        self.assertTrue(res.success)
        self.assertIn("Good morning, Sir.", res.data)
        self.assertIn("32.5% used", res.data)
        self.assertIn("Battery at 95%", res.data)
        self.assertIn("27°C, Sunny", res.data)
        self.assertIn("Project Kickoff", res.data)
        self.assertIn("Apple announces M5 Ultra", res.data)


class TestBootstrapCommsIntegration(unittest.TestCase):
    def test_bootstrap_wires_comms_tools_and_procedures(self):
        container = bootstrap_jarvis()
        # Verify tools are registered in registry
        for tool_name in ["gmail", "telegram", "calendar", "morning_protocol", "weather", "news", "finance", "system_control", "data_analytics"]:
            tool = container.tools.get_tool(tool_name)
            self.assertIsNotNone(tool, f"Expected {tool_name} to be registered in bootstrap ToolRegistry")

        # Verify procedural memory contains key workflows
        match = container.procedural_memory.find_matching_procedure("good morning briefing")
        self.assertIsNotNone(match)
        self.assertEqual(match["name"], "Morning Briefing Routine")


if __name__ == "__main__":
    unittest.main()
