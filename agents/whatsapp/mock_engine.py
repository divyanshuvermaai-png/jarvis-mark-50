"""
J.A.R.V.I.S. WhatsApp Agent - Mock Simulation Engine
Provides 100% offline, reproducible simulation for contacts, conversations,
unread notifications, message sending, and calls without touching real WhatsApp.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import (
    ContactMatch, Message, Conversation, WhatsAppActivity,
    ActionResult, MessagePriority, MessageType, CallType
)


class WhatsAppMockEngine:
    """
    Simulated WhatsApp environment for testing and safe development.
    Active when WHATSAPP_MOCK_MODE is enabled.
    """

    def __init__(self):
        self.mock_contacts = [
            "Rahul Sharma",
            "Mom",
            "Dad",
            "Ankit",
            "Priya",
            "Subham",
            "Divyanshu Verma",
            "Alex Smith",
            "Alex Johnson"
        ]

        self.sent_messages: List[Dict[str, Any]] = []
        self.initiated_calls: List[Dict[str, Any]] = []
        self._init_mock_conversations()

    def _init_mock_conversations(self):
        """Initializes realistic conversations with unreads and context."""
        now = datetime.now().strftime("%I:%M %p")

        self.conversations: Dict[str, Conversation] = {
            "Rahul Sharma": Conversation(
                contact_name="Rahul Sharma",
                unread_count=4,
                messages=[
                    Message(sender="Rahul Sharma", text="Hey Divyanshu, quick update about tomorrow."),
                    Message(sender="Rahul Sharma", text="The client meeting is confirmed for 11 AM."),
                    Message(sender="Rahul Sharma", text="Please make sure to bring the project architecture documents."),
                    Message(sender="Rahul Sharma", text="Can you confirm if you'll be there?"),
                ],
                last_activity=now,
                last_message_text="Can you confirm if you'll be there?",
                urgency_level=MessagePriority.IMPORTANT,
                needs_reply=True
            ),
            "Mom": Conversation(
                contact_name="Mom",
                unread_count=2,
                messages=[
                    Message(sender="Mom", text="Beta, when will you be home?"),
                    Message(sender="Mom", text="Please call me when you are free.")
                ],
                last_activity=now,
                last_message_text="Please call me when you are free.",
                urgency_level=MessagePriority.IMPORTANT,
                needs_reply=True
            ),
            "Ankit": Conversation(
                contact_name="Ankit",
                unread_count=1,
                messages=[
                    Message(sender="Ankit", text="Hey, check out this screenshot of the new UI design. What do you think?", message_type=MessageType.IMAGE)
                ],
                last_activity=now,
                last_message_text="Hey, check out this screenshot of the new UI design. What do you think?",
                urgency_level=MessagePriority.NORMAL,
                needs_reply=True
            ),
            "Priya": Conversation(
                contact_name="Priya",
                unread_count=0,
                messages=[
                    Message(sender="Priya", text="The team summit venue has been finalized at the Tech Hub.")
                ],
                last_activity=now,
                last_message_text="The team summit venue has been finalized at the Tech Hub.",
                urgency_level=MessagePriority.LOW_PRIORITY,
                needs_reply=False
            )
        }

    def find_contacts(self, query: str) -> List[ContactMatch]:
        """Simulates contact resolution."""
        q = query.lower().strip()
        matches = []
        for c in self.mock_contacts:
            if q in c.lower():
                matches.append(ContactMatch(
                    name=c,
                    match_score=1.0 if q == c.lower() else 0.85,
                    is_exact=(q == c.lower()),
                    source="mock_contacts",
                    raw_query=query
                ))
        return matches

    def open_conversation(self, contact_name: str) -> ActionResult:
        """Simulates opening a chat."""
        return ActionResult(
            success=True,
            action="open_conversation",
            data={"contact": contact_name, "mode": "mock"},
            message=f"Opened conversation with {contact_name}."
        )

    def read_conversation(self, contact_name: str, max_messages: int = 10) -> List[Message]:
        """Returns mock messages for contact."""
        conv = self.conversations.get(contact_name)
        if not conv:
            # Check partial match
            for name, c in self.conversations.items():
                if contact_name.lower() in name.lower():
                    conv = c
                    break

        if conv:
            return conv.messages[-max_messages:]
        return [
            Message(sender=contact_name, text="Hey! All good here.")
        ]

    def send_message(self, contact_name: str, message: str) -> ActionResult:
        """Simulates sending message."""
        self.sent_messages.append({
            "contact": contact_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        # Add outgoing message to conversation if exists
        if contact_name in self.conversations:
            self.conversations[contact_name].messages.append(
                Message(sender="You", text=message, is_outgoing=True)
            )
            self.conversations[contact_name].needs_reply = False

        return ActionResult(
            success=True,
            action="send_message",
            data={"contact": contact_name, "message": message, "mode": "mock"},
            message=f"Sent message to {contact_name}."
        )

    def call(self, contact_name: str, call_type: CallType = CallType.VOICE) -> ActionResult:
        """Simulates initiating voice or video call."""
        self.initiated_calls.append({
            "contact": contact_name,
            "type": call_type.value,
            "timestamp": datetime.now().isoformat()
        })
        return ActionResult(
            success=True,
            action="call",
            data={"contact": contact_name, "type": call_type.value, "mode": "mock"},
            message=f"Calling {contact_name} on WhatsApp ({call_type.value} call)..."
        )

    def get_recent_activity(self) -> WhatsAppActivity:
        """Returns structured mock activity matching prompt specifications."""
        conv_list = list(self.conversations.values())
        total_unread = sum(c.unread_count for c in conv_list)
        recent_senders = [c.contact_name for c in conv_list if c.unread_count > 0]
        needs_reply = [c.contact_name for c in conv_list if c.needs_reply]

        return WhatsAppActivity(
            total_conversations=len(conv_list),
            unread_count=total_unread,
            recent_senders=recent_senders,
            needs_reply_count=len(needs_reply),
            needs_reply_contacts=needs_reply,
            conversations=conv_list,
            summary=(
                f"You have {len(conv_list)} recent WhatsApp conversations.\n"
                f"{len(recent_senders)} people sent new messages:\n"
                f"• Rahul Sharma — 4 messages (discussing tomorrow's meeting)\n"
                f"• Mom — 2 messages (asked you to call her)\n"
                f"• Ankit — 1 message (shared photo & asked for feedback)\n\n"
                f"{len(needs_reply)} conversations appear to need a reply."
            )
        )
