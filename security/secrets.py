"""
J.A.R.V.I.S. Security Kernel — Secrets Management Subsystem
Integrates with macOS Keychain via `/usr/bin/security` CLI with secure filesystem fallback.
Prevents hardcoding secrets in source code and leaks into logs or prompts.
"""
import os
import subprocess
import shutil
from typing import Optional, Tuple

CONFIG_DIR = os.path.expanduser("~/.jarvis_system")
SECRETS_DIR = os.path.join(CONFIG_DIR, "secrets")

KEYCHAIN_SERVICE = "JARVIS_AI_ASSISTANT"


def is_macos_keychain_available() -> bool:
    """Check if macOS security CLI is available."""
    return shutil.which("security") is not None


def get_keychain_secret(account: str, service: str = KEYCHAIN_SERVICE) -> Optional[str]:
    """Retrieve secret from macOS Keychain."""
    if not is_macos_keychain_available():
        return None
    try:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=4
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def set_keychain_secret(account: str, secret_value: str, service: str = KEYCHAIN_SERVICE) -> bool:
    """Store secret in macOS Keychain (-U updates existing)."""
    if not is_macos_keychain_available():
        return False
    try:
        res = subprocess.run(
            ["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", secret_value],
            capture_output=True,
            timeout=4
        )
        return res.returncode == 0
    except Exception:
        return False


def get_secret(key_name: str, fallback_env: Optional[str] = None) -> Optional[str]:
    """
    Get secret with priority:
    1. Environment variable (runtime deployment override)
    2. macOS Keychain
    3. File fallback with restricted 0o600 permissions
    """
    # 1. Environment variable
    if fallback_env and os.environ.get(fallback_env):
        return os.environ[fallback_env].strip()

    # 2. macOS Keychain
    kc_secret = get_keychain_secret(key_name)
    if kc_secret:
        return kc_secret

    # 3. File fallback in ~/.jarvis_system/secrets/
    os.makedirs(SECRETS_DIR, exist_ok=True)
    fallback_file = os.path.join(SECRETS_DIR, f"{key_name}.key")
    if os.path.exists(fallback_file):
        try:
            with open(fallback_file, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass

    return None


def store_secret(key_name: str, secret_value: str) -> bool:
    """Store secret into Keychain, and fallback to 0o600 permission file."""
    stored = False
    if is_macos_keychain_available():
        stored = set_keychain_secret(key_name, secret_value)

    # Always ensure 0o600 file backup
    os.makedirs(SECRETS_DIR, exist_ok=True)
    fallback_file = os.path.join(SECRETS_DIR, f"{key_name}.key")
    try:
        with open(fallback_file, "w", encoding="utf-8") as f:
            f.write(secret_value.strip())
        os.chmod(fallback_file, 0o600)
        stored = True
    except Exception:
        pass

    return stored


def get_secrets_status() -> dict:
    """Return status of secrets subsystem without leaking keys."""
    kc_available = is_macos_keychain_available()
    return {
        "keychain_available": kc_available,
        "storage_mode": "macOS Keychain (Hardware/System Protected)" if kc_available else "Local Filesystem (0o600 Restricted)"
    }
