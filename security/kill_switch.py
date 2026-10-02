"""
J.A.R.V.I.S. Security Kernel — Global Kill Switch & Security State Machine
Allows immediate revocation of privileged tools and enforcement of lockdown.
The AI CANNOT disable the kill switch via prompt or natural language.
"""
import time
import threading
from enum import Enum
from typing import Tuple, Optional

class SecurityState(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    LOCKED = "LOCKED"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    AUTH_REQUIRED = "AUTH_REQUIRED"


class KillSwitchManager:
    """Thread-safe global security state controller."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KillSwitchManager, cls).__new__(cls)
                cls._instance._state = SecurityState.NORMAL
                cls._instance._reason = ""
                cls._instance._activated_at = 0.0
                cls._instance._activated_by = ""
        return cls._instance

    @property
    def state(self) -> SecurityState:
        with self._lock:
            return self._state

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._state in (SecurityState.KILL_SWITCH_ACTIVE, SecurityState.LOCKED)

    def get_state(self) -> SecurityState:
        with self._lock:
            return self._state

    def is_kill_switch_active(self) -> bool:
        with self._lock:
            return self._state in (SecurityState.KILL_SWITCH_ACTIVE, SecurityState.LOCKED)

    def reset(self, actor: str = "CONSOLE") -> None:
        """Reset state to NORMAL."""
        with self._lock:
            self._state = SecurityState.NORMAL
            self._reason = ""
            self._activated_at = 0.0
            self._activated_by = ""

    def activate(self, reason: str = "Manual security trigger", source: str = "LOCAL_OWNER", actor: Optional[str] = None) -> None:
        """Immediately lock down system and deny all privileged tools."""
        act = actor or source
        with self._lock:
            self._state = SecurityState.KILL_SWITCH_ACTIVE
            self._reason = reason
            self._activated_at = time.time()
            self._activated_by = act
            print(f"\n🚨 [KILL SWITCH ACTIVATED] Reason: {reason} | Triggered by: {act}\n", flush=True)

    def deactivate(self, secret_candidate: Optional[str] = None, is_local_console: bool = False) -> Tuple[bool, str]:
        """
        Disarm kill switch. Natural language prompts CANNOT call this.
        Requires verified owner secret or direct local console execution.
        """
        from .trust import TrustLevel
        from core.auth import verify_remote_secret

        with self._lock:
            if is_local_console:
                self._state = SecurityState.NORMAL
                self._reason = ""
                return True, "Kill switch disarmed via verified local console."

            if secret_candidate and verify_remote_secret(secret_candidate):
                self._state = SecurityState.NORMAL
                self._reason = ""
                return True, "Kill switch disarmed with verified owner secret."

            return False, "Authorization denied. Valid owner secret or local console required to reset kill switch."

    def lock_workstation(self, reason: str = "Workstation lock requested") -> None:
        with self._lock:
            self._state = SecurityState.LOCKED
            self._reason = reason

    def unlock_workstation(self) -> None:
        with self._lock:
            if self._state == SecurityState.LOCKED:
                self._state = SecurityState.NORMAL
                self._reason = ""

    def get_diagnostics(self) -> dict:
        with self._lock:
            return {
                "state": self._state.value,
                "is_active": self._state in (SecurityState.KILL_SWITCH_ACTIVE, SecurityState.LOCKED),
                "reason": self._reason,
                "activated_at": self._activated_at,
                "activated_by": self._activated_by
            }


# Global Singleton
kill_switch = KillSwitchManager()
