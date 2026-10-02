"""
J.A.R.V.I.S. Access Profiles & Permission Subsystem
Strict Two-Tier Operational Security Model:
1. LOCAL     (main.py, port 5001)   - Private Local Mac Companion (Full Mac Automation & Tools)
2. REMOTE_QA (main_2.py, port 5002) - Public Remote Internet Q&A Server (Zero Mac Actions / Conversational Only)
"""
from enum import Enum
from typing import Set

class AccessProfile(str, Enum):
    LOCAL = "LOCAL"         # Port 5001 - Private Local Mac Companion (Full Desktop Power)
    REMOTE_QA = "REMOTE_QA" # Port 5002 - Public Remote Internet Q&A Server (Zero Mac Actions)
    
    # Aliases
    PUBLIC = "REMOTE_QA"
    REMOTE_AUTH = "REMOTE_QA"
    OWNER = "LOCAL"

# Actions permitted for Local Desktop Mode only (main.py)
FULL_ALLOWED_ACTIONS: Set[str] = {
    # Core & Research
    "general_chat",
    "web_search",
    "read_page",
    "system_info",
    "briefing",
    "status",
    
    # Desktop Automation
    "desktop_type",
    "desktop_key",
    "desktop_snap",
    "desktop_minimize",
    "desktop_list_windows",
    "desktop_focus",
    "click",
    "double_click",
    "right_click",
    "move",
    "drag",
    "scroll",
    "ocr",
    
    # Vision & Copilot
    "analyze_screen",
    "screenshot",
    
    # Media & Communications
    "open_app",
    "close_app",
    "play_song",
    "media_control",
    "whatsapp",
    "whatsapp_call",
    "whatsapp_read",
    
    # Hardware & System
    "volume",
    "brightness",
    "lock_screen",
    "sleep",
    "toggle_gestures"
}

def is_action_permitted(profile: AccessProfile, action_name: str) -> bool:
    """Check if an action is allowed for a given operational access profile."""
    if not action_name:
        return True
    
    # ONLY LOCAL profile (main.py) has access to Mac desktop & OS capabilities
    if profile in (AccessProfile.LOCAL, "LOCAL"):
        return action_name in FULL_ALLOWED_ACTIONS or action_name.startswith("plugin:")
    
    # Remote Q&A profile has ZERO access to any Mac automation, desktop, or system action
    return False

def get_profile_permissions(profile: AccessProfile) -> Set[str]:
    """Retrieve full set of permitted actions for a profile."""
    if profile in (AccessProfile.LOCAL, "LOCAL"):
        return FULL_ALLOWED_ACTIONS.copy()
    # Remote Q&A has no permitted system actions
    return set()
