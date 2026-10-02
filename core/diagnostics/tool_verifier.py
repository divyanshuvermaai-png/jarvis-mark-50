"""
J.A.R.V.I.S. Sandboxed Tool Verifier & Controlled Expansion Subsystem
Statically and dynamically verifies candidate custom tools in an isolated sandbox.
Strictly replaces insecure live exec() with AST verification, isolated subprocess tests,
and fail-closed capability gates.
"""
import os
import json
import ast
import sys

import subprocess
import tempfile

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger("jarvis.diagnostics.verifier")

FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "globals", "locals"}
FORBIDDEN_MODULES = {"ctypes", "pty", "pickle", "shelve", "pip"}

@dataclass
class VerificationResult:
    is_valid: bool
    issues: List[str] = field(default_factory=list)
    tool_id: Optional[str] = None
    stdout: str = ""
    stderr: str = ""


class SandboxedToolVerifier:
    """
    Validates custom tool code through static AST analysis and isolated subprocess execution.
    """
    @classmethod
    def verify(cls, code: str, sample_params: Optional[Dict[str, Any]] = None) -> VerificationResult:
        issues: List[str] = []

        # 1. Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return VerificationResult(is_valid=False, issues=[f"Syntax error: {e}"])

        # 2. Static Security & Architecture Analysis
        found_tool_class = False
        tool_id = None

        for node in ast.walk(tree):
            # Check for forbidden function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    issues.append(f"Forbidden security primitive detected: '{node.func.id}()'")

            # Check for forbidden imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in FORBIDDEN_MODULES:
                            issues.append(f"Forbidden module import: '{alias.name}'")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in FORBIDDEN_MODULES:
                        issues.append(f"Forbidden module import: '{node.module}'")

            # Check for BaseTool class definition
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id == "BaseTool") or (
                        isinstance(base, ast.Attribute) and base.attr == "BaseTool"
                    ):
                        found_tool_class = True

        if not found_tool_class:
            issues.append("Tool code must define a class that inherits from 'BaseTool'.")

        if issues:
            return VerificationResult(is_valid=False, issues=issues)

        # 3. Dynamic Subprocess Execution Sandbox
        # Write code to temporary harness file and run in isolated Python process
        with tempfile.TemporaryDirectory() as tmpdir:
            tool_file = Path(tmpdir) / "candidate_tool.py"
            harness_file = Path(tmpdir) / "test_harness.py"

            tool_file.write_text(code, encoding="utf-8")

            # Harness script imports candidate tool and verifies execution
            harness_code = f"""
import sys
sys.path.insert(0, '{os.path.dirname(os.path.abspath(__file__))}/../..')
sys.path.insert(0, '{tmpdir}')
import json
import inspect
from candidate_tool import *
from tools.base import BaseTool

# Find tool class
tool_classes = [obj for name, obj in inspect.getmembers(sys.modules['candidate_tool']) if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool]
if not tool_classes:
    print("ERROR: No BaseTool subclass found in module", file=sys.stderr)
    sys.exit(1)

tool_instance = tool_classes[0]()
print(f"TOOL_ID:{{tool_instance.id}}")

# Verify properties
assert tool_instance.name, "Tool name is empty"
assert tool_instance.description, "Tool description is empty"
assert isinstance(tool_instance.parameters_schema, dict), "parameters_schema must be a dict"

# Execute test run
params = {json.dumps(sample_params or {})}
res = tool_instance.execute(params)
assert hasattr(res, 'success'), "execute() must return ToolResult"
print("VERIFICATION_SUCCESS")
"""
            harness_file.write_text(harness_code, encoding="utf-8")

            try:
                proc = subprocess.run(
                    [sys.executable, str(harness_file)],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )

                if proc.returncode != 0:
                    return VerificationResult(
                        is_valid=False,
                        issues=[f"Dynamic verification failed with code {proc.returncode}"],
                        stdout=proc.stdout,
                        stderr=proc.stderr
                    )

                # Extract tool_id from output
                for line in proc.stdout.splitlines():
                    if line.startswith("TOOL_ID:"):
                        tool_id = line[8:].strip()

                return VerificationResult(
                    is_valid=True,
                    issues=[],
                    tool_id=tool_id,
                    stdout=proc.stdout,
                    stderr=proc.stderr
                )

            except subprocess.TimeoutExpired:
                return VerificationResult(
                    is_valid=False,
                    issues=["Dynamic verification timed out (> 5.0 seconds). Potential infinite loop or blocking call."]
                )
            except Exception as e:
                return VerificationResult(
                    is_valid=False,
                    issues=[f"Verification error: {e}"]
                )
