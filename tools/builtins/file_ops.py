"""
Contained Filesystem Operations Tool
Provides safe file reading, directory listing, and writing within allowed root boundaries.
"""
from typing import Dict, Any
import os
from pathlib import Path
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskTier
from security.action_validator import validate_file_path

class FileOpsTool(BaseTool):
    @property
    def id(self) -> str:
        return "file_ops"

    @property
    def name(self) -> str:
        return "Safe File Operations"

    @property
    def description(self) -> str:
        return "Read, list, or write files within approved user and project directories."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["operation", "path"],
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "list", "write"],
                    "description": "Operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write (required for operation='write')"
                }
            }
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.FILE_READ

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        op = params.get("operation")
        raw_path = params.get("path")
        content = params.get("content", "")

        is_valid_path, target_path, err = validate_file_path(raw_path)
        if not is_valid_path:
            return ToolResult(success=False, error=f"Access denied: {err or 'Path is outside allowed directories.'}")

        p = Path(target_path)

        if op == "read":
            if not p.exists():
                return ToolResult(success=False, error=f"File not found: {target_path}")
            if p.is_dir():
                return ToolResult(success=False, error=f"Path is a directory, not a file: {target_path}")
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                # Truncate if gigantic
                if len(text) > 50000:
                    text = text[:50000] + "\n... [TRUNCATED DUE TO SIZE]"
                return ToolResult(success=True, data=text)
            except Exception as e:
                return ToolResult(success=False, error=f"Error reading file: {e}")

        elif op == "list":
            if not p.exists():
                return ToolResult(success=False, error=f"Directory not found: {target_path}")
            if not p.is_dir():
                return ToolResult(success=False, error=f"Path is not a directory: {target_path}")
            try:
                entries = []
                for entry in p.iterdir():
                    entries.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size_bytes": entry.stat().st_size if entry.is_file() else 0
                    })
                return ToolResult(success=True, data=entries[:100])
            except Exception as e:
                return ToolResult(success=False, error=f"Error listing directory: {e}")

        elif op == "write":
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return ToolResult(success=True, data=f"Successfully wrote {len(content)} characters to {target_path}")
            except Exception as e:
                return ToolResult(success=False, error=f"Error writing file: {e}")

        return ToolResult(success=False, error=f"Unsupported operation: '{op}'")
