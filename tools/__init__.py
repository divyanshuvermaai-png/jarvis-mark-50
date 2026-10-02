"""
J.A.R.V.I.S. Tools Framework
"""
from .base import BaseTool, ToolResult
from .registry import ToolRegistry, tool_registry
from .builtins import SystemInfoTool, FileOpsTool, WebSearchTool

# Auto-register default tools
tool_registry.register(SystemInfoTool())
tool_registry.register(FileOpsTool())
tool_registry.register(WebSearchTool())

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "tool_registry",
    "SystemInfoTool",
    "FileOpsTool",
    "WebSearchTool"
]
