"""
J.A.R.V.I.S. Security Kernel — Trust & Session Classification Subsystem
Strict Server-Side Trust Resolution. Client-supplied roles/flags are NEVER trusted.
"""
import os
from enum import Enum
from typing import Optional

class TrustLevel(str, Enum):
    REMOTE_PUBLIC = "REMOTE_PUBLIC"             # External unauthenticated Internet caller
    LOCAL_USER = "LOCAL_USER"                   # Unprivileged local user
    LOCAL_OWNER = "LOCAL_OWNER"                 # Workstation owner (Divyanshu Verma) on trusted loopback
    AUTHENTICATED_OWNER = "AUTHENTICATED_OWNER" # Cryptographically validated owner session
    SYSTEM_INTERNAL = "SYSTEM_INTERNAL"         # Internal core processes & sensor telemetry

    def is_owner(self) -> bool:
        return self in (TrustLevel.LOCAL_OWNER, TrustLevel.AUTHENTICATED_OWNER, TrustLevel.SYSTEM_INTERNAL)

    def is_remote(self) -> bool:
        return self == TrustLevel.REMOTE_PUBLIC


def is_loopback_ip(ip: Optional[str]) -> bool:
    if not ip:
        return False
    clean_ip = ip.strip().lower()
    return clean_ip in ("127.0.0.1", "::1", "localhost", "0:0:0:0:0:0:0:1")


def resolve_trust_level(request=None, token: Optional[str] = None, is_internal: bool = False) -> TrustLevel:
    """
    Deterministically resolve trust level based solely on network topology
    and verified cryptographic server sessions.
    
    SECURITY RULE:
    Any client-supplied parameters such as `role`, `user`, `admin`, or `mode`
    in JSON payloads, headers, or query parameters are strictly IGNORED.
    """
    if is_internal:
        return TrustLevel.SYSTEM_INTERNAL

    if request is None:
        return TrustLevel.REMOTE_PUBLIC

    # Check for reverse proxy / tunnel headers (Cloudflare, ngrok, load balancer)
    headers = getattr(request, "headers", {})
    has_tunnel_headers = bool(
        headers.get("CF-Connecting-IP") or 
        headers.get("X-Forwarded-For") or 
        headers.get("CF-RAY") or
        headers.get("X-Real-IP")
    )

    client_ip = getattr(request, "remote_addr", None) or ""

    # If traffic originated through tunnel/proxy, it is external
    if has_tunnel_headers or not is_loopback_ip(client_ip):
        # Check if an authenticated session token was provided
        if not token:
            auth_header = headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            elif hasattr(request, "cookies"):
                token = request.cookies.get("jarvis_session") or request.cookies.get("jarvis_remote_token")

        if token:
            try:
                from core.auth import validate_token
                if validate_token(token):
                    return TrustLevel.AUTHENTICATED_OWNER
            except Exception:
                pass

        return TrustLevel.REMOTE_PUBLIC

    # Direct local loopback request
    return TrustLevel.LOCAL_OWNER
