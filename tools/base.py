"""
J.A.R.V.I.S. Base Tool Framework
Standardized contract, parameter schema, risk tiers, and execution boundaries for tools.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from security.capabilities import Capability, RiskTier

@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }

class BaseTool(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique tool identifier (e.g. 'system_info', 'read_file')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description for LLM tool selection."""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON Schema defining the accepted input parameters."""
        pass

    @property
    def required_capability(self) -> Capability:
        return Capability.SYSTEM_INFO_READ

    @property
    def risk_tier(self) -> RiskTier:
        return RiskTier.LOW

    @property
    def timeout_seconds(self) -> int:
        return 30

    @property
    def is_reversible(self) -> bool:
        return False

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the tool logic with validated parameters."""
        pass
