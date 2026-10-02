"""
J.A.R.V.I.S. Security Kernel — Action & Parameter Validator
Strict argument validation, path traversal defense, and AppleScript parameter sanitization.
Ensures raw user strings are NEVER passed unsanitized to subcommands, AppleScript, or filesystem.
"""
import os
import re
import tempfile
import urllib.parse
from typing import Dict, Any, Tuple, Optional, List

# Allowed directory roots for file operations
DEFAULT_ALLOWED_ROOTS = [
    os.path.expanduser("~/.jarvis_system"),
    "/tmp",
    "/private/tmp",
    tempfile.gettempdir(),
    os.path.realpath(tempfile.gettempdir()),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
]

SAFE_APP_NAME_RE = re.compile(r"^[a-zA-Z0-9\s\-_\.]{1,64}$")
SAFE_KEY_RE = re.compile(r"^[a-zA-Z0-9\+\s]{1,32}$")


def sanitize_applescript_string(val: str) -> str:
    """
    Safely escape a string for literal embedding inside AppleScript double quotes.
    Prevents quote escapes and nested script injection.
    """
    if not val:
        return ""
    # Strip null bytes and control characters
    val = val.replace("\0", "").replace("\r", "")
    # Escape backslashes first, then double quotes
    escaped = val.replace("\\", "\\\\").replace('"', '\\"')
    # Prevent AppleScript line continuation or comment termination tricks
    escaped = escaped.replace("\n", "\\n")
    return escaped


def validate_file_path(
    path: str,
    allowed_roots: Optional[List[str]] = None,
    allow_create: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate that a file path does not escape allowed directories.
    Blocks null bytes, relative traversal (../), and unauthorized root access.
    Returns: (is_valid, resolved_path, error_reason)
    """
    if not path or not isinstance(path, str):
        return False, None, "File path is empty or invalid type."

    if "\0" in path:
        return False, None, "Null byte injection detected in path."

    # Expand user tilde and resolve absolute real path
    expanded = os.path.expanduser(path.strip())
    resolved = os.path.abspath(os.path.realpath(expanded))

    roots = allowed_roots or DEFAULT_ALLOWED_ROOTS
    is_contained = False
    for root in roots:
        real_root = os.path.realpath(os.path.abspath(os.path.expanduser(root)))
        if resolved == real_root or resolved.startswith(real_root + os.sep):
            is_contained = True
            break

    if not is_contained:
        return False, None, f"Path traversal violation: '{path}' is outside authorized directories."

    if not allow_create and not os.path.exists(resolved):
        return False, None, f"Target file does not exist: '{resolved}'."

    return True, resolved, None


def validate_action_params(action: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Strict validation of action parameters prior to execution.
    Returns: (is_valid, error_reason)
    """
    if not isinstance(params, dict):
        return False, "Parameters must be a dictionary."

    # Validate any file path parameters (path traversal, null byte, directory boundary)
    for path_key in ("save_path", "image_path", "file_path", "path"):
        if path_key in params:
            p_val = params[path_key]
            if p_val is not None:
                is_p_valid, _, p_reason = validate_file_path(str(p_val), allow_create=True)
                if not is_p_valid:
                    return False, p_reason

    # 1. Volume
    if action == "volume":
        lvl = params.get("level")
        if lvl is None or not isinstance(lvl, (int, float)):
            return False, "Volume level must be a numeric value."
        if not (0 <= lvl <= 100):
            return False, f"Volume level {lvl} out of valid range (0-100)."
        return True, None

    # 2. Brightness
    if action == "brightness":
        lvl = params.get("level")
        if lvl is None or not isinstance(lvl, (int, float)):
            return False, "Brightness level must be a numeric value."
        if not (0 <= lvl <= 100):
            return False, f"Brightness level {lvl} out of valid range (0-100)."
        return True, None

    # 3. Window Management
    if action == "desktop_snap":
        pos = params.get("position", "maximize")
        if pos not in ("left", "right", "maximize"):
            return False, f"Invalid window snap position: '{pos}'. Must be left, right, or maximize."
        return True, None

    if action == "desktop_focus":
        app = params.get("app", "")
        if not app or not SAFE_APP_NAME_RE.match(app):
            return False, f"Invalid application name for focus: '{app}'."
        return True, None

    # 4. App Launch / Close
    if action in ("open_app", "close_app"):
        name = params.get("name", "")
        if not name or not SAFE_APP_NAME_RE.match(name):
            return False, f"Invalid application name: '{name}'."
        return True, None

    # 5. Keyboard automation
    if action == "desktop_key":
        key = params.get("key", "")
        if not key or not SAFE_KEY_RE.match(key):
            return False, f"Invalid key sequence: '{key}'."
        return True, None

    if action == "desktop_type":
        text = params.get("text", "")
        if not isinstance(text, str):
            return False, "Typing text must be a string."
        if len(text) > 2000:
            return False, "Typing text exceeds maximum limit of 2000 characters."
        return True, None

    # 6. Mouse automation
    if action in ("click", "double_click", "right_click", "move", "drag", "down", "up"):
        x = params.get("x")
        y = params.get("y")
        if x is not None:
            if not isinstance(x, int) or not (0 <= x <= 7680):
                return False, f"Mouse X coordinate {x} is out of bounds."
        if y is not None:
            if not isinstance(y, int) or not (0 <= y <= 4320):
                return False, f"Mouse Y coordinate {y} is out of bounds."
        return True, None

    # 7. WhatsApp
    if action in ("whatsapp", "whatsapp_call", "whatsapp_read", "whatsapp_media", "whatsapp_summarize_contact"):
        contact = params.get("contact", "")
        if not isinstance(contact, str) or len(contact) > 120:
            return False, "WhatsApp contact name is invalid or exceeds 120 characters."
        if action == "whatsapp":
            msg = params.get("message", "")
            if not isinstance(msg, str) or len(msg) > 4000:
                return False, "WhatsApp message exceeds 4000 characters."
        return True, None

    if action == "whatsapp_conversational":
        text = params.get("text", "")
        if not isinstance(text, str) or len(text) > 4000:
            return False, "Conversational command exceeds 4000 characters."
        return True, None

    # 8. Web Reader / Search
    if action == "read_page":
        url = params.get("url", "")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False, f"Invalid URL for page reading: '{url}'."
        return True, None

    if action == "web_search":
        query = params.get("query", "")
        if not isinstance(query, str) or len(query) > 500:
            return False, "Search query exceeds 500 characters."
        return True, None

    # 9. General Allowed / No Params needed
    if action in ("screenshot", "analyze_screen", "ocr", "lock_screen", "sleep",
                  "desktop_minimize", "desktop_list_windows", "briefing",
                  "whatsapp_activity_summary", "whatsapp_who_messaged", "whatsapp_needs_reply",
                  "whatsapp_delta", "whatsapp_health",
                  "toggle_gestures", "system_info", "status", "general_chat", "biometrics"):
        return True, None

    # Unknown action
    return True, None
