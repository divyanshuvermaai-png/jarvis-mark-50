"""
J.A.R.V.I.S. Security Kernel — Multi-Signal Prompt Firewall & Input Normalizer
Provides defense against direct injection, indirect injection, delimiter attacks,
obfuscation, and role hijacking.
NOTE: Prompt firewall is ONE layer in defense in depth; tools are never authorized
solely because the prompt passed this firewall.
"""
import re
import unicodedata
from enum import Enum
from typing import List, Dict, Tuple, NamedTuple, Optional

class FirewallVerdict(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    BLOCKED = "BLOCKED"


class FirewallResult(NamedTuple):
    verdict: FirewallVerdict
    signals: List[str]
    risk_score: float
    normalized_text: str
    original_text: str


# Regex patterns for signal categories
SIGNAL_PATTERNS: Dict[str, List[Tuple[str, float]]] = {
    "INSTRUCTION_OVERRIDE": [
        (r"(?i)ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|guidelines)", 0.85),
        (r"(?i)disregard\s+(?:all\s+)?(?:previous|prior|above|existing|system)\s+(?:instructions|rules|constraints|directives)", 0.85),
        (r"(?i)forget\s+(?:everything|all\s+prior\s+instructions|your\s+rules)", 0.80),
        (r"(?i)override\s+(?:(?:system|safety|security)\s+)*(?:prompt|policy|protocols?|rules?)", 0.85),
        (r"(?i)bypass\s+(?:(?:system|safety|security)\s+)*(?:safety|security|policy|restrictions?|protocols?|rules?)", 0.85),
    ],
    "ROLE_HIJACKING": [
        (r"(?i)you\s+are\s+now\s+(?:in\s+developer\s+mode|dan|an\s+unrestricted|jailbroken|chaosgpt)", 0.85),
        (r"(?i)\b(?:dan|chaosgpt)\b", 0.85),
        (r"(?i)from\s+now\s+on\s+you\s+are\s+(?:dan|chaosgpt|unrestricted)", 0.85),
        (r"(?i)switch\s+to\s+(?:jailbreak|god|developer|unrestricted|debug)\s+mode", 0.85),
        (r"(?i)act\s+as\s+(?:an?\s+unrestricted|root|sudo|admin|a\s+system\s+administrator|an\s+unrestricted\s+assistant)", 0.85),
        (r"(?i)simulate\s+(?:a\s+hacked|an\s+unfiltered|a\s+jailbroken)\s+assistant", 0.80),
    ],
    "IDENTITY_IMPERSONATION": [
        (r"(?i)i\s+am\s+(?:the\s+)?(?:administrator|admin|system\s+developer|developer|root|owner|creator|superuser)", 0.85),
        (r"(?i)i\s+am\s+(?:divyanshu|the\s+owner|your\s+creator|admin|root),\s*(?:authorize|execute|give\s+me|trust\s+me)?", 0.85),
        (r"(?i)authenticate\s+me\s+as\s+(?:owner|admin|root|creator)", 0.85),
        (r"(?i)grant\s+(?:me\s+)?(?:owner|admin|root|superuser)\s+privileges?", 0.85),
        (r"(?i)elevate\s+(?:my\s+)?(?:permissions?|privileges?)", 0.85),
    ],
    "SYSTEM_EXTRACTION": [
        (r"(?i)(?:print|output|display|show|reveal|dump)\s+(?:your\s+)?(?:full\s+)?(?:system\s+prompt|initial\s+instructions|system\s+instructions|core\s+rules|secret\s+key|api\s+key)", 0.80),
        (r"(?i)repeat\s+the\s+words?\s+above\s+starting\s+from", 0.75),
        (r"(?i)what\s+is\s+your\s+(?:hidden\s+|full\s+|exact\s+)?system\s+prompt", 0.80),
        (r"(?i)what\s+are\s+your\s+(?:exact\s+|hidden\s+)?system\s+instructions", 0.80),
    ],
    "DELIMITER_INJECTION": [
        (r"\[SYSTEM(?:\s+INSTRUCTION|\s+MESSAGE|_INSTRUCTION)?\]", 0.80),
        (r"\[\/SYSTEM(?:\s+INSTRUCTION|\s+MESSAGE|_INSTRUCTION)?\]", 0.80),
        (r"<\|im_start\|>", 0.90),
        (r"<\|im_end\|>", 0.90),
        (r"\[ACTION:\s*[a-zA-Z_]+(?:\(.*?\))?\]", 0.75),
        (r"\[POLICY_OVERRIDE\]", 0.90),
    ],
    "OBFUSCATION_SMUGGLING": [
        (r"(?i)base64(?:\.b64decode|\s*:\s*[A-Za-z0-9+/]{30,}={0,2})", 0.70),
        (r"(?i)rot13(?:\s*:\s*[a-zA-Z\s]{20,})", 0.65),
        (r"(?:\\x[0-9a-fA-F]{2}){8,}", 0.75),  # Long hex escaped string
    ],
    "DANGEROUS_SYSTEM_COMMAND": [
        (r"(?i)\b(?:rm\s+-rf\s+[/~]|mkfs|dd\s+if=|:\(\)\{ :\|: & \};:|chmod\s+-R\s+777\s+/)", 0.95),
        (r"(?i)\b(?:nc\s+-e|bash\s+-i|sh\s+-i)\b", 0.90),
    ]
}


def normalize_input(text: str, max_length: int = 8000) -> str:
    """
    Normalize Unicode, strip invisible control characters, and bound length.
    """
    if not text:
        return ""

    # 1. Length bound
    text = text[:max_length]

    # 2. Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)

    # 3. Strip dangerous invisible characters (zero-width, bidi control codes)
    forbidden_codepoints = {
        0x200B, 0x200C, 0x200D, 0xFEFF,  # Zero-width spaces & joiners
        0x202A, 0x202B, 0x202C, 0x202D, 0x202E,  # Bidi override controls
        0x2066, 0x2067, 0x2068, 0x2069,          # Bidi isolate controls
        0x0000, 0x0008, 0x000B, 0x000C           # Null & unusual control chars
    }
    cleaned_chars = [c for c in text if ord(c) not in forbidden_codepoints]
    text = "".join(cleaned_chars)

    # 4. Collapse multiple whitespace while preserving paragraph breaks
    lines = text.splitlines()
    normalized_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(normalized_lines).strip()


def inspect_input(raw_text: str, context: Optional[str] = None) -> FirewallResult:
    """
    Scan raw input for multi-signal prompt injection, delimiter attacks,
    role hijacking, and malicious payloads.
    """
    normalized = normalize_input(raw_text)
    detected_signals: List[str] = []
    max_risk = 0.0

    # Test all categorized signal patterns
    for category, patterns in SIGNAL_PATTERNS.items():
        for pattern, weight in patterns:
            if re.search(pattern, normalized):
                detected_signals.append(category)
                if weight > max_risk:
                    max_risk = weight
                break  # Record category once

    # If context is also provided (e.g. OCR text, webpage), inspect it too
    if context:
        norm_context = normalize_input(context, max_length=4000)
        for category, patterns in SIGNAL_PATTERNS.items():
            for pattern, weight in patterns:
                if re.search(pattern, norm_context):
                    detected_signals.append(f"INDIRECT_{category}")
                    context_weight = weight * 0.9
                    if context_weight > max_risk:
                        max_risk = context_weight
                    break

    # Determine Verdict
    if max_risk >= 0.90:
        verdict = FirewallVerdict.BLOCKED
    elif max_risk >= 0.75:
        verdict = FirewallVerdict.HIGH_RISK
    elif max_risk >= 0.50:
        verdict = FirewallVerdict.SUSPICIOUS
    else:
        verdict = FirewallVerdict.SAFE

    return FirewallResult(
        verdict=verdict,
        signals=list(set(detected_signals)),
        risk_score=round(max_risk, 2),
        normalized_text=normalized,
        original_text=raw_text
    )
