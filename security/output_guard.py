"""
J.A.R.V.I.S. Security Kernel — Output Guard & Secret Sanitizer Subsystem
Prevents accidental leakage of credentials, API keys, private filesystem paths,
and internal stack traces before model or tool output is returned to clients.
"""
import re
from typing import Any, Dict, List, Union

SECRET_PATTERNS = [
    # Google API Keys
    (r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]"),
    # Generic API Keys / Bearer tokens
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer [REDACTED_TOKEN]"),
    # OpenAI style keys
    (r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_API_KEY]"),
    # Cloudflare / generic tokens
    (r"\b(?:jarvis-[a-zA-Z0-9]{12,})\b", "[REDACTED_SECRET]"),
    # PEM Private Keys
    (r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
]

# Sensitive internal paths to mask for remote clients
PATH_PATTERNS = [
    (r"/Users/[a-zA-Z0-9_.-]+/\.jarvis_system", "[SYSTEM_CONFIG]"),
    (r"/Users/[a-zA-Z0-9_.-]+", "[HOST_PATH]"),
]


def sanitize_text_output(text: str, is_remote: bool = False) -> str:
    """
    Sanitize text strings for secrets and sensitive host information.
    """
    if not text or not isinstance(text, str):
        return text

    sanitized = text

    # 1. Scrub Secrets
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    # 2. Mask Internal Paths if remote
    if is_remote:
        for pattern, replacement in PATH_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def sanitize_error(error: Union[str, Exception], is_remote: bool = False) -> str:
    """
    Format and scrub errors to prevent stack trace or path exposure to remote callers.
    """
    err_str = str(error)
    if is_remote:
        # Strip tracebacks and file references
        err_str = re.sub(r'File ".*?", line \d+, in .*', '', err_str)
        err_str = re.sub(r'Traceback \(most recent call last\):.*', '', err_str, flags=re.DOTALL)
        err_str = sanitize_text_output(err_str, is_remote=True).strip()
        if not err_str or "Error" not in err_str:
            return "An internal operation error occurred."
    return sanitize_text_output(err_str, is_remote=is_remote)
