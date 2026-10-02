"""
J.A.R.V.I.S. Security Kernel — Tamper-Evident Audit Hash Chain
Implements a cryptographically linked SHA-256 audit log.
Provides verify_audit_chain() to detect modifications, deletions, or reordering.
"""
import os
import json
import time
import hashlib
import secrets
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List

GENESIS_HASH = "0" * 64
CONFIG_DIR = os.path.expanduser("~/.jarvis_system")
AUDIT_LOG_FILE = os.path.join(CONFIG_DIR, "audit_chain.jsonl")

_audit_lock = threading.Lock()


def canonical_json(data: Dict[str, Any]) -> str:
    """Format dictionary into deterministic, sorted canonical JSON string."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def scrub_sensitive_data(data: Any) -> Any:
    """Recursively scrub passwords, tokens, API keys from audit logs."""
    sensitive_keys = {"token", "secret", "password", "key", "api_key", "authorization", "cookie"}
    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                scrubbed[k] = "[REDACTED_SECRET]"
            else:
                scrubbed[k] = scrub_sensitive_data(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_sensitive_data(x) for x in data]
    return data


class AuditChain:
    """Tamper-evident append-only SHA-256 audit logger."""

    def __init__(self, log_path: str = AUDIT_LOG_FILE):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._last_hash = self._get_tail_hash()

    def _get_tail_hash(self) -> str:
        """Read the last record's hash, or return GENESIS_HASH if empty."""
        if not os.path.exists(self.log_path):
            return GENESIS_HASH

        last_hash = GENESIS_HASH
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        record = json.loads(line)
                        if "current_hash" in record:
                            last_hash = record["current_hash"]
        except Exception:
            return GENESIS_HASH
        return last_hash

    def log_event(
        self,
        event_type: str,
        action: str,
        result: str,
        trust_level: str = "SYSTEM_INTERNAL",
        session_id: str = "",
        risk_level: str = "LOW",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record a cryptographically hashed event to the audit chain.
        """
        with _audit_lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            event_id = secrets.token_hex(8)
            clean_details = scrub_sensitive_data(details or {})

            payload = {
                "timestamp": now_iso,
                "event_id": event_id,
                "session_id": session_id,
                "trust_level": str(trust_level),
                "event_type": event_type,
                "action": action,
                "result": result,
                "risk_level": str(risk_level),
                "details": clean_details,
                "previous_hash": self._last_hash
            }

            canonical = canonical_json(payload)
            current_hash = hashlib.sha256((canonical + self._last_hash).encode("utf-8")).hexdigest()

            record = dict(payload)
            record["current_hash"] = current_hash

            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            self._last_hash = current_hash
            return record

    def verify_chain(self) -> Tuple[bool, int, Optional[str]]:
        """
        Cryptographically verify the integrity of the audit chain.
        Detects any modified content, deleted records, or reordered lines.
        Returns: (is_valid, record_count, error_reason)
        """
        with _audit_lock:
            if not os.path.exists(self.log_path):
                return True, 0, None

            expected_prev = GENESIS_HASH
            count = 0

            with open(self.log_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                    except Exception as e:
                        return False, count, f"Malformed JSON on line {line_idx}: {e}"

                    recorded_hash = record.get("current_hash")
                    recorded_prev = record.get("previous_hash")

                    # Check link to previous hash
                    if recorded_prev != expected_prev:
                        return False, count, (
                            f"Broken chain link at line {line_idx}: expected prev '{expected_prev}', "
                            f"found '{recorded_prev}'"
                        )

                    # Recompute hash
                    payload = dict(record)
                    payload.pop("current_hash", None)
                    canonical = canonical_json(payload)
                    computed_hash = hashlib.sha256((canonical + recorded_prev).encode("utf-8")).hexdigest()

                    if computed_hash != recorded_hash:
                        return False, count, (
                            f"Tampered record at line {line_idx}: hash mismatch. "
                            f"Computed: {computed_hash}, Recorded: {recorded_hash}"
                        )

                    expected_prev = recorded_hash
                    count += 1

            return True, count, None


# Global Singleton
audit_chain = AuditChain()
