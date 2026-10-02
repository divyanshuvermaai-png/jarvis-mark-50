"""
J.A.R.V.I.S. Remote Security Engine
Consolidated delegation layer to core.auth and core.profiles.
Zero duplication of security, session, or permission logic.
"""
from core.auth import (
    REMOTE_SECRET,
    verify_remote_secret,
    create_session,
    validate_token,
    revoke_session as destroy_session,
    check_login_rate_limit as check_rate_limit,
    record_login_failure as record_failed_attempt,
    clear_login_failures as clear_failed_attempts,
    get_client_ip,
    extract_token,
    is_local_request,
    require_remote_auth,
    audit_logger
)
from core.profiles import AccessProfile, is_action_permitted

def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https:;"
    return response

def is_action_allowed_remotely(action_name, is_authenticated=True):
    """Check if action is allowed over remote link."""
    profile = AccessProfile.REMOTE_AUTH if is_authenticated else AccessProfile.PUBLIC
    return is_action_permitted(profile, action_name)

__all__ = [
    'REMOTE_SECRET',
    'verify_remote_secret',
    'create_session',
    'validate_token',
    'destroy_session',
    'check_rate_limit',
    'record_failed_attempt',
    'clear_failed_attempts',
    'get_client_ip',
    'extract_token',
    'is_local_request',
    'require_remote_auth',
    'apply_security_headers',
    'is_action_allowed_remotely',
    'audit_logger'
]
