"""
J.A.R.V.I.S. Security Kernel — Capabilities & Tool Manifest Subsystem
Defines explicit authorization capabilities, risk ratings, and tool metadata.
The model is NOT the authority.
"""
from enum import Enum
from typing import Dict, Set, Optional, NamedTuple
from .trust import TrustLevel

class Capability(str, Enum):
    # Safe capabilities
    CHAT = "CHAT"
    STATUS = "STATUS"
    SYSTEM_INFO_READ = "SYSTEM_INFO_READ"

    # Sensitive capabilities
    MEMORY_READ = "MEMORY_READ"
    MEMORY_WRITE = "MEMORY_WRITE"
    SCREEN_READ = "SCREEN_READ"
    VISION = "VISION"
    FILE_READ = "FILE_READ"
    AUDIO_CONTROL = "AUDIO_CONTROL"

    # High-Risk capabilities
    APP_CONTROL = "APP_CONTROL"
    WINDOW_CONTROL = "WINDOW_CONTROL"
    MOUSE_CONTROL = "MOUSE_CONTROL"
    KEYBOARD_CONTROL = "KEYBOARD_CONTROL"
    BROWSER_AUTOMATION = "BROWSER_AUTOMATION"
    WHATSAPP_AUTOMATION = "WHATSAPP_AUTOMATION"

    # Critical capabilities
    FILE_WRITE = "FILE_WRITE"
    CODE_EXECUTION = "CODE_EXECUTION"
    SHELL_EXECUTION = "SHELL_EXECUTION"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    SENSITIVE = "SENSITIVE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

RiskTier = RiskLevel


class ToolManifestEntry(NamedTuple):
    tool_name: str
    capability: Capability
    risk_level: RiskLevel
    allowed_trust_levels: Set[TrustLevel]
    requires_confirmation: bool = False
    description: str = ""


# Default trust sets
OWNER_ONLY: Set[TrustLevel] = {
    TrustLevel.LOCAL_OWNER,
    TrustLevel.AUTHENTICATED_OWNER,
    TrustLevel.SYSTEM_INTERNAL
}

LOCAL_ONLY: Set[TrustLevel] = {
    TrustLevel.LOCAL_OWNER,
    TrustLevel.SYSTEM_INTERNAL
}

ALL_TRUST: Set[TrustLevel] = {
    TrustLevel.REMOTE_PUBLIC,
    TrustLevel.LOCAL_USER,
    TrustLevel.LOCAL_OWNER,
    TrustLevel.AUTHENTICATED_OWNER,
    TrustLevel.SYSTEM_INTERNAL
}

DISABLED_BY_DEFAULT: Set[TrustLevel] = set()


TOOL_MANIFEST: Dict[str, ToolManifestEntry] = {
    # Safe & Informational
    "general_chat": ToolManifestEntry("general_chat", Capability.CHAT, RiskLevel.LOW, ALL_TRUST, False, "Conversational AI text response"),
    "status": ToolManifestEntry("status", Capability.STATUS, RiskLevel.LOW, ALL_TRUST, False, "Basic health & service status"),
    "system_info": ToolManifestEntry("system_info", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Hardware diagnostics"),
    "briefing": ToolManifestEntry("briefing", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Morning status briefing"),

    # Browser & Research
    "web_search": ToolManifestEntry("web_search", Capability.BROWSER_AUTOMATION, RiskLevel.MODERATE, OWNER_ONLY, False, "DuckDuckGo web search"),
    "read_page": ToolManifestEntry("read_page", Capability.BROWSER_AUTOMATION, RiskLevel.MODERATE, OWNER_ONLY, False, "Fetch & parse webpage content"),

    # Audio & Display
    "volume": ToolManifestEntry("volume", Capability.AUDIO_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Adjust Mac audio volume"),
    "brightness": ToolManifestEntry("brightness", Capability.SYSTEM_ADMIN, RiskLevel.LOW, OWNER_ONLY, False, "Adjust screen brightness"),
    "play_song": ToolManifestEntry("play_song", Capability.APP_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Play song on Spotify"),
    "media_control": ToolManifestEntry("media_control", Capability.APP_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Spotify / Apple Music play/pause/skip"),

    # App Management
    "open_app": ToolManifestEntry("open_app", Capability.APP_CONTROL, RiskLevel.MODERATE, OWNER_ONLY, False, "Launch macOS application"),
    "close_app": ToolManifestEntry("close_app", Capability.APP_CONTROL, RiskLevel.MODERATE, OWNER_ONLY, False, "Quit macOS application"),

    # Vision & Screen OCR
    "screenshot": ToolManifestEntry("screenshot", Capability.SCREEN_READ, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Capture screen to file"),
    "analyze_screen": ToolManifestEntry("analyze_screen", Capability.VISION, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Screen capture with vision/OCR analysis"),
    "ocr": ToolManifestEntry("ocr", Capability.VISION, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Optical character recognition on screen"),

    # Desktop Keyboard Automation
    "desktop_type": ToolManifestEntry("desktop_type", Capability.KEYBOARD_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Type text string via simulated keystrokes"),
    "desktop_key": ToolManifestEntry("desktop_key", Capability.KEYBOARD_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Press special key or hotkey shortcut"),

    # Desktop Window Management
    "desktop_snap": ToolManifestEntry("desktop_snap", Capability.WINDOW_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Snap frontmost window left/right/maximize"),
    "desktop_minimize": ToolManifestEntry("desktop_minimize", Capability.WINDOW_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Minimize frontmost window"),
    "desktop_list_windows": ToolManifestEntry("desktop_list_windows", Capability.WINDOW_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "List all visible window titles"),
    "desktop_focus": ToolManifestEntry("desktop_focus", Capability.WINDOW_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Bring specified app window to front"),

    # Desktop Mouse Automation
    "click": ToolManifestEntry("click", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Click at screen coordinates"),
    "double_click": ToolManifestEntry("double_click", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Double click at screen coordinates"),
    "right_click": ToolManifestEntry("right_click", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Right click at screen coordinates"),
    "move": ToolManifestEntry("move", Capability.MOUSE_CONTROL, RiskLevel.MODERATE, OWNER_ONLY, False, "Move cursor to screen coordinates"),
    "drag": ToolManifestEntry("drag", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Click-and-drag between coordinates"),
    "scroll": ToolManifestEntry("scroll", Capability.MOUSE_CONTROL, RiskLevel.LOW, OWNER_ONLY, False, "Scroll viewport up or down"),
    "down": ToolManifestEntry("down", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Mouse button down"),
    "up": ToolManifestEntry("up", Capability.MOUSE_CONTROL, RiskLevel.HIGH, OWNER_ONLY, False, "Mouse button up"),
    "screen_size": ToolManifestEntry("screen_size", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Get screen resolution"),

    # WhatsApp Automation
    "whatsapp": ToolManifestEntry("whatsapp", Capability.WHATSAPP_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Send WhatsApp message"),
    "whatsapp_call": ToolManifestEntry("whatsapp_call", Capability.WHATSAPP_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Initiate WhatsApp voice/video call"),
    "whatsapp_read": ToolManifestEntry("whatsapp_read", Capability.WHATSAPP_AUTOMATION, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Read recent WhatsApp chat messages"),
    "whatsapp_media": ToolManifestEntry("whatsapp_media", Capability.WHATSAPP_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Send WhatsApp media attachment"),
    "whatsapp_activity_summary": ToolManifestEntry("whatsapp_activity_summary", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "Executive summary of recent WhatsApp communications"),
    "whatsapp_who_messaged": ToolManifestEntry("whatsapp_who_messaged", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "List recent WhatsApp message senders"),
    "whatsapp_needs_reply": ToolManifestEntry("whatsapp_needs_reply", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "List WhatsApp contacts awaiting response"),
    "whatsapp_delta": ToolManifestEntry("whatsapp_delta", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "Delta activity on WhatsApp since last check"),
    "whatsapp_summarize_contact": ToolManifestEntry("whatsapp_summarize_contact", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "Summarize messages from specific WhatsApp contact"),
    "whatsapp_conversational": ToolManifestEntry("whatsapp_conversational", Capability.WHATSAPP_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Conversational intent WhatsApp instruction"),
    "whatsapp_health": ToolManifestEntry("whatsapp_health", Capability.WHATSAPP_AUTOMATION, RiskLevel.LOW, OWNER_ONLY, False, "WhatsApp subsystem diagnostic health audit"),

    # Social & Web Platform Automation
    "instagram_dm": ToolManifestEntry("instagram_dm", Capability.BROWSER_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Send Instagram Direct Message"),
    "youtube_upload": ToolManifestEntry("youtube_upload", Capability.BROWSER_AUTOMATION, RiskLevel.HIGH, OWNER_ONLY, False, "Stage and upload video to YouTube with AI metadata"),

    # System Control
    "lock_screen": ToolManifestEntry("lock_screen", Capability.SYSTEM_ADMIN, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Lock Mac display"),
    "sleep": ToolManifestEntry("sleep", Capability.SYSTEM_ADMIN, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Put Mac to sleep"),
    "toggle_gestures": ToolManifestEntry("toggle_gestures", Capability.SYSTEM_ADMIN, RiskLevel.LOW, OWNER_ONLY, False, "Enable or disable optical gestures"),

    # Memory & Personality
    "memory_read": ToolManifestEntry("memory_read", Capability.MEMORY_READ, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Read persistent memory.md"),
    "memory_write": ToolManifestEntry("memory_write", Capability.MEMORY_WRITE, RiskLevel.SENSITIVE, LOCAL_ONLY, False, "Append or update persistent memory.md"),
    "soul_read": ToolManifestEntry("soul_read", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Read soul.md personality"),
    "soul_write": ToolManifestEntry("soul_write", Capability.SECURITY_ADMIN, RiskLevel.CRITICAL, LOCAL_ONLY, True, "Overwrite soul.md personality"),

    # Settings & Security
    "settings_read": ToolManifestEntry("settings_read", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Read settings.json"),
    "settings_write": ToolManifestEntry("settings_write", Capability.SECURITY_ADMIN, RiskLevel.CRITICAL, LOCAL_ONLY, True, "Update settings.json"),

    # File Operations
    "file_ops": ToolManifestEntry("file_ops", Capability.FILE_READ, RiskLevel.MODERATE, OWNER_ONLY, False, "Safe contained file operations"),

    # Extended Dream Capabilities (Weather, News, Finance, Analytics, Comms)
    "weather": ToolManifestEntry("weather", Capability.STATUS, RiskLevel.LOW, ALL_TRUST, False, "Live weather and forecast via wttr.in"),
    "news": ToolManifestEntry("news", Capability.CHAT, RiskLevel.LOW, ALL_TRUST, False, "Live top world, tech, and business headlines"),
    "finance": ToolManifestEntry("finance", Capability.CHAT, RiskLevel.LOW, ALL_TRUST, False, "Real-time stock prices and financial metrics"),
    "system_control": ToolManifestEntry("system_control", Capability.SYSTEM_ADMIN, RiskLevel.MODERATE, OWNER_ONLY, False, "System volume, lock, wifi, clipboard, notifications"),
    "data_analytics": ToolManifestEntry("data_analytics", Capability.FILE_READ, RiskLevel.LOW, OWNER_ONLY, False, "Analyze CSV data with statistical summaries"),
    "gmail": ToolManifestEntry("gmail", Capability.APP_CONTROL, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Gmail send, read, search, and inbox summarization"),
    "telegram": ToolManifestEntry("telegram", Capability.APP_CONTROL, RiskLevel.SENSITIVE, OWNER_ONLY, False, "Telegram Bot messaging and alerts"),
    "calendar": ToolManifestEntry("calendar", Capability.APP_CONTROL, RiskLevel.MODERATE, OWNER_ONLY, False, "macOS Calendar events and agenda"),
    "morning_protocol": ToolManifestEntry("morning_protocol", Capability.SYSTEM_INFO_READ, RiskLevel.LOW, OWNER_ONLY, False, "Automated morning status briefing"),
    "biometrics": ToolManifestEntry("biometrics", Capability.SECURITY_ADMIN, RiskLevel.MODERATE, OWNER_ONLY, False, "Hardware Touch ID biometric authentication"),

    # Dangerous Subprocess / Arbitrary Code Execution (Strictly Blocked by Default)
    "shell_exec": ToolManifestEntry("shell_exec", Capability.SHELL_EXECUTION, RiskLevel.CRITICAL, DISABLED_BY_DEFAULT, True, "Arbitrary shell execution"),
    "code_eval": ToolManifestEntry("code_eval", Capability.CODE_EXECUTION, RiskLevel.CRITICAL, DISABLED_BY_DEFAULT, True, "Arbitrary Python code evaluation"),
}


def get_tool_manifest_entry(tool_name: str) -> Optional[ToolManifestEntry]:
    normalized = tool_name.lower().strip()
    if normalized in TOOL_MANIFEST:
        return TOOL_MANIFEST[normalized]
    if normalized.startswith("desktop_"):
        suffix = normalized[8:]
        if suffix in TOOL_MANIFEST:
            return TOOL_MANIFEST[suffix]
    else:
        prefixed = f"desktop_{normalized}"
        if prefixed in TOOL_MANIFEST:
            return TOOL_MANIFEST[prefixed]
    return None
