"""
J.A.R.V.I.S. Centralized Security Subsystem (Defense in Depth)
"""
from .trust import TrustLevel, resolve_trust_level
from .capabilities import Capability, RiskLevel, TOOL_MANIFEST, get_tool_manifest_entry
from .policy_engine import PolicyEngine, PolicyDecision
from .prompt_firewall import inspect_input, normalize_input, FirewallVerdict, FirewallResult
from .kill_switch import kill_switch, SecurityState, KillSwitchManager
from .audit import audit_chain, AuditChain
from .secrets import get_secret, store_secret, get_secrets_status
from .sandbox import ExecutionLimiter, run_bounded_action, validate_python_expression
from .output_guard import sanitize_text_output, sanitize_error
from .action_validator import validate_file_path, validate_action_params, sanitize_applescript_string
from .context_isolation import assemble_context, build_external_data_block, build_memory_block
from .security_kernel import security_kernel, SecurityKernel
from .biometrics import biometric_authenticator, BiometricAuthenticator

__all__ = [
    "TrustLevel",
    "resolve_trust_level",
    "Capability",
    "RiskLevel",
    "TOOL_MANIFEST",
    "get_tool_manifest_entry",
    "PolicyEngine",
    "PolicyDecision",
    "inspect_input",
    "normalize_input",
    "FirewallVerdict",
    "FirewallResult",
    "kill_switch",
    "SecurityState",
    "KillSwitchManager",
    "audit_chain",
    "AuditChain",
    "get_secret",
    "store_secret",
    "get_secrets_status",
    "ExecutionLimiter",
    "run_bounded_action",
    "validate_python_expression",
    "sanitize_text_output",
    "sanitize_error",
    "validate_file_path",
    "validate_action_params",
    "sanitize_applescript_string",
    "assemble_context",
    "build_external_data_block",
    "build_memory_block",
    "security_kernel",
    "SecurityKernel",
    "biometric_authenticator",
    "BiometricAuthenticator",
]
