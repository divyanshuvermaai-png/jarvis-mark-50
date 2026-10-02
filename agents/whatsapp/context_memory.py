"""
J.A.R.V.I.S. WhatsApp Agent - Context Memory
Maintains multi-turn conversational context, resolves pronouns (him/her/them),
and tracks action continuity across turns.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import re


class WhatsAppContextMemory:
    """
    In-memory state tracker for conversational WhatsApp continuity.
    Enables follow-ups such as "Tell him I'll be there" or "Call him".
    """

    PRONOUNS = {"him", "her", "them", "this person", "that person", "the person who just messaged me", "the sender"}

    def __init__(self):
        self.last_contact: Optional[str] = None
        self.last_opened_conversation: Optional[str] = None
        self.last_mentioned_message: Optional[str] = None
        self.last_action: Optional[str] = None
        self.last_message_text: Optional[str] = None
        self.last_updated: Optional[datetime] = None

    @property
    def last_whatsapp_contact(self) -> Optional[str]:
        return self.last_contact

    def update_contact(self, contact: str):
        """Updates the active contact reference."""
        if contact and contact.strip():
            self.last_contact = contact.strip()
            self.last_opened_conversation = self.last_contact
            self.last_updated = datetime.now()

    def update_action(self, action: str, contact: Optional[str] = None, message: Optional[str] = None):
        """Updates the last action and optional message text."""
        self.last_action = action
        if contact:
            self.update_contact(contact)
        if message:
            self.last_message_text = message
        self.last_updated = datetime.now()

    def resolve_target(self, query: str) -> str:
        """
        Resolves query to known contact name if query is a pronoun or contextual reference.
        If no pronoun match, returns query unchanged.
        """
        cleaned = query.strip().lower()

        # Check pronoun references
        if cleaned in self.PRONOUNS:
            if self.last_contact:
                return self.last_contact

        # Check regex phrases like "to him" or "call him"
        for p in self.PRONOUNS:
            if p in cleaned:
                if self.last_contact:
                    return self.last_contact

        return query

    def resolve_message(self, message_query: str) -> str:
        """
        Resolves phrases like 'the same message' or 'send that' to the last dispatched message.
        """
        cleaned = message_query.strip().lower()
        if cleaned in {"the same message", "that message", "the same thing", "send the same"}:
            if self.last_message_text:
                return self.last_message_text
        return message_query

    def get_state(self) -> Dict[str, Any]:
        """Returns snapshot of current memory state."""
        return {
            "last_contact": self.last_contact,
            "last_opened_conversation": self.last_opened_conversation,
            "last_mentioned_message": self.last_mentioned_message,
            "last_action": self.last_action,
            "last_message_text": self.last_message_text,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    def clear(self):
        """Clears memory context."""
        self.last_contact = None
        self.last_opened_conversation = None
        self.last_mentioned_message = None
        self.last_action = None
        self.last_message_text = None
        self.last_updated = None


# Global context instance for J.A.R.V.I.S. runtime
whatsapp_context_memory = WhatsAppContextMemory()
