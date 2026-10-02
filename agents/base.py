"""
J.A.R.V.I.S. Base Agent
Foundation for specialized agents with access to the ModelRouter, ToolRegistry, and Security policy.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from intelligence.router import ModelRouter
from tools.registry import ToolRegistry, tool_registry

class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        role: str,
        router: ModelRouter,
        tools: Optional[ToolRegistry] = None
    ):
        self.name = name
        self.role = role
        self.router = router
        self.tools = tools or tool_registry

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The specialized system prompt defining the agent's persona and constraints."""
        pass
