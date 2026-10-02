"""
J.A.R.V.I.S. Core Event Bus
Provides lightweight, decoupled event pub/sub for all subsystems.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any, Dict, List
from enum import Enum
import threading

class EventType(str, Enum):
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    TASK_CREATED = "TASK_CREATED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TOOL_REQUESTED = "TOOL_REQUESTED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    MODEL_ROUTED = "MODEL_ROUTED"
    SECURITY_ALERT = "SECURITY_ALERT"
    AUDIT_EVENT = "AUDIT_EVENT"
    KILL_SWITCH_TRIGGERED = "KILL_SWITCH_TRIGGERED"
    WHATSAPP_MESSAGE_RECEIVED = "whatsapp.message.received"
    WHATSAPP_CONVERSATION_UPDATED = "whatsapp.conversation.updated"
    WHATSAPP_UNREAD_CHANGED = "whatsapp.unread.changed"
    WHATSAPP_CALL_STARTED = "whatsapp.call.started"
    WHATSAPP_CALL_ENDED = "whatsapp.call.ended"
    WHATSAPP_ACTION_FAILED = "whatsapp.action.failed"

@dataclass
class Event:
    event_type: EventType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = {}
                cls._instance._sub_lock = threading.RLock()
            return cls._instance

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        with self._sub_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        with self._sub_lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event: Event):
        with self._sub_lock:
            listeners = list(self._subscribers.get(event.event_type, []))
            # Also notify wildcard subscribers if any
            wildcard = list(self._subscribers.get("*", []))
        
        for handler in listeners + wildcard:
            try:
                handler(event)
            except Exception as e:
                # Do not let listener errors crash the bus
                pass

    def clear(self):
        with self._sub_lock:
            self._subscribers.clear()

event_bus = EventBus()
