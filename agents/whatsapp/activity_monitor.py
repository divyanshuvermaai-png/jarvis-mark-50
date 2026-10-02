"""
J.A.R.V.I.S. WhatsApp Agent - Activity Monitor & Event Publisher
Monitors conversation activity, tracks state deltas ('What's new since I left?'),
and publishes structured events to the J.A.R.V.I.S. Event Bus.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from core.events import event_bus, Event, EventType
from .models import WhatsAppActivity, Conversation, Message

logger = logging.getLogger("jarvis.whatsapp.monitor")


class WhatsAppActivityMonitor:
    """
    Tracks WhatsApp activity transitions, unread deltas, and dispatches events.
    """

    def __init__(self):
        self.last_known_activity: Optional[WhatsAppActivity] = None
        self.last_inspected_timestamp: datetime = datetime.now()
        self.seen_message_ids: set = set()

    def set_baseline(self, activity: WhatsAppActivity):
        """Sets the reference baseline for calculating activity deltas."""
        self.last_known_activity = activity
        self.last_inspected_timestamp = datetime.now()
        for conv in activity.conversations:
            for msg in conv.messages:
                if msg.id:
                    self.seen_message_ids.add(msg.id)

    def record_activity(self, activity: WhatsAppActivity) -> Dict[str, Any]:
        """
        Records new activity, checks for changes, and publishes events to the event bus.
        Returns a delta summary.
        """
        previous_unread = self.last_known_activity.unread_count if self.last_known_activity else 0
        new_unread = activity.unread_count

        # Publish unread changed event if difference detected
        if new_unread != previous_unread:
            try:
                event_bus.publish(Event(
                    event_type=EventType.AUDIT_EVENT,
                    source="WhatsAppActivityMonitor",
                    payload={
                        "event": "whatsapp.unread.changed",
                        "old_count": previous_unread,
                        "new_count": new_unread
                    }
                ))
            except Exception as e:
                logger.debug(f"Event bus publish error: {e}")

        # Check for new messages
        new_messages: List[Message] = []
        for conv in activity.conversations:
            for msg in conv.messages:
                identifier = msg.id or f"{conv.contact_name}_{msg.timestamp}_{msg.text[:20]}"
                if identifier not in self.seen_message_ids:
                    self.seen_message_ids.add(identifier)
                    new_messages.append(msg)
                    try:
                        event_bus.publish(Event(
                            event_type=EventType.AUDIT_EVENT,
                            source="WhatsAppActivityMonitor",
                            payload={
                                "event": "whatsapp.message.received",
                                "contact": conv.contact_name,
                                "sender": msg.sender,
                                "timestamp": msg.timestamp,
                                "is_outgoing": msg.is_outgoing
                            }
                        ))
                    except Exception:
                        pass

        delta = {
            "new_message_count": len(new_messages),
            "unread_diff": new_unread - previous_unread,
            "new_senders": list({m.sender for m in new_messages if not m.is_outgoing})
        }

        self.last_known_activity = activity
        return delta

    def get_delta_since_last_seen(self, current_activity: WhatsAppActivity) -> str:
        """
        Answers: 'What's new since I left?' or 'What changed while I was away?'.
        """
        if not self.last_known_activity:
            self.set_baseline(current_activity)
            return "Sir, activity monitoring has just established a baseline. Here are your current updates:\n" + current_activity.summary

        # Identify senders who have updated since last inspection
        new_senders = []
        for conv in current_activity.conversations:
            # Check if this contact has unread or new activity
            if conv.unread_count > 0 or conv.needs_reply:
                new_senders.append(f"• {conv.contact_name}: {conv.unread_count} new message(s) — \"{conv.last_message_text}\"")

        # Update last inspected time
        self.last_inspected_timestamp = datetime.now()
        self.last_known_activity = current_activity

        if not new_senders:
            return "Sir, there have been no new incoming messages or unread updates since you last checked."

        return "Since you were last active, the following updates arrived:\n" + "\n".join(new_senders)


whatsapp_activity_monitor = WhatsAppActivityMonitor()
