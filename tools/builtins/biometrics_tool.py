"""
J.A.R.V.I.S. macOS Touch ID Biometric Tool
Exposes hardware-level Apple Silicon Touch ID verification and status to the agent.
"""
import logging
from typing import Dict, Any, Optional

from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier
from security.biometrics import biometric_authenticator, BiometricAuthenticator

logger = logging.getLogger("jarvis.tools.biometrics")


class BiometricTool(BaseTool):
    """
    Tool exposed to J.A.R.V.I.S. agent for hardware Touch ID identity confirmation.
    """
    def __init__(self, authenticator: Optional[BiometricAuthenticator] = None):
        self.authenticator = authenticator or biometric_authenticator

    @property
    def id(self) -> str:
        return "biometrics"

    @property
    def name(self) -> str:
        return "macOS Touch ID Biometrics"

    @property
    def description(self) -> str:
        return "Verify owner identity with native Apple Silicon Touch ID biometric hardware or check biometric sensor status."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["verify", "status"],
                    "description": "'verify' to prompt Touch ID, 'status' to check hardware sensor readiness."
                },
                "reason": {
                    "type": "string",
                    "description": "Custom prompt text displayed during Touch ID authorization."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.SECURITY_ADMIN

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "status").lower().strip()

        if action == "status":
            touch_id = self.authenticator.is_touch_id_supported()
            owner_auth = self.authenticator.is_device_owner_auth_supported()
            status_text = (
                f"Biometric Status:\n"
                f"• Touch ID Hardware: {'Enrolled & Ready' if touch_id else 'Unavailable'}\n"
                f"• Device Owner Authentication: {'Ready' if owner_auth else 'Unavailable'}"
            )
            return ToolResult(
                success=True,
                data=status_text,
                metadata={"touch_id": touch_id, "device_owner_auth": owner_auth}
            )

        elif action == "verify":
            reason = params.get("reason", "J.A.R.V.I.S. requires Touch ID verification to proceed.")
            success, err = self.authenticator.authenticate(reason=reason, timeout_sec=20.0)
            if success:
                return ToolResult(
                    success=True,
                    data="Biometric verification confirmed: Owner identity verified via Touch ID."
                )
            else:
                return ToolResult(
                    success=False,
                    error=err or "Biometric authentication failed."
                )

        else:
            return ToolResult(success=False, error=f"Unknown biometrics action: '{action}'")
