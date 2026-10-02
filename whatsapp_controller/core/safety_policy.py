from enum import Enum

class RiskLevel(Enum):
    READ_ONLY = "read_only"
    LOW_RISK = "low_risk"
    HIGH_RISK = "high_risk"
    DESTRUCTIVE = "destructive"

class SafetyPolicyEngine:
    def __init__(self, require_message_confirmation=False):
        self.require_message_confirmation = require_message_confirmation

    def evaluate_operation(self, operation: str, is_ambiguous: bool) -> dict:
        """
        Determines if an operation should proceed, be blocked, or require confirmation.
        """
        if is_ambiguous:
            return {"allow": False, "reason": "Ambiguous contact target."}
            
        risk = self._get_risk_level(operation)
        
        if risk == RiskLevel.READ_ONLY:
            return {"allow": True, "requires_confirmation": False}
        elif risk == RiskLevel.LOW_RISK: # E.g., sending messages
            return {"allow": True, "requires_confirmation": self.require_message_confirmation}
        elif risk == RiskLevel.HIGH_RISK: # E.g., making calls
            return {"allow": True, "requires_confirmation": True}
        elif risk == RiskLevel.DESTRUCTIVE: # E.g., deleting messages
            return {"allow": True, "requires_confirmation": True}
            
        return {"allow": False, "reason": "Unknown operation type."}

    def _get_risk_level(self, operation: str) -> RiskLevel:
        if operation in ["read_chat", "search_chat", "check_state"]:
            return RiskLevel.READ_ONLY
        if operation in ["send_message", "send_media", "reply_message"]:
            return RiskLevel.LOW_RISK
        if operation in ["audio_call", "video_call"]:
            return RiskLevel.HIGH_RISK
        if operation in ["delete_message"]:
            return RiskLevel.DESTRUCTIVE
        return None
