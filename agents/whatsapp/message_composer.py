"""
J.A.R.V.I.S. WhatsApp Agent - Message Composer
Translates conversational user intents ('Say hello to Rahul', 'Wish Ankit happy birthday')
into polished, natural messages and detects sensitive/consequential content.
"""
import re
from typing import Tuple, Optional


class MessageComposer:
    """
    Composes natural messages from spoken/text user commands and audits them
    against safety policies for consequential or sensitive material.
    """

    # Patterns for sensitive/consequential message content requiring explicit user confirmation
    SENSITIVE_PATTERNS = [
        (r'\b(?:\d{4}[ -]?){3}\d{4}\b', "Credit or debit card number detected"),
        (r'\b(?:cvv|cvc)\s*[:=]?\s*\d{3,4}\b', "Card CVV/security code detected"),
        (r'\b(?:otp|one[- ]time password)\b.*?\b\d{4,8}\b', "OTP verification code detected"),
        (r'\b(?:password|passwd|pwd)\s*[:=]?\s*\S+\b', "Account password detected"),
        (r'\b(?:bank account|account number|acc no)\s*[:=]?\s*\d{6,18}\b', "Bank account details detected"),
        (r'\b(?:api[_-]?key|secret[_-]?token|private[_-]?key)\b', "API key or secret token detected"),
        (r'\b(?:i accept the terms|i legally agree|i hereby sign)\b', "Legal commitment clause detected")
    ]

    @staticmethod
    def compose_from_intent(contact_name: str, raw_command: str) -> Tuple[str, bool]:
        """
        Extracts or generates natural message text from conversational intent.
        Returns: (composed_message, is_generated_greeting)
        """
        cmd = raw_command.strip()
        contact = contact_name.strip().title()

        # 1. "Say hello / hi / hey to X"
        m = re.search(r'say\s+(?:hello|hi|hey|greetings)(?:\s+to\s+.*)?$', cmd, re.IGNORECASE)
        if m:
            return f"Hello, {contact}!", True

        # 2. "Say good morning / afternoon / evening / night to X"
        m = re.search(r'say\s+(good\s+(?:morning|afternoon|evening|night))(?:\s+to\s+.*)?$', cmd, re.IGNORECASE)
        if m:
            greeting = m.group(1).capitalize()
            return f"{greeting}, {contact}!", True

        # 3. "Wish X happy birthday / happy anniversary / all the best"
        m = re.search(r'wish\s+(?:.*?\s+)?happy\s+birthday', cmd, re.IGNORECASE)
        if m:
            return f"Happy Birthday, {contact}! Wishing you a wonderful year ahead! 🎉", True

        m = re.search(r'wish\s+(?:.*?\s+)?happy\s+anniversary', cmd, re.IGNORECASE)
        if m:
            return f"Happy Anniversary, {contact}! Wishing you both joy and love! 🥂", True

        # 4. "Tell X congratulations / congrats"
        m = re.search(r'tell\s+(?:.*?\s+)?(?:congratulations|congrats)', cmd, re.IGNORECASE)
        if m:
            return f"Congratulations, {contact}! Thrilled to hear the great news! 🎊", True

        # 5. "Tell X that / saying / with / <message>"
        m = re.search(r'(?:tell|message|inform)\s+[a-zA-Z0-9_\-\+]+\s+(?:that\s+|saying\s+|with\s+)?(.+)$', cmd, re.IGNORECASE)
        if m:
            body = m.group(1).strip()
            # Clean quotes if user wrapped text in quotes
            body = body.strip('"\'')
            return body, False

        # 6. "Send X: <message>"
        m = re.search(r'send\s+.*?\s*:\s*(.+)$', cmd, re.IGNORECASE)
        if m:
            body = m.group(1).strip().strip('"\'')
            return body, False

        # Fallback to command itself
        return cmd, False

    @classmethod
    def audit_message(cls, message: str) -> Tuple[bool, Optional[str]]:
        """
        Audits message for high-risk, sensitive, or consequential statements.
        Returns: (requires_confirmation: bool, reason: Optional[str])
        """
        msg_lower = message.lower()

        for pattern, reason in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, msg_lower):
                return True, reason

        return False, None
