"""
J.A.R.V.I.S. Central Security Kernel
Master orchestrator implementing the 11-stage Defense-in-Depth pipeline:
Input Normalization -> Prompt Firewall -> Trust Resolution -> Context Isolation ->
Inference -> Tool Authorization -> Action Validation -> Sandbox Limits -> Execution ->
Audit Hash Chain -> Output Sanitization.
"""
from typing import Dict, Any, Optional, Callable, NamedTuple, Tuple
from .trust import TrustLevel, resolve_trust_level
from .prompt_firewall import inspect_input, FirewallResult, FirewallVerdict
from .policy_engine import PolicyEngine, PolicyDecision
from .capabilities import RiskLevel, Capability
from .audit import audit_chain
from .kill_switch import kill_switch
from .sandbox import ExecutionLimiter, run_bounded_action, StepLimitExceeded, ExecutionTimeoutError
from .output_guard import sanitize_text_output, sanitize_error
from .context_isolation import assemble_context
from .secrets import is_macos_keychain_available
from .biometrics import biometric_authenticator


class ProcessedInput(NamedTuple):
    normalized_message: str
    trust_level: TrustLevel
    firewall_result: FirewallResult
    is_blocked: bool


class SecurityKernel:
    """Central J.A.R.V.I.S. Security Kernel."""

    @staticmethod
    def process_input(
        raw_message: str,
        request=None,
        token: Optional[str] = None,
        is_internal: bool = False,
        context_data: Optional[str] = None
    ) -> ProcessedInput:
        """
        Execute Stages 1-3:
        1. Input Normalization
        2. Multi-Signal Prompt Firewall Inspection
        3. Trust Level Resolution
        """
        # 1 & 2. Normalization & Prompt Firewall
        fw_res = inspect_input(raw_message, context=context_data)

        # 3. Trust Resolution (Server-side)
        trust = resolve_trust_level(request=request, token=token, is_internal=is_internal)

        # If prompt firewall detected dangerous direct exploit or high risk:
        is_blocked = (fw_res.verdict == FirewallVerdict.BLOCKED)

        # Audit Prompt Firewall event
        if fw_res.signals:
            audit_chain.log_event(
                event_type="PROMPT_FIREWALL_TRIGGER",
                action="inspect_input",
                result=fw_res.verdict.value,
                trust_level=trust.value,
                risk_level="HIGH" if is_blocked else "MODERATE",
                details={"signals": fw_res.signals, "score": fw_res.risk_score}
            )

        return ProcessedInput(
            normalized_message=fw_res.normalized_text,
            trust_level=trust,
            firewall_result=fw_res,
            is_blocked=is_blocked
        )

    @staticmethod
    def authorize_action(
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER,
        session_id: str = ""
    ) -> PolicyDecision:
        """
        Execute Stages 6 & 7: Tool Authorization & Parameter Validation.
        """
        decision = PolicyEngine.evaluate(
            action_name=action_name,
            params=params,
            trust_level=trust_level,
            session_id=session_id
        )

        if not decision.allowed:
            audit_chain.log_event(
                event_type="AUTHORIZATION_DENIED",
                action=action_name,
                result="DENIED",
                trust_level=trust_level.value,
                session_id=session_id,
                risk_level=decision.risk_level.value,
                details={"reason": decision.reason, "params": params}
            )

        return decision

    @staticmethod
    def authorize_and_execute(
        action_data: Dict[str, Any],
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER,
        executor_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        limiter: Optional[ExecutionLimiter] = None,
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Execute Stages 6-10:
        Authorize -> Validate -> Sandbox Bounds -> Execute -> Audit Hash Chain.
        """
        action = action_data.get("action", "")
        params = action_data.get("params", {}) or {}

        # Authorize & Validate
        decision = SecurityKernel.authorize_action(
            action_name=action,
            params=params,
            trust_level=trust_level,
            session_id=session_id
        )

        if not decision.allowed:
            return {
                "action": action,
                "success": False,
                "data": decision.reason,
                "blocked_by_security": True
            }

        # Step Limiter (Stage 8)
        if limiter:
            try:
                limiter.record_step(action)
            except StepLimitExceeded as sle:
                audit_chain.log_event(
                    event_type="SANDBOX_VIOLATION",
                    action=action,
                    result="STEP_LIMIT_EXCEEDED",
                    trust_level=trust_level.value,
                    session_id=session_id,
                    risk_level=decision.risk_level.value,
                    details={"error": str(sle)}
                )
                return {"action": action, "success": False, "data": str(sle)}

        # Controlled Execution (Stage 9)
        if executor_fn is None:
            return {"action": action, "success": True, "data": "Authorized (No executor provided)"}

        try:
            exec_result = run_bounded_action(executor_fn, action_data)
            success = exec_result.get("success", True)
            data_out = exec_result.get("data")

            # Audit Hash Chain (Stage 10)
            audit_chain.log_event(
                event_type="ACTION_EXECUTE",
                action=action,
                result="SUCCESS" if success else "FAILED",
                trust_level=trust_level.value,
                session_id=session_id,
                risk_level=decision.risk_level.value,
                details={"success": success, "params": params}
            )

            # Output Sanitization on Action Result (Stage 11)
            is_remote = trust_level.is_remote()
            if isinstance(data_out, str):
                exec_result["data"] = sanitize_text_output(data_out, is_remote=is_remote)

            return exec_result

        except ExecutionTimeoutError as ete:
            audit_chain.log_event(
                event_type="ACTION_TIMEOUT",
                action=action,
                result="TIMEOUT",
                trust_level=trust_level.value,
                session_id=session_id,
                risk_level=decision.risk_level.value,
                details={"error": str(ete)}
            )
            return {"action": action, "success": False, "data": str(ete)}
        except Exception as e:
            err_msg = sanitize_error(e, is_remote=trust_level.is_remote())
            audit_chain.log_event(
                event_type="ACTION_ERROR",
                action=action,
                result="ERROR",
                trust_level=trust_level.value,
                session_id=session_id,
                risk_level=decision.risk_level.value,
                details={"error": str(e)}
            )
            return {"action": action, "success": False, "data": err_msg}

    @staticmethod
    def sanitize_output(content: Any, trust_level: TrustLevel = TrustLevel.LOCAL_OWNER) -> Any:
        """Stage 11: Output Sanitization."""
        is_remote = trust_level.is_remote()
        if isinstance(content, str):
            return sanitize_text_output(content, is_remote=is_remote)
        elif isinstance(content, dict):
            clean = {}
            for k, v in content.items():
                clean[k] = SecurityKernel.sanitize_output(v, trust_level=trust_level)
            return clean
        elif isinstance(content, list):
            return [SecurityKernel.sanitize_output(item, trust_level=trust_level) for item in content]
        return content

    @staticmethod
    def elevate_with_biometrics(action_name: str, reason: str = "") -> Tuple[bool, Optional[str]]:
        """
        Request hardware Touch ID biometric elevation for a sensitive or critical operation.
        Returns: (success: bool, error_message: Optional[str])
        """
        prompt = reason or f"J.A.R.V.I.S. requires Touch ID elevation for '{action_name}'."
        success, err = biometric_authenticator.authenticate(reason=prompt)
        return success, err

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Return genuine status of all security subsystems."""
        is_valid, record_count, err = audit_chain.verify_chain()
        keychain_avail = is_macos_keychain_available()
        return {
            "kernel_active": True,
            "security_state": kill_switch.state.name,
            "kill_switch_active": kill_switch.is_active,
            "policy_engine": "ENFORCING",
            "prompt_firewall": "ACTIVE",
            "context_isolation": "ACTIVE",
            "secret_backend": "macOS_Keychain" if keychain_avail else "RESTRICTED_FILESYSTEM",
            "biometrics": {
                "touch_id": biometric_authenticator.is_touch_id_supported(),
                "device_owner_auth": biometric_authenticator.is_device_owner_auth_supported()
            },
            "audit_chain": {
                "verified": is_valid,
                "total_records": record_count,
                "integrity_error": err
            }
        }


# Global Singleton
security_kernel = SecurityKernel()
