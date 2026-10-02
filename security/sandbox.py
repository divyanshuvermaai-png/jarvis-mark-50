"""
J.A.R.V.I.S. Security Kernel — Sandbox & Resource Limit Subsystem
Enforces loop depth limits, execution timeouts, and AST evaluation restrictions.
"""
import ast
import time
import concurrent.futures
from typing import Any, Callable, Tuple, Optional, Set

MAX_ACTIONS_PER_REQUEST = 5
MAX_EXECUTION_TIMEOUT_SECONDS = 15.0
MAX_OUTPUT_BYTES = 64 * 1024  # 64 KB

FORBIDDEN_AST_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.Delete,
    ast.Global,
    ast.Nonlocal,
    ast.AsyncFunctionDef,
    ast.FunctionDef,
    ast.ClassDef,
    ast.Yield,
    ast.YieldFrom
)

FORBIDDEN_ATTRIBUTES = {
    "__subclasses__", "__globals__", "__builtins__", "__import__",
    "__code__", "__reduce__", "__reduce_ex__", "__mro__",
    "gi_frame", "f_globals", "f_locals", "cr_frame"
}


class StepLimitExceeded(Exception):
    pass


class ExecutionTimeoutError(Exception):
    pass


class ExecutionLimiter:
    """Track and limit multi-step action execution per request."""

    def __init__(self, max_steps: int = MAX_ACTIONS_PER_REQUEST):
        self.max_steps = max_steps
        self.step_count = 0

    def record_step(self, action_name: str) -> None:
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise StepLimitExceeded(
                f"Agentic loop limit exceeded: Attempted {self.step_count} actions (maximum allowed: {self.max_steps})."
            )


def run_bounded_action(func: Callable, *args, timeout_seconds: float = MAX_EXECUTION_TIMEOUT_SECONDS, **kwargs) -> Any:
    """
    Execute an action with a strict execution timeout to prevent hanging or freezing.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise ExecutionTimeoutError(f"Action timed out after {timeout_seconds}s.")


def validate_python_expression(code_str: str) -> Tuple[bool, Optional[str]]:
    """
    Statically validate a Python snippet using AST to prevent dangerous dunders,
    imports, or system calls.
    NOTE: AST validation is defense-in-depth, not a substitute for disabling arbitrary code execution.
    """
    try:
        tree = ast.parse(code_str, mode="eval")
    except SyntaxError as e:
        return False, f"Syntax error in expression: {e}"

    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_AST_NODES):
            return False, f"Forbidden AST node: {type(node).__name__}"

        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
            return False, f"Forbidden attribute access: {node.attr}"

        if isinstance(node, ast.Name):
            if node.id in ("eval", "exec", "compile", "open", "input", "__import__", "breakpoint"):
                return False, f"Forbidden built-in identifier: {node.id}"

    return True, None
