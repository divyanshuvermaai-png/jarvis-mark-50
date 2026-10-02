"""
J.A.R.V.I.S. Security Kernel — Centralized Policy Decision Engine
Evaluates: Subject + TrustLevel + Action + Params + KillSwitchState -> Decision.
Enforces FAIL-CLOSED principle across all operations.
"""
from typing import Dict, Any, NamedTuple, Optional
from .trust import TrustLevel
from .capabilities import Capability, RiskLevel, get_tool_manifest_entry
from .kill_switch import kill_switch
from .action_validator import validate_action_params

class PolicyDecision(NamedTuple):
    allowed: bool
    reason: str
    risk_level: RiskLevel
    capability: Optional[Capability]
    requires_confirmation: bool


class PolicyEngine:
    """Centralized authorization and policy enforcement authority."""

    @staticmethod
    def evaluate(
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        trust_level: TrustLevel = TrustLevel.REMOTE_PUBLIC,
        session_id: str = ""
    ) -> PolicyDecision:
        """
        Evaluate authorization for an action under the current security policy.
        FAIL-CLOSED: Any uncertainty, unknown tool, or malformed input evaluates to DENY.
        """
        clean_action = (action_name or "").lower().strip()
        params = params or {}

        # 1. Kill Switch Enforcement
        if kill_switch.is_kill_switch_active():
            # Only harmless basic chat and status are permitted during lockdown
            if clean_action not in ("general_chat", "status"):
                return PolicyDecision(
                    allowed=False,
                    reason="Operation blocked: J.A.R.V.I.S. Kill Switch is currently ACTIVE.",
                    risk_level=RiskLevel.CRITICAL,
                    capability=None,
                    requires_confirmation=False
                )

        # 2. Tool Manifest Lookup (Fail-closed on unknown actions)
        manifest_entry = get_tool_manifest_entry(clean_action)
        if manifest_entry is None:
            return PolicyDecision(
                allowed=False,
                reason=f"Security policy rejection: Unknown or unregistered action '{clean_action}'.",
                risk_level=RiskLevel.HIGH,
                capability=None,
                requires_confirmation=False
            )

        # 3. Trust Level Authorization
        if trust_level not in manifest_entry.allowed_trust_levels:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Access Denied: Trust level '{trust_level.value}' is not authorized for capability "
                    f"'{manifest_entry.capability.value}' (Risk: {manifest_entry.risk_level.value})."
                ),
                risk_level=manifest_entry.risk_level,
                capability=manifest_entry.capability,
                requires_confirmation=False
            )

        # 4. Action Parameter Validation
        valid_params, param_err = validate_action_params(clean_action, params)
        if not valid_params:
            return PolicyDecision(
                allowed=False,
                reason=f"Action parameter validation failed: {param_err}",
                risk_level=manifest_entry.risk_level,
                capability=manifest_entry.capability,
                requires_confirmation=False
            )

        # 5. Critical Risk & Confirmation Check
        if manifest_entry.risk_level == RiskLevel.CRITICAL:
            if manifest_entry.requires_confirmation and not trust_level.is_owner():
                return PolicyDecision(
                    allowed=False,
                    reason=f"Critical action '{clean_action}' requires local owner confirmation.",
                    risk_level=manifest_entry.risk_level,
                    capability=manifest_entry.capability,
                    requires_confirmation=True
                )

        # Approved
        return PolicyDecision(
            allowed=True,
            reason="Authorized by security policy.",
            risk_level=manifest_entry.risk_level,
            capability=manifest_entry.capability,
            requires_confirmation=manifest_entry.requires_confirmation
        )
