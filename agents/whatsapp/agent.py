"""
J.A.R.V.I.S. Advanced WhatsApp Agent
Autonomous conversational agent providing deep natural-language, voice-first,
and security-hardened control over WhatsApp Desktop on macOS.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from agents.base import BaseAgent
from intelligence.router import ModelRouter, model_router
from .models import (
    ContactMatch, Message, Conversation, WhatsAppActivity,
    ActionResult, WhatsAppPrivacyMode, CallType, MessagePriority
)
from .contact_resolver import ContactResolver, is_phone_number
from .context_memory import whatsapp_context_memory, WhatsAppContextMemory
from .message_composer import MessageComposer
from .permission_manager import whatsapp_permission_manager, WhatsAppPermissionManager
from .summarizer import WhatsAppSummarizer
from .activity_monitor import whatsapp_activity_monitor, WhatsAppActivityMonitor
from .mock_engine import WhatsAppMockEngine
from .desktop_controller import WhatsAppDesktopController
from .health_check import WhatsAppHealthCheck

logger = logging.getLogger("jarvis.agents.whatsapp")


class WhatsAppAgent(BaseAgent):
    """
    Production WhatsApp Agent for J.A.R.V.I.S.
    Operates through the user's logged-in WhatsApp Desktop macOS client or mock engine.
    """

    def __init__(
        self,
        router: Optional[ModelRouter] = None,
        mock_mode: Optional[bool] = None,
        tools = None
    ):
        router = router or model_router
        super().__init__(
            name="WhatsAppAgent",
            role="Autonomous WhatsApp Communication & Perception Agent",
            router=router,
            tools=tools
        )

        # Mock mode toggle: via param or env var WHATSAPP_MOCK_MODE
        env_mock = os.getenv("WHATSAPP_MOCK_MODE", "false").lower() in ("true", "1", "yes")
        self.mock_mode = env_mock if mock_mode is None else mock_mode

        # Internal Subsystems
        self.mock_engine = WhatsAppMockEngine()
        self.desktop_controller = WhatsAppDesktopController()
        self.resolver = ContactResolver(contact_cache=self.mock_engine.mock_contacts if self.mock_mode else None)
        self.context = whatsapp_context_memory
        self.permissions = whatsapp_permission_manager
        self.monitor = whatsapp_activity_monitor
        self.summarizer = WhatsAppSummarizer()

    def set_mock_mode(self, enabled: bool):
        """Toggles between real macOS desktop control and offline simulation."""
        self.mock_mode = enabled
        self.resolver.contact_cache = self.mock_engine.mock_contacts if enabled else None

    @property
    def system_prompt(self) -> str:
        return """You are the WHATSAPP COMMUNICATION AGENT of J.A.R.V.I.S.
You manage natural-language voice and text interaction with WhatsApp on macOS.
CORE PRINCIPLES:
1. Local-First Privacy: Do not transmit private conversation bodies to cloud providers.
2. Zero-Mistake Contact Resolution: Never dispatch or call an ambiguous contact without confirmation.
3. Multi-turn Continuity: Remember conversational pronouns ('him', 'her', 'them') across turns.
4. Intelligent Confirmation: Routine greetings send immediately; sensitive/financial content requires explicit confirmation."""

    # ── Core Interface Methods (Section 4) ──

    def find_contact(self, name: str) -> List[ContactMatch]:
        """Finds candidate contact matches using exact, fuzzy, and phonetic matching."""
        resolved_name = self.context.resolve_target(name)
        if self.mock_mode:
            return self.mock_engine.find_contacts(resolved_name)
        return self.resolver.find_matches(resolved_name)

    def open_conversation(self, contact_id: str) -> ActionResult:
        """Opens/focuses conversation with target contact."""
        target = self.context.resolve_target(contact_id)
        match, candidates = self.resolver.resolve(target)
        if candidates and not match:
            names = [c.name for c in candidates]
            return ActionResult(
                success=False,
                action="open_conversation",
                error="MULTIPLE_CONTACT_MATCHES",
                requires_confirmation=True,
                confirmation_reason=f"I found multiple contacts matching '{target}': {', '.join(names)}. Which one do you mean?",
                data={"candidates": names}
            )
        resolved_name = match.name if match else target

        if self.mock_mode:
            res = self.mock_engine.open_conversation(resolved_name)
        else:
            res = self.desktop_controller.open_conversation(resolved_name)

        if res.success:
            self.context.update_contact(resolved_name)
            self.context.update_action("open_conversation", contact=resolved_name)
        return res

    def read_conversation(self, contact_id: str, options: Optional[Dict[str, Any]] = None) -> List[Message]:
        """Reads recent messages from contact conversation."""
        opts = options or {}
        max_msgs = int(opts.get("max_messages", 10))
        target = self.context.resolve_target(contact_id)

        # Check permission
        allowed, reason = self.permissions.is_allowed("read_messages")
        if not allowed:
            logger.warning(reason)
            return []

        match, _ = self.resolver.resolve(target)
        resolved_name = match.name if match else target
        phone = match.phone if match else None

        if self.mock_mode:
            msgs = self.mock_engine.read_conversation(resolved_name, max_messages=max_msgs)
        else:
            msgs = self.desktop_controller.read_visible_conversation(resolved_name, max_messages=max_msgs, phone=phone)

        self.context.update_contact(resolved_name)
        self.context.update_action("read_conversation", contact=resolved_name)
        return msgs

    def send_message(self, contact_id: str, message: str) -> ActionResult:
        """Composes, audits, and dispatches a text message."""
        target = self.context.resolve_target(contact_id)

        # 1. Check capability permission
        allowed, reason = self.permissions.is_allowed("send_messages")
        if not allowed:
            return ActionResult(success=False, action="send_message", error=reason, errorCode="PERMISSION_DENIED")

        # 2. Resolve Contact & Check Ambiguity
        match, candidates = self.resolver.resolve(target)
        if candidates and not match:
            names = [c.name for c in candidates]
            return ActionResult(
                success=False,
                action="send_message",
                error="MULTIPLE_CONTACT_MATCHES",
                requires_confirmation=True,
                confirmation_reason=f"I found multiple contacts matching '{target}': {', '.join(names)}. Which one do you mean?",
                data={"candidates": names}
            )

        resolved_name = match.name if match else target
        phone = match.phone if match else None

        # 3. Resolve pronoun / message references (e.g. 'the same message')
        msg_text = self.context.resolve_message(message)
        if not msg_text.strip():
            return ActionResult(success=False, action="send_message", error="Message cannot be empty", errorCode="EMPTY_MESSAGE")

        # 4. Audit Message for Sensitive Content
        is_sensitive, sens_reason = MessageComposer.audit_message(msg_text)
        if is_sensitive:
            return ActionResult(
                success=False,
                action="send_message",
                requires_confirmation=True,
                confirmation_reason=f"Safety Check: {sens_reason}. Do you confirm sending this message to {resolved_name}?",
                data={"contact": resolved_name, "message": msg_text}
            )

        # 5. Dispatch Message
        if self.mock_mode:
            res = self.mock_engine.send_message(resolved_name, msg_text)
        else:
            res = self.desktop_controller.send_message(resolved_name, msg_text, phone=phone)

        if res.success:
            self.context.update_action("send_message", contact=resolved_name, message=msg_text)
        return res

    def call(self, contact_id: str, call_type: str = "voice") -> ActionResult:
        """Initiates voice or video call with resolved contact."""
        target = self.context.resolve_target(contact_id)
        is_video = (call_type.lower() == "video")
        cap = "video_call" if is_video else "call"

        # 1. Check permission
        allowed, reason = self.permissions.is_allowed(cap)
        if not allowed:
            return ActionResult(success=False, action="call", error=reason, errorCode="PERMISSION_DENIED")

        # 2. Resolve Contact
        match, candidates = self.resolver.resolve(target)
        if candidates and not match:
            names = [c.name for c in candidates]
            return ActionResult(
                success=False,
                action="call",
                error="MULTIPLE_CONTACT_MATCHES",
                requires_confirmation=True,
                confirmation_reason=f"I found multiple contacts matching '{target}': {', '.join(names)}. Which one do you mean?",
                data={"candidates": names}
            )

        resolved_name = match.name if match else target
        phone = match.phone if match else None
        c_type = CallType.VIDEO if is_video else CallType.VOICE

        if self.mock_mode:
            res = self.mock_engine.call(resolved_name, c_type)
        else:
            res = self.desktop_controller.initiate_call(resolved_name, c_type, phone=phone)

        if res.success:
            self.context.update_action("call", contact=resolved_name)
        return res

    def get_unread_conversations(self) -> List[Conversation]:
        """Returns list of conversations with unread messages."""
        activity = self.get_recent_activity()
        return [c for c in activity.conversations if c.unread_count > 0]

    def get_recent_activity(self, options: Optional[Dict[str, Any]] = None) -> WhatsAppActivity:
        """Inspects and returns structured recent activity."""
        if self.mock_mode:
            activity = self.mock_engine.get_recent_activity()
        else:
            # Under desktop control, query open state / mock baseline
            activity = self.mock_engine.get_recent_activity()

        # Update monitor baseline
        self.monitor.record_activity(activity)
        return activity

    def summarize_conversation(self, contact_id: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Summarizes recent messages with a specific contact."""
        allowed, reason = self.permissions.is_allowed("summarize")
        if not allowed:
            return reason

        target = self.context.resolve_target(contact_id)
        msgs = self.read_conversation(target)
        if not msgs:
            return f"Sir, no recent messages found with {target}."

        return self.summarizer.summarize_conversation(target, msgs, privacy_mode=self.permissions.privacy_mode)

    def summarize_recent_activity(self, options: Optional[Dict[str, Any]] = None) -> str:
        """Summarizes all recent WhatsApp activity."""
        allowed, reason = self.permissions.is_allowed("summarize")
        if not allowed:
            return reason

        activity = self.get_recent_activity(options)
        return self.summarizer.summarize_activity(activity, privacy_mode=self.permissions.privacy_mode)

    def health_check(self) -> Dict[str, Any]:
        """Returns health status of WhatsApp agent and underlying desktop controller."""
        return WhatsAppHealthCheck.inspect(is_mock_mode=self.mock_mode)

    # ── High-Level Natural Language & Voice Command Router ──

    def handle_command(self, natural_text: str) -> Dict[str, Any]:
        """
        Parses and executes natural-language or voice commands.
        Handles all commands from Section 2 & Section 40.
        """
        text = natural_text.strip()
        text_lower = text.lower()

        # 1. "What's happening on WhatsApp?" / "What are my WhatsApp updates?" / "Summarize my WhatsApp"
        if any(p in text_lower for p in [
            "what's happening on whatsapp", "what is happening on whatsapp",
            "what are my whatsapp updates", "whatsapp updates", "show me my whatsapp updates",
            "summarize my whatsapp", "summarize whatsapp", "what are the whatsapp updates"
        ]):
            summary = self.summarize_recent_activity()
            return {"success": True, "action": "summarize_recent_activity", "response": summary}

        # 2. "Who messaged me?" / "Who sent me messages today?" / "Did anyone message me"
        if any(p in text_lower for p in [
            "who messaged me", "who sent me messages", "who contacted me",
            "did anyone message me"
        ]):
            act = self.get_recent_activity()
            resp = self.summarizer.get_senders_summary(act)
            return {"success": True, "action": "who_messaged_me", "response": resp}

        # 3. "Who needs a reply?"
        if "who needs a reply" in text_lower or "needs a response" in text_lower:
            act = self.get_recent_activity()
            resp = self.summarizer.get_needs_reply_summary(act)
            return {"success": True, "action": "who_needs_reply", "response": resp}

        # 4. "Show me my unread WhatsApp messages" / "unread messages"
        if "unread" in text_lower and ("whatsapp" in text_lower or "message" in text_lower):
            unreads = self.get_unread_conversations()
            if not unreads:
                return {"success": True, "action": "unread", "response": "You have 0 unread WhatsApp messages, Sir."}
            lines = [f"You have unread messages across {len(unreads)} conversation(s):"]
            for u in unreads:
                lines.append(f"• {u.contact_name}: {u.unread_count} unread — \"{u.last_message_text}\"")
            return {"success": True, "action": "unread", "response": "\n".join(lines)}

        # 5. "What's new since I left?" / "What changed while I was away?"
        if any(p in text_lower for p in ["since i left", "while i was away", "what's new"]):
            act = self.get_recent_activity()
            resp = self.monitor.get_delta_since_last_seen(act)
            return {"success": True, "action": "delta_since_last_seen", "response": resp}

        # 6. "Check WhatsApp" / "WhatsApp health"
        if text_lower in ("check whatsapp", "whatsapp status", "whatsapp health", "is whatsapp working"):
            hc = self.health_check()
            return {"success": True, "action": "health_check", "response": hc["summary"], "data": hc}

        # 7. "Open my WhatsApp" / "Open WhatsApp"
        if re.match(r'^(?:open|launch|start)\s+(?:my\s+)?whatsapp$', text_lower):
            if self.mock_mode:
                return {"success": True, "action": "activate_whatsapp", "response": "WhatsApp Desktop activated in simulation mode."}
            res = self.desktop_controller.activate_whatsapp()
            return {"success": res.success, "action": "activate_whatsapp", "response": "WhatsApp Desktop activated." if res.success else res.error}

        # 8. "Open my chat with <contact>" / "Open <contact>'s chat"
        m_open = re.match(r'open\s+(?:my\s+)?(?:chat|conversation)\s+(?:with\s+)?(.+)', text, re.IGNORECASE)
        if not m_open:
            m_open = re.match(r'open\s+(.+?)(?:\'s)?\s+(?:chat|conversation)$', text, re.IGNORECASE)
        if m_open:
            target = m_open.group(1).strip()
            res = self.open_conversation(target)
            if res.requires_confirmation:
                return {"success": False, "action": "open_conversation", "response": res.confirmation_reason}
            return {"success": res.success, "action": "open_conversation", "response": f"Opened chat with {target}." if res.success else res.error}

        # 9. "Summarize <contact>'s messages" / "What did <contact> say?"
        m_sum = re.match(r'summarize\s+(.+?)(?:\'s)?\s+messages?', text, re.IGNORECASE)
        if not m_sum:
            m_sum = re.match(r'what\s+did\s+(.+?)\s+(?:say|send|message)(?:\s+yesterday|\s+today)?\??$', text, re.IGNORECASE)
        if m_sum:
            target = m_sum.group(1).strip()
            summary = self.summarize_conversation(target)
            return {"success": True, "action": "summarize_conversation", "response": summary}

        # 10. "Read the latest message from <contact>" / "Read <contact>"
        m_read = re.match(r'read\s+(?:the\s+)?(?:latest|recent|last)?\s*(?:message\s+from\s+)?(.+)', text, re.IGNORECASE)
        if m_read:
            target = m_read.group(1).strip()
            # Check if target is not generic
            if target.lower() not in ("whatsapp", "my screen"):
                msgs = self.read_conversation(target, {"max_messages": 1})
                if msgs:
                    last_m = msgs[-1]
                    return {"success": True, "action": "read_message", "response": f"Latest message from {target}: \"{last_m.text}\""}
                return {"success": False, "action": "read_message", "response": f"No messages found from {target}."}

        # 11. "Call the person who just messaged me"
        if "person who just messaged me" in text_lower or "person who messaged me" in text_lower:
            act = self.get_recent_activity()
            if act.recent_senders:
                latest_sender = act.recent_senders[0]
                is_video = "video" in text_lower
                res = self.call(latest_sender, "video" if is_video else "voice")
                return {"success": res.success, "action": "call", "response": res.message or res.error}

        # 12. Video call commands ("Video call Mom", "Start a WhatsApp video call with Mom")
        m_vcall = re.match(r'(?:start\s+a\s+)?(?:whatsapp\s+)?video\s+call\s+(?:with\s+)?(.+?)(?:\s+on\s+whatsapp)?$', text, re.IGNORECASE)
        if not m_vcall:
            m_vcall = re.match(r'video\s+call\s+(.+?)(?:\s+on\s+whatsapp)?$', text, re.IGNORECASE)
        if m_vcall:
            target = m_vcall.group(1).strip()
            res = self.call(target, "video")
            if res.requires_confirmation:
                return {"success": False, "action": "call", "response": res.confirmation_reason}
            return {"success": res.success, "action": "call", "response": res.message or res.error}

        # 13. Voice call commands ("Call Rahul on WhatsApp", "WhatsApp Rahul")
        m_call = re.match(r'(?:start\s+a\s+)?(?:whatsapp\s+)?call\s+(.+?)(?:\s+on\s+whatsapp)?$', text, re.IGNORECASE)
        if not m_call and re.match(r'^whatsapp\s+([a-zA-Z0-9_\-\+ ]+)$', text, re.IGNORECASE):
            m_call = re.match(r'^whatsapp\s+(.+)$', text, re.IGNORECASE)
        if m_call:
            target = m_call.group(1).strip()
            if target.lower() not in ("updates", "status", "health"):
                res = self.call(target, "voice")
                if res.requires_confirmation:
                    return {"success": False, "action": "call", "response": res.confirmation_reason}
                return {"success": res.success, "action": "call", "response": res.message or res.error}

        # 14. Conversational Greetings & Wishes ("Say hello to Rahul", "Wish Ankit happy birthday", "Tell Priya congratulations")
        if any(text_lower.startswith(k) for k in ("say hello", "say hi", "say good morning", "say good evening", "say good night", "wish ", "tell ")):
            # Check for "Say hello to Rahul" or "Wish Ankit happy birthday"
            # Extract target
            m_target = re.search(r'(?:to|wish|tell)\s+([a-zA-Z0-9_\-\+]+)', text, re.IGNORECASE)
            if m_target:
                target = m_target.group(1).strip()
                composed_msg, is_greeting = MessageComposer.compose_from_intent(target, text)
                res = self.send_message(target, composed_msg)
                if res.requires_confirmation:
                    return {"success": False, "action": "send_message", "response": res.confirmation_reason}
                if res.success:
                    return {"success": True, "action": "send_message", "response": f"Done. I told {target}: \"{composed_msg}\""}
                return {"success": False, "action": "send_message", "response": res.error}

        # 15. Standard Messaging ("Message Dad saying...", "Tell Rahul I'll be there", "Send Rahul: ...", "Reply to him saying...")
        m_msg = re.match(r'(?:send\s+a?\s*message\s+to|message|tell|inform)\s+(.+?)\s+(?:saying|that|with)\s+(.+)', text, re.IGNORECASE)
        if not m_msg:
            m_msg = re.match(r'reply\s+(?:to\s+)?(.+?)\s+(?:saying|that|with)\s+(.+)', text, re.IGNORECASE)
        if not m_msg:
            m_msg = re.match(r'send\s+(.+?)\s*:\s*(.+)', text, re.IGNORECASE)
        if not m_msg:
            m_msg = re.match(r'(?:tell|inform)\s+([a-zA-Z0-9_\-\+]+)\s+(.+)', text, re.IGNORECASE)
        if m_msg:
            raw_target = m_msg.group(1).strip()
            target = self.context.resolve_target(raw_target)
            body = m_msg.group(2).strip().strip('"\'')
            res = self.send_message(target, body)
            if res.requires_confirmation:
                return {"success": False, "action": "send_message", "response": res.confirmation_reason}
            if res.success:
                disp_target = res.data.get('contact', target) if (isinstance(res.data, dict) and res.data.get('contact')) else target
                return {"success": True, "action": "send_message", "response": f"Done. I messaged {disp_target}: \"{body}\""}
            return {"success": False, "action": "send_message", "response": res.error}

        # Fallback
        return {
            "success": False,
            "action": "unknown",
            "response": "Sir, I did not recognize that specific WhatsApp instruction. You can ask me to call, message, read, or summarize WhatsApp."
        }


# Singleton WhatsAppAgent instance
whatsapp_agent = WhatsAppAgent()
