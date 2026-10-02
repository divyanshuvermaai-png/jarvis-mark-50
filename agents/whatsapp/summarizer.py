"""
J.A.R.V.I.S. WhatsApp Agent - Conversation Summarizer & Priority Classifier
Provides local-first conversation summarization, message deduplication,
context compression, and urgency classification.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from .models import Message, Conversation, WhatsAppActivity, MessagePriority, WhatsAppPrivacyMode


class WhatsAppSummarizer:
    """
    Local-first conversational summarizer.
    Under STRICT_LOCAL mode, executes deterministic key-point extraction and urgency scoring
    without transmitting any message content outside the device.
    """

    URGENT_KEYWORDS = [
        "urgent", "asap", "emergency", "immediately", "deadline", "right now",
        "quick", "hurry", "critical", "important", "alert"
    ]

    QUESTION_INDICATORS = [
        "?", "can you", "could you", "will you", "are you", "when", "where",
        "what", "why", "how", "let me know", "confirm", "reply", "update me"
    ]

    LOW_PRIORITY_PATTERNS = [
        r'^(?:ok|okay|k|cool|nice|good|great|thanks|thx|ty|gm|gn|lol|haha)\b',
        r'^(?:👍|❤️|😂|🔥|🙏|👏|✨|🙌)+$'
    ]

    @classmethod
    def classify_priority(cls, text: str) -> MessagePriority:
        """Classifies message urgency into structured priority tiers."""
        txt_lower = text.lower().strip()
        if not txt_lower:
            return MessagePriority.UNKNOWN

        # Check urgent keywords
        if any(k in txt_lower for k in cls.URGENT_KEYWORDS):
            return MessagePriority.URGENT

        # Check question/confirmation request
        if any(q in txt_lower for q in cls.QUESTION_INDICATORS):
            return MessagePriority.IMPORTANT

        # Check low priority short replies/emojis
        for pat in cls.LOW_PRIORITY_PATTERNS:
            if re.match(pat, txt_lower):
                return MessagePriority.LOW_PRIORITY

        return MessagePriority.NORMAL

    @classmethod
    def compress_messages(cls, messages: List[Message], max_messages: int = 20) -> List[Message]:
        """
        Deduplicates consecutive identical messages and filters media metadata noise.
        """
        if not messages:
            return []

        recent = messages[-max_messages:]
        compressed: List[Message] = []
        last_text = None

        for msg in recent:
            cleaned_text = msg.text.strip()
            # Omit identical consecutive duplicate messages
            if cleaned_text == last_text:
                continue

            last_text = cleaned_text
            compressed.append(msg)

        return compressed

    @classmethod
    def summarize_conversation(
        cls,
        contact_name: str,
        messages: List[Message],
        privacy_mode: WhatsAppPrivacyMode = WhatsAppPrivacyMode.STRICT_LOCAL
    ) -> str:
        """
        Generates a concise bulleted summary of messages from a single contact.
        """
        compressed = cls.compress_messages(messages)
        if not compressed:
            return f"No recent messages found with {contact_name}."

        incoming = [m for m in compressed if not m.is_outgoing]
        if not incoming:
            return f"All recent messages with {contact_name} were sent by you."

        # Extract salient points and questions
        key_points: List[str] = []
        questions: List[str] = []
        highest_priority = MessagePriority.NORMAL

        for m in incoming:
            prio = cls.classify_priority(m.text)
            if prio == MessagePriority.URGENT:
                highest_priority = MessagePriority.URGENT
            elif prio == MessagePriority.IMPORTANT and highest_priority != MessagePriority.URGENT:
                highest_priority = MessagePriority.IMPORTANT

            # Check if this message is a direct question or request
            if any(q in m.text.lower() for q in cls.QUESTION_INDICATORS) or "?" in m.text:
                questions.append(m.text.strip())
            else:
                key_points.append(m.text.strip())

        # Construct readable response
        lines = [
            f"Conversation with {contact_name}:",
            f"{contact_name} sent {len(incoming)} recent message{'s' if len(incoming) > 1 else ''}."
        ]

        if key_points:
            lines.append("Main points:")
            for pt in key_points[-4:]:
                lines.append(f"• {pt}")

        if questions:
            lines.append("Requests / Questions:")
            for q in questions[-3:]:
                lines.append(f"• {q}")

        # Overall summary line
        if highest_priority == MessagePriority.URGENT:
            lines.append(f"Overall: This conversation contains time-sensitive updates and likely needs a prompt reply.")
        elif questions:
            lines.append(f"Overall: {contact_name} asked for your input and likely needs a reply.")
        else:
            lines.append(f"Overall: Latest update received from {contact_name}.")

        return "\n".join(lines)

    @classmethod
    def summarize_activity(
        cls,
        activity: WhatsAppActivity,
        privacy_mode: WhatsAppPrivacyMode = WhatsAppPrivacyMode.STRICT_LOCAL
    ) -> str:
        """
        Produces a structured macro summary of all recent WhatsApp activity.
        """
        if activity.total_conversations == 0 and not activity.conversations:
            return "Sir, you currently have no new or recent WhatsApp activity."

        lines = [
            "WHATSAPP EXECUTIVE BRIEFING",
            "----------------------------",
            f"You have {activity.total_conversations} recent WhatsApp conversation{'s' if activity.total_conversations != 1 else ''} ({activity.unread_count} Unread Messages)."
        ]

        if activity.recent_senders:
            lines.append(f"\n{len(activity.recent_senders)} contact(s) sent messages recently:")
            for conv in activity.conversations:
                if conv.contact_name in activity.recent_senders:
                    cnt = len(conv.messages) if conv.messages else max(1, conv.unread_count)
                    brief = conv.last_message_text if conv.last_message_text else "Recent activity"
                    lines.append(f"• {conv.contact_name} ({cnt} msg{'s' if cnt != 1 else ''}): \"{brief}\"")

        if activity.needs_reply_count > 0:
            lines.append(f"\n{activity.needs_reply_count} conversation(s) likely need a reply: {', '.join(activity.needs_reply_contacts)}")
        else:
            lines.append("\nNo conversations appear to need urgent reply.")

        return "\n".join(lines)

    @classmethod
    def get_senders_summary(cls, activity: WhatsAppActivity) -> str:
        """
        Direct answer to 'Who messaged me?' or 'Who sent me messages today?'.
        """
        if not activity.recent_senders:
            return "No contacts have sent you messages recently."

        sender_lines = []
        for conv in activity.conversations:
            if conv.contact_name in activity.recent_senders:
                unr = f" ({conv.unread_count} unread)" if conv.unread_count > 0 else ""
                last = f" — \"{conv.last_message_text}\"" if conv.last_message_text else ""
                sender_lines.append(f"• {conv.contact_name}{unr}{last}")

        return f"Recent WhatsApp senders:\n" + "\n".join(sender_lines)

    @classmethod
    def get_needs_reply_summary(cls, activity: WhatsAppActivity) -> str:
        """
        Direct answer to 'Who needs a reply?'.
        """
        if not activity.needs_reply_contacts:
            return "Sir, none of your recent conversations appear to be waiting for an urgent reply."

        details = []
        for conv in activity.conversations:
            if conv.contact_name in activity.needs_reply_contacts:
                details.append(f"• {conv.contact_name}: \"{conv.last_message_text}\"")

        return f"The following {len(activity.needs_reply_contacts)} contact(s) likely need a reply:\n" + "\n".join(details)
