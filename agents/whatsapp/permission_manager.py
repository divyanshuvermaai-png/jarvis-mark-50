"""
J.A.R.V.I.S. WhatsApp Agent - Permission & Policy Manager
Enforces fine-grained capability permissions, local-first privacy modes, and
intelligent friction-free confirmation policies.
"""
import os
import json
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from .models import WhatsAppPrivacyMode

logger = logging.getLogger("jarvis.whatsapp.permissions")

CONFIG_DIR = os.path.expanduser("~/.jarvis_system")
PERMISSIONS_FILE = os.path.join(CONFIG_DIR, "whatsapp_permissions.json")


class WhatsAppPermissionManager:
    """
    Controls runtime authorizations for WhatsApp capabilities.
    Allows users to toggle individual permissions safely.
    """

    DEFAULT_PERMISSIONS: Dict[str, bool] = {
        "read_messages": True,
        "send_messages": True,
        "call": True,
        "video_call": True,
        "summarize": True
    }

    def __init__(self, config_path: str = PERMISSIONS_FILE):
        self.config_path = config_path
        self.privacy_mode: WhatsAppPrivacyMode = WhatsAppPrivacyMode.STRICT_LOCAL
        self.proactive_enabled: bool = False
        self.permissions: Dict[str, bool] = dict(self.DEFAULT_PERMISSIONS)
        self.load()

    def load(self):
        """Loads permissions and privacy policy from disk."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.permissions.update(data.get("permissions", {}))
                    mode_str = data.get("privacy_mode", WhatsAppPrivacyMode.STRICT_LOCAL.value)
                    try:
                        self.privacy_mode = WhatsAppPrivacyMode(mode_str)
                    except ValueError:
                        self.privacy_mode = WhatsAppPrivacyMode.STRICT_LOCAL
                    self.proactive_enabled = bool(data.get("proactive_enabled", False))
            except Exception as e:
                logger.warning(f"Failed to load WhatsApp permissions config: {e}")

    def save(self):
        """Persists permissions and policy to disk."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump({
                    "permissions": self.permissions,
                    "privacy_mode": self.privacy_mode.value,
                    "proactive_enabled": self.proactive_enabled
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save WhatsApp permissions config: {e}")

    def is_allowed(self, capability: str) -> Tuple[bool, str]:
        """
        Checks if a specific capability is allowed.
        Capability can be: 'read_messages', 'send_messages', 'call', 'video_call', 'summarize'
        """
        cap = capability.lower().strip()
        allowed = self.permissions.get(cap, False)
        if not allowed:
            return False, f"Permission '{cap}' for WhatsApp is currently disabled in J.A.R.V.I.S. settings."
        return True, "Allowed"

    def set_permission(self, capability: str, allowed: bool):
        """Sets an individual permission flag."""
        cap = capability.lower().strip()
        self.permissions[cap] = allowed
        self.save()

    def set_privacy_mode(self, mode: WhatsAppPrivacyMode):
        """Updates the privacy mode."""
        self.privacy_mode = mode
        self.save()

    def set_proactive(self, enabled: bool):
        """Toggles proactive notifications."""
        self.proactive_enabled = enabled
        self.save()

    def get_status(self) -> Dict[str, Any]:
        """Returns structured status dictionary."""
        return {
            "permissions": self.permissions,
            "privacy_mode": self.privacy_mode.value,
            "proactive_enabled": self.proactive_enabled
        }

    def reset_defaults(self):
        """Resets all permissions to defaults."""
        self.permissions = dict(self.DEFAULT_PERMISSIONS)
        self.privacy_mode = WhatsAppPrivacyMode.STRICT_LOCAL
        self.proactive_enabled = False
        self.save()


# Default singleton instance
whatsapp_permission_manager = WhatsAppPermissionManager()
