"""
J.A.R.V.I.S. Unified Authentication & Session Engine
Distinguishes between:
1. LOCAL SESSION        (Trusted direct localhost loopback)
2. REMOTE AUTHENTICATED (Requires authenticated session token)
3. PUBLIC UNAUTHENTICATED (Strictly read-only / blocked from privileged Mac automation)

Provides:
- Constant-time secret verification (hmac.compare_digest)
- Sliding-window IP rate limiting
- Cryptographic session tokens with configurable TTL
- Session revocation & expiration
- Structured security audit logging (zero credential leakage)
"""
import os
import time
import hmac
import secrets
import string
import logging
from functools import wraps
from flask import request, jsonify, make_response

CONFIG_DIR = os.path.expanduser("~/.jarvis_system")
REMOTE_SECRET_FILE = os.path.join(CONFIG_DIR, "remote_secret.key")
OWNER_SECRET_FILE = os.path.join(CONFIG_DIR, "owner_secret.key")

# Setup audit logger
audit_logger = logging.getLogger("JARVIS_AUDIT")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[AUDIT %(levelname)s] %(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S"))
    audit_logger.addHandler(ch)

# ── 1. Secret Management ──
def get_or_create_remote_secret() -> str:
    """Retrieve secret from env or ~/.jarvis_system/remote_secret.key, or generate a new one."""
    env_secret = (
        os.environ.get("JARVIS_REMOTE_SECRET", "").strip() or 
        os.environ.get("JARVIS_OWNER_SECRET", "").strip()
    )
    if env_secret:
        return env_secret

    os.makedirs(CONFIG_DIR, exist_ok=True)
    for s_file in (REMOTE_SECRET_FILE, OWNER_SECRET_FILE):
        if os.path.exists(s_file):
            try:
                with open(s_file, "r") as f:
                    saved = f.read().strip()
                    if saved:
                        return saved
            except Exception as e:
                audit_logger.warning(f"Error reading secret file {s_file}: {e}")

    # Generate a strong 18-character passphrase
    alphabet = string.ascii_letters + string.digits
    new_secret = "jarvis-" + "".join(secrets.choice(alphabet) for _ in range(12))
    try:
        with open(REMOTE_SECRET_FILE, "w") as f:
            f.write(new_secret)
        os.chmod(REMOTE_SECRET_FILE, 0o600)  # Owner read/write only
        audit_logger.info(f"Generated new persistent security key at {REMOTE_SECRET_FILE}")
    except Exception as e:
        audit_logger.error(f"Could not persist secret key: {e}")
    return new_secret

REMOTE_SECRET = get_or_create_remote_secret()
OWNER_SECRET = REMOTE_SECRET  # Backward compatibility alias

def verify_remote_secret(candidate: str) -> bool:
    """Verify secret using constant-time comparison to prevent timing attacks."""
    if not candidate or not isinstance(candidate, str):
        return False
    return hmac.compare_digest(candidate.encode('utf-8'), REMOTE_SECRET.encode('utf-8'))

verify_owner_secret = verify_remote_secret  # Backward compatibility alias

# ── 2. Session Management ──
# session_token -> {"ip": str, "created_at": float, "expires_at": float, "user": str}
_sessions = {}
DEFAULT_TTL = int(os.environ.get("JARVIS_SESSION_TTL", str(24 * 3600)))  # 24 hours

def create_session(client_ip: str, ttl_seconds: int = DEFAULT_TTL) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    _sessions[token] = {
        "ip": client_ip,
        "created_at": now,
        "expires_at": now + ttl_seconds,
        "user": "Divyanshu Verma"
    }
    audit_logger.info(f"[AUTH] Established authenticated session for client IP: {client_ip}")
    return token

create_owner_session = create_session  # Backward compatibility alias

def validate_token(token: str) -> bool:
    if not token or token not in _sessions:
        return False
    session = _sessions[token]
    if time.time() > session["expires_at"]:
        del _sessions[token]
        audit_logger.info(f"[AUTH] Expired session token purged")
        return False
    return True

validate_owner_token = validate_token  # Backward compatibility alias

def revoke_session(token: str) -> bool:
    if token in _sessions:
        del _sessions[token]
        audit_logger.info(f"[AUTH] Session revoked successfully")
        return True
    return False

revoke_owner_session = revoke_session  # Backward compatibility alias

# ── 3. Rate Limiter (Brute-force protection) ──
_login_failures = {}
MAX_FAILED_ATTEMPTS = int(os.environ.get("JARVIS_AUTH_RATE_LIMIT", "5"))
LOCKOUT_WINDOW = 300  # 5 minutes

def check_login_rate_limit(client_ip: str):
    now = time.time()
    attempts = _login_failures.get(client_ip, [])
    valid_attempts = [t for t in attempts if now - t < LOCKOUT_WINDOW]
    _login_failures[client_ip] = valid_attempts

    if len(valid_attempts) >= MAX_FAILED_ATTEMPTS:
        remaining = int(LOCKOUT_WINDOW - (now - valid_attempts[0]))
        audit_logger.warning(f"[SECURITY] Rate limit triggered for IP {client_ip}. Lockout active.")
        return False, f"Too many failed authentication attempts. Lockout active for {max(1, remaining)}s."
    return True, None

check_rate_limit = check_login_rate_limit  # Backward compatibility alias

def record_login_failure(client_ip: str):
    now = time.time()
    if client_ip not in _login_failures:
        _login_failures[client_ip] = []
    _login_failures[client_ip].append(now)
    audit_logger.warning(f"[SECURITY] Failed authentication attempt recorded for IP: {client_ip}")

record_failed_attempt = record_login_failure  # Backward compatibility alias

def clear_login_failures(client_ip: str):
    if client_ip in _login_failures:
        del _login_failures[client_ip]

clear_failed_attempts = clear_login_failures  # Backward compatibility alias

# ── 4. Request Origin & Context Resolution ──
def get_client_ip() -> str:
    if request.headers.get("CF-Connecting-IP"):
        return request.headers.get("CF-Connecting-IP")
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def is_local_request() -> bool:
    """Determine if a request is a trusted direct localhost connection vs a remote tunnel."""
    if request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For") or request.headers.get("CF-RAY"):
        return False

    client_ip = request.remote_addr or ""
    return client_ip in ("127.0.0.1", "::1", "localhost")

def extract_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    # Check query param for WebSocket handshakes
    if request.args.get("token"):
        return request.args.get("token").strip()
    # Check Cookies
    token = request.cookies.get("jarvis_session", "") or request.cookies.get("jarvis_owner_session", "")
    return token.strip()

extract_owner_token = extract_token  # Backward compatibility alias

# ── 5. Security Decorator ──
def require_remote_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Local loopback connection: trusted local session
        if is_local_request():
            return f(*args, **kwargs)

        # Remote connection: MUST be authenticated
        token = extract_token()
        client_ip = get_client_ip()

        if not validate_token(token):
            audit_logger.warning(f"[SECURITY] Unauthorized access attempt to {request.path} from {client_ip}")
            return jsonify({
                "success": False,
                "error": "Authentication required. Session missing or expired.",
                "authenticated": False
            }), 401

        return f(*args, **kwargs)
    return decorated

require_owner_auth = require_remote_auth  # Backward compatibility alias
