"""
J.A.R.V.I.S. Core Intelligence & Security Foundation
"""
from .profiles import AccessProfile, is_action_permitted, get_profile_permissions
from .subsystems import probe_subsystems, format_remote_banner
from .auth import (
    REMOTE_SECRET,
    OWNER_SECRET,
    verify_remote_secret,
    verify_owner_secret,
    create_session,
    create_owner_session,
    validate_token,
    validate_owner_token,
    revoke_session,
    revoke_owner_session,
    check_login_rate_limit,
    record_login_failure,
    clear_login_failures,
    get_client_ip,
    is_local_request,
    extract_token,
    extract_owner_token,
    require_remote_auth,
    require_owner_auth
)

__all__ = [
    'AccessProfile',
    'is_action_permitted',
    'get_profile_permissions',
    'probe_subsystems',
    'format_remote_banner',
    'REMOTE_SECRET',
    'OWNER_SECRET',
    'verify_remote_secret',
    'verify_owner_secret',
    'create_session',
    'create_owner_session',
    'validate_token',
    'validate_owner_token',
    'revoke_session',
    'revoke_owner_session',
    'check_login_rate_limit',
    'record_login_failure',
    'clear_login_failures',
    'get_client_ip',
    'is_local_request',
    'extract_token',
    'extract_owner_token',
    'require_remote_auth',
    'require_owner_auth'
]
