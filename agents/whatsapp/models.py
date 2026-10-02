"""
J.A.R.V.I.S. WhatsApp Agent Subsystem - Data Models
Defines structured entities for contacts, messages, conversations, and agent activity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class CallType(str, Enum):
    VOICE = "voice"
    VIDEO = "video"


class WhatsAppPrivacyMode(str, Enum):
    STRICT_LOCAL = "STRICT_LOCAL"          # 100% on-device processing only (Gemma 4 E2B / extractive)
    LOCAL_PREFERRED = "LOCAL_PREFERRED"    # Local preferred, cloud fallback allowed with notice
    CLOUD_ALLOWED = "CLOUD_ALLOWED"        # Cloud reasoning permitted for deep summarization


class MessagePriority(str, Enum):
    URGENT = "URGENT"             # Deadlines, immediate action requests, emergencies
    IMPORTANT = "IMPORTANT"       # Work meetings, confirmations, family requests
    NORMAL = "NORMAL"             # General chats, discussions
    LOW_PRIORITY = "LOW_PRIORITY" # Greetings, status updates, memes, stickers
    UNKNOWN = "UNKNOWN"           # Unclassified or empty messages


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"
    LINK = "LINK"
    STICKER = "STICKER"
    GIF = "GIF"
    VOICE_NOTE = "VOICE_NOTE"
    LOCATION = "LOCATION"
    CONTACT = "CONTACT"


@dataclass
class ContactMatch:
    name: str
    phone: Optional[str] = None
    id: Optional[str] = None
    match_score: float = 1.0
    is_exact: bool = False
    source: str = "whatsapp"
    raw_query: str = ""

    def __post_init__(self):
        if self.id is None:
            self.id = self.phone or self.name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "phone": self.phone,
            "match_score": round(self.match_score, 2),
            "is_exact": self.is_exact,
            "source": self.source,
            "raw_query": self.raw_query
        }


@dataclass
class Message:
    sender: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_outgoing: bool = False
    message_type: MessageType = MessageType.TEXT
    is_read: bool = True
    priority: MessagePriority = MessagePriority.NORMAL
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "text": self.text,
            "timestamp": self.timestamp,
            "is_outgoing": self.is_outgoing,
            "message_type": self.message_type.value,
            "is_read": self.is_read,
            "priority": self.priority.value
        }


@dataclass
class Conversation:
    contact_name: str
    unread_count: int = 0
    messages: List[Message] = field(default_factory=list)
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    last_message_text: str = ""
    urgency_level: MessagePriority = MessagePriority.NORMAL
    needs_reply: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contact_name": self.contact_name,
            "unread_count": self.unread_count,
            "messages": [m.to_dict() for m in self.messages],
            "last_activity": self.last_activity,
            "last_message_text": self.last_message_text,
            "urgency_level": self.urgency_level.value,
            "needs_reply": self.needs_reply
        }


@dataclass
class WhatsAppActivity:
    total_conversations: int = 0
    unread_count: int = 0
    recent_senders: List[str] = field(default_factory=list)
    needs_reply_count: int = 0
    needs_reply_contacts: List[str] = field(default_factory=list)
    conversations: List[Conversation] = field(default_factory=list)
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_conversations": self.total_conversations,
            "unread_count": self.unread_count,
            "recent_senders": self.recent_senders,
            "needs_reply_count": self.needs_reply_count,
            "needs_reply_contacts": self.needs_reply_contacts,
            "conversations": [c.to_dict() for c in self.conversations],
            "last_checked": self.last_checked,
            "summary": self.summary
        }


@dataclass
class ActionResult:
    success: bool
    action: str
    data: Any = None
    message: Optional[str] = None
    error: Optional[str] = None
    errorCode: Optional[str] = None
    recoverable: bool = True
    requires_confirmation: bool = False
    confirmation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "errorCode": self.errorCode,
            "recoverable": self.recoverable,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_reason": self.confirmation_reason
        }
