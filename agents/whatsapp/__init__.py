"""
J.A.R.V.I.S. WhatsApp Agent Package
Exposes core agents, resolvers, context memory, and safety engines.
"""
from .models import (
    ContactMatch, Message, Conversation, WhatsAppActivity,
    ActionResult, WhatsAppPrivacyMode, CallType, MessagePriority, MessageType
)
from .contact_resolver import ContactResolver, is_phone_number
from .context_memory import WhatsAppContextMemory, whatsapp_context_memory
from .message_composer import MessageComposer
from .permission_manager import WhatsAppPermissionManager, whatsapp_permission_manager
from .summarizer import WhatsAppSummarizer
from .activity_monitor import WhatsAppActivityMonitor, whatsapp_activity_monitor
from .mock_engine import WhatsAppMockEngine
from .desktop_controller import WhatsAppDesktopController
from .health_check import WhatsAppHealthCheck
from .agent import WhatsAppAgent, whatsapp_agent

__all__ = [
    "WhatsAppAgent",
    "whatsapp_agent",
    "ContactResolver",
    "is_phone_number",
    "WhatsAppContextMemory",
    "whatsapp_context_memory",
    "MessageComposer",
    "WhatsAppPermissionManager",
    "whatsapp_permission_manager",
    "WhatsAppSummarizer",
    "WhatsAppActivityMonitor",
    "whatsapp_activity_monitor",
    "WhatsAppMockEngine",
    "WhatsAppDesktopController",
    "WhatsAppHealthCheck",
    "ContactMatch",
    "Message",
    "Conversation",
    "WhatsAppActivity",
    "ActionResult",
    "WhatsAppPrivacyMode",
    "CallType",
    "MessagePriority",
    "MessageType"
]
