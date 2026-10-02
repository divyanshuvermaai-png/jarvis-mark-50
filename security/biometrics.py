"""
J.A.R.V.I.S. macOS Touch ID Biometric Authentication Subsystem
Integrates native Apple Silicon LocalAuthentication (LAContext) for hardware-level
Touch ID verification, credential elevation, and defense-in-depth authorization.
"""
import os
import threading
import logging
from typing import Dict, Any, Optional, Tuple

from security.audit import audit_chain

logger = logging.getLogger("jarvis.security.biometrics")

# Attempt PyObjC LocalAuthentication import
_HAS_LOCAL_AUTH = False
try:
    import LocalAuthentication
    _HAS_LOCAL_AUTH = True
except ImportError:
    LocalAuthentication = None
    logger.warning("LocalAuthentication framework not available; Touch ID hardware disabled.")


class BiometricAuthenticator:
    """
    Evaluates hardware Touch ID biometrics via macOS LocalAuthentication.
    Enforces fail-closed security for elevated J.A.R.V.I.S. operations.
    """

    def __init__(self):
        self._available = _HAS_LOCAL_AUTH

    def is_touch_id_supported(self) -> bool:
        """Check if hardware Touch ID is available and enrolled on this Mac."""
        if not self._available or LocalAuthentication is None:
            return False
        try:
            context = LocalAuthentication.LAContext.alloc().init()
            can_eval, err = context.canEvaluatePolicy_error_(
                LocalAuthentication.LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                None
            )
            return bool(can_eval and err is None)
        except Exception as e:
            logger.debug(f"Touch ID availability check failed: {e}")
            return False

    def is_device_owner_auth_supported(self) -> bool:
        """Check if device owner authentication (Touch ID or passcode) is available."""
        if not self._available or LocalAuthentication is None:
            return False
        try:
            context = LocalAuthentication.LAContext.alloc().init()
            can_eval, err = context.canEvaluatePolicy_error_(
                LocalAuthentication.LAPolicyDeviceOwnerAuthentication,
                None
            )
            return bool(can_eval and err is None)
        except Exception as e:
            logger.debug(f"Device owner auth check failed: {e}")
            return False

    def authenticate(
        self,
        reason: str = "J.A.R.V.I.S. requires Touch ID verification to authorize this action.",
        timeout_sec: float = 30.0,
        allow_passcode_fallback: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Prompt the user for Touch ID biometric verification.
        Returns: (success: bool, error_message: Optional[str])
        """
        # Testing bypass hook for automated test suites
        test_override = os.environ.get("JARVIS_BYPASS_BIOMETRICS_TESTING")
        if test_override is not None:
            val = test_override.strip().lower()
            if val in ("1", "true", "allow", "yes"):
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_SUCCESS",
                    action="biometric_verify",
                    result="SUCCESS",
                    risk_level="MODERATE",
                    details={"mode": "test_override_allow", "reason": reason}
                )
                return True, None
            else:
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_DENIED",
                    action="biometric_verify",
                    result="DENIED",
                    risk_level="MODERATE",
                    details={"mode": "test_override_deny", "reason": reason}
                )
                return False, "Biometric authentication rejected by test configuration."

        if not self._available or LocalAuthentication is None:
            audit_chain.log_event(
                event_type="BIOMETRIC_AUTH_FAILED",
                action="biometric_verify",
                result="UNAVAILABLE",
                risk_level="HIGH",
                details={"error": "LocalAuthentication unavailable"}
            )
            return False, "Hardware biometric authentication is unavailable on this platform."

        try:
            context = LocalAuthentication.LAContext.alloc().init()
            if allow_passcode_fallback:
                policy = LocalAuthentication.LAPolicyDeviceOwnerAuthentication
                context.setLocalizedFallbackTitle_("Use Passcode")
            else:
                policy = LocalAuthentication.LAPolicyDeviceOwnerAuthenticationWithBiometrics
                context.setLocalizedFallbackTitle_("")

            # Pre-check policy capability
            can_eval, err = context.canEvaluatePolicy_error_(policy, None)
            if not can_eval:
                err_msg = str(err.localizedDescription()) if err else "Policy cannot be evaluated."
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_FAILED",
                    action="biometric_verify",
                    result="CANNOT_EVALUATE",
                    risk_level="HIGH",
                    details={"error": err_msg}
                )
                return False, f"Cannot evaluate biometric policy: {err_msg}"

            result: Dict[str, Any] = {"success": False, "error": None}
            event = threading.Event()

            def reply_handler(success: bool, error_obj: Any):
                result["success"] = bool(success)
                if error_obj:
                    try:
                        result["error"] = str(error_obj.localizedDescription())
                    except Exception:
                        result["error"] = str(error_obj)
                event.set()

            context.evaluatePolicy_localizedReason_reply_(policy, reason, reply_handler)

            finished = event.wait(timeout=timeout_sec)
            if not finished:
                try:
                    context.invalidate()
                except Exception:
                    pass
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_TIMEOUT",
                    action="biometric_verify",
                    result="TIMEOUT",
                    risk_level="HIGH",
                    details={"timeout_sec": timeout_sec, "reason": reason}
                )
                return False, f"Biometric verification timed out after {timeout_sec} seconds."

            if result["success"]:
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_SUCCESS",
                    action="biometric_verify",
                    result="SUCCESS",
                    risk_level="LOW",
                    details={"reason": reason}
                )
                return True, None
            else:
                err_desc = result["error"] or "Biometric verification failed or was cancelled."
                audit_chain.log_event(
                    event_type="BIOMETRIC_AUTH_FAILED",
                    action="biometric_verify",
                    result="FAILED",
                    risk_level="MODERATE",
                    details={"error": err_desc, "reason": reason}
                )
                return False, err_desc

        except Exception as e:
            logger.error(f"Biometric authentication exception: {e}")
            audit_chain.log_event(
                event_type="BIOMETRIC_AUTH_ERROR",
                action="biometric_verify",
                result="ERROR",
                risk_level="HIGH",
                details={"exception": str(e)}
            )
            return False, f"Biometric authentication error: {str(e)}"


# Singleton Authenticator
biometric_authenticator = BiometricAuthenticator()

