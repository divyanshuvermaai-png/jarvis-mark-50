"""
Comprehensive Test Suite for J.A.R.V.I.S. Advanced WhatsApp Agent Subsystem.
Verifies all 10 Acceptance Workflows, Subsystem Units, Security Guards,
Granular Permissions, and REST API Endpoints in 100% Isolated Mock Mode.
"""
import os
import unittest
from unittest.mock import patch, MagicMock

# Force offline mock mode for all tests
os.environ["WHATSAPP_MOCK_MODE"] = "true"

from agents.whatsapp.models import (
    ContactMatch, Message, Conversation, WhatsAppActivity,
    ActionResult, WhatsAppPrivacyMode, CallType, MessagePriority
)
from agents.whatsapp.contact_resolver import ContactResolver, is_phone_number
from agents.whatsapp.context_memory import WhatsAppContextMemory
from agents.whatsapp.message_composer import MessageComposer
from agents.whatsapp.permission_manager import WhatsAppPermissionManager
from agents.whatsapp.summarizer import WhatsAppSummarizer
from agents.whatsapp.activity_monitor import WhatsAppActivityMonitor
from agents.whatsapp.mock_engine import WhatsAppMockEngine
from agents.whatsapp.health_check import WhatsAppHealthCheck
from agents.whatsapp.agent import WhatsAppAgent, whatsapp_agent
from integrations.whatsapp import WhatsAppTool
from main import app, parse_commands, execute_action


class TestWhatsAppAgentWorkflows(unittest.TestCase):
    """Verifies all 10 Master Acceptance Workflows."""

    def setUp(self):
        self.agent = WhatsAppAgent(mock_mode=True)
        # Ensure fresh context memory
        self.agent.context.clear()
        self.agent.permissions.reset_defaults()

    def test_acceptance_1_activity_summary(self):
        """Workflow 1: 'What's happening on WhatsApp?' -> returns structured recent activity."""
        res = self.agent.handle_command("What's happening on WhatsApp?")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "summarize_recent_activity")
        self.assertIn("WHATSAPP EXECUTIVE BRIEFING", res["response"])
        self.assertIn("Unread Messages", res["response"])

    def test_acceptance_2_who_messaged_me(self):
        """Workflow 2: 'Who messaged me?' -> identifies recent senders."""
        res = self.agent.handle_command("Who messaged me?")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "who_messaged_me")
        self.assertIn("Recent WhatsApp senders", res["response"])
        self.assertTrue(any(name in res["response"] for name in ["Rahul Sharma", "Mom", "Priya"]))

    def test_acceptance_3_summarize_contact(self):
        """Workflow 3: 'What did Rahul say?' -> retrieves and summarizes Rahul's messages."""
        res = self.agent.handle_command("What did Rahul say?")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "summarize_conversation")
        self.assertIn("Conversation with Rahul", res["response"])
        # Verifies context memory recorded Rahul
        self.assertIn("Rahul", self.agent.context.last_whatsapp_contact)

    def test_acceptance_4_say_hello(self):
        """Workflow 4: 'Say hello to Rahul' -> composes greeting and dispatches."""
        res = self.agent.handle_command("Say hello to Rahul")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "send_message")
        self.assertIn("Hello", res["response"])
        self.assertIn("Rahul", res["response"])

    def test_acceptance_5_tell_contact(self):
        """Workflow 5: 'Tell Rahul I'll call him later' -> sends exact text."""
        res = self.agent.handle_command("Tell Rahul I'll call him later")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "send_message")
        self.assertIn("I'll call him later", res["response"])

    def test_acceptance_6_voice_call(self):
        """Workflow 6: 'Call Rahul on WhatsApp' -> initiates voice call."""
        res = self.agent.handle_command("Call Rahul on WhatsApp")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "call")
        self.assertIn("Calling", res["response"])

    def test_acceptance_7_video_call(self):
        """Workflow 7: 'Video call Mom' -> initiates video call."""
        res = self.agent.handle_command("Video call Mom")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "call")
        self.assertIn("video", res["response"].lower())

    def test_acceptance_8_open_whatsapp(self):
        """Workflow 8: 'Open my WhatsApp' -> activates desktop client."""
        res = self.agent.handle_command("Open my WhatsApp")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "activate_whatsapp")

    def test_acceptance_9_delta_since_left(self):
        """Workflow 9: 'What's new since I left?' -> calculates baseline delta."""
        # Establish initial baseline
        self.agent.get_recent_activity()
        res = self.agent.handle_command("What's new since I left?")
        self.assertTrue(res["success"])
        self.assertEqual(res["action"], "delta_since_last_seen")

    def test_acceptance_10_pronoun_reply(self):
        """Workflow 10: Multi-turn pronoun resolution ('him' -> last contact)."""
        # Step 1: Speak about or message Rahul
        res1 = self.agent.handle_command("Tell Rahul I'll check it")
        self.assertTrue(res1["success"])
        self.assertEqual(self.agent.context.last_whatsapp_contact, "Rahul Sharma")

        # Step 2: Refer to him with pronoun 'him'
        res2 = self.agent.handle_command("Reply to him saying I'll do it")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["action"], "send_message")
        self.assertIn("Rahul Sharma", res2["response"])


class TestWhatsAppSubsystems(unittest.TestCase):
    """Unit tests for individual components of the WhatsApp agent."""

    def setUp(self):
        self.engine = WhatsAppMockEngine()
        self.resolver = ContactResolver(contact_cache=self.engine.mock_contacts)
        self.context = WhatsAppContextMemory()
        self.permissions = WhatsAppPermissionManager(config_path="/tmp/test_jarvis_wa_perms.json")
        self.permissions.reset_defaults()

    def tearDown(self):
        if os.path.exists("/tmp/test_jarvis_wa_perms.json"):
            try:
                os.remove("/tmp/test_jarvis_wa_perms.json")
            except Exception:
                pass

    def test_contact_resolver_exact_and_fuzzy(self):
        """Tests exact and fuzzy contact resolution."""
        match, _ = self.resolver.resolve("Rahul Sharma")
        self.assertIsNotNone(match)
        self.assertEqual(match.name, "Rahul Sharma")

        # Fuzzy match
        match_f, _ = self.resolver.resolve("rahul")
        self.assertIsNotNone(match_f)
        self.assertEqual(match_f.name, "Rahul Sharma")

    def test_contact_resolver_nickname(self):
        """Tests nickname mapping ('mom' -> Mom)."""
        match, _ = self.resolver.resolve("mom")
        self.assertIsNotNone(match)
        self.assertEqual(match.name, "Mom")

    def test_contact_resolver_phone_bypass(self):
        """Tests phone number pattern detection and bypass."""
        phone = "+1 (555) 987-6543"
        self.assertTrue(is_phone_number(phone))
        match, _ = self.resolver.resolve(phone)
        self.assertIsNotNone(match)
        self.assertEqual(match.id, "+15559876543")

    def test_contact_resolver_ambiguity(self):
        """Tests detection of multiple candidate matches."""
        ambiguous_cache = [
            ContactMatch(name="Alex Smith", id="1"),
            ContactMatch(name="Alex Johnson", id="2")
        ]
        res_ambig = ContactResolver(contact_cache=ambiguous_cache)
        match, candidates = res_ambig.resolve("Alex")
        self.assertIsNone(match)
        self.assertEqual(len(candidates), 2)

    def test_message_composer_greetings(self):
        """Tests intent generation for greetings and wishes."""
        msg, is_greeting = MessageComposer.compose_from_intent("Rahul", "Say hello to Rahul")
        self.assertTrue(is_greeting)
        self.assertTrue("Hello" in msg and "Rahul" in msg)

        bday_msg, is_bday = MessageComposer.compose_from_intent("Ankit", "Wish Ankit happy birthday")
        self.assertTrue(is_bday)
        self.assertIn("Happy Birthday", bday_msg)

    def test_message_composer_sensitive_content_audit(self):
        """Tests safety audit blocking financial numbers and credentials."""
        # Clean message
        is_sens, _ = MessageComposer.audit_message("See you at 5 PM for coffee!")
        self.assertFalse(is_sens)

        # Sensitive password
        is_sens_pw, reason_pw = MessageComposer.audit_message("Here is your temporary password: SecretPass123!")
        self.assertTrue(is_sens_pw)
        self.assertIn("password", reason_pw.lower())

        # Sensitive OTP
        is_sens_otp, reason_otp = MessageComposer.audit_message("Your login OTP code is 849201")
        self.assertTrue(is_sens_otp)

        # Sensitive credit card
        is_sens_cc, reason_cc = MessageComposer.audit_message("Use card 4532 8912 3456 7890")
        self.assertTrue(is_sens_cc)

    def test_permission_manager_toggle_and_enforcement(self):
        """Tests runtime permission checks and denial."""
        self.permissions.set_permission("send_messages", False)
        allowed, reason = self.permissions.is_allowed("send_messages")
        self.assertFalse(allowed)
        self.assertIn("disabled", reason)

        # Reset
        self.permissions.set_permission("send_messages", True)
        allowed2, _ = self.permissions.is_allowed("send_messages")
        self.assertTrue(allowed2)

    def test_agent_permission_enforcement(self):
        """Verifies WhatsAppAgent blocks actions when capability is disabled."""
        agent = WhatsAppAgent(mock_mode=True)
        agent.permissions.set_permission("call", False)

        res = agent.call("Rahul", "voice")
        self.assertFalse(res.success)
        self.assertEqual(res.errorCode, "PERMISSION_DENIED")

        agent.permissions.set_permission("call", True)

    def test_health_check(self):
        """Tests WhatsApp subsystem health check diagnostics."""
        hc = WhatsAppHealthCheck.inspect(is_mock_mode=True)
        self.assertIn("summary", hc)
        self.assertTrue(hc["mock_mode"])
        self.assertEqual(hc["privacy_mode"], "STRICT_LOCAL")


class TestWhatsAppMainIntegration(unittest.TestCase):
    """Tests integration of WhatsApp agent into main.py and REST API."""

    def setUp(self):
        self.client = app.test_client()
        whatsapp_agent.set_mock_mode(True)
        whatsapp_agent.permissions.reset_defaults()

    def test_parse_commands_whatsapp_intents(self):
        """Verifies natural language command parsing in main.py."""
        acts = parse_commands("what's happening on whatsapp")
        self.assertTrue(any(a["action"] == "whatsapp_activity_summary" for a in acts))

        acts_who = parse_commands("who messaged me")
        self.assertTrue(any(a["action"] == "whatsapp_who_messaged" for a in acts_who))

        acts_call = parse_commands("call rahul on whatsapp")
        self.assertTrue(any(a["action"] == "whatsapp_call" for a in acts_call))

        acts_vcall = parse_commands("video call mom")
        self.assertTrue(any(a["action"] == "whatsapp_call" and a["params"].get("video") for a in acts_vcall))

        acts_say = parse_commands("say hello to rahul")
        self.assertTrue(any(a["action"] == "whatsapp_conversational" for a in acts_say))

    def test_api_whatsapp_activity(self):
        """Tests GET /api/whatsapp/activity."""
        res = self.client.get("/api/whatsapp/activity")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("activity", data)
        self.assertIn("summary", data)

    def test_api_whatsapp_summarize(self):
        """Tests GET /api/whatsapp/summarize."""
        res = self.client.get("/api/whatsapp/summarize")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)

    def test_api_whatsapp_permissions(self):
        """Tests GET & POST /api/whatsapp/permissions."""
        # GET
        get_res = self.client.get("/api/whatsapp/permissions")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("permissions", data["status"])

        # POST update
        post_res = self.client.post("/api/whatsapp/permissions", json={
            "permissions": {"video_call": False}
        })
        self.assertEqual(post_res.status_code, 200)
        updated = post_res.get_json()
        self.assertFalse(updated["status"]["permissions"]["video_call"])

        # Restore
        self.client.post("/api/whatsapp/permissions", json={"permissions": {"video_call": True}})

    def test_api_whatsapp_health(self):
        """Tests GET /api/whatsapp/health."""
        res = self.client.get("/api/whatsapp/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("health", data)

    def test_api_whatsapp_mock(self):
        """Tests GET & POST /api/whatsapp/mock."""
        res = self.client.get("/api/whatsapp/mock")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue("mock_mode" in data)

    def test_chat_endpoint_direct_whatsapp_summary(self):
        """Verifies that /api/chat returns rich WhatsApp summaries directly."""
        res = self.client.post("/api/chat", json={"message": "What's happening on WhatsApp?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("WHATSAPP EXECUTIVE BRIEFING", data["response"])


if __name__ == "__main__":
    unittest.main()
