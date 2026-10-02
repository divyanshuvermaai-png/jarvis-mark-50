"""
J.A.R.V.I.S. LLM Provider Abstraction Layer
Establishes uniform contracts across local and cloud AI models.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List, Dict, Any, Optional

@dataclass
class ProviderMetadata:
    provider_id: str
    model_name: str
    is_local: bool
    latency_tier: str  # "LOW", "MEDIUM", "HIGH"
    context_window: int
    supports_tools: bool
    supports_vision: bool
    cost_per_million_tokens: float = 0.0

class LLMProvider(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return provider capability and performance metadata."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is currently initialized and ready."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a complete text completion."""
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream response tokens sequentially."""
        pass

    def health_check(self) -> bool:
        """Probe provider responsiveness with a minimal ping."""
        try:
            if not self.is_available():
                return False
            resp = self.generate("ping", max_tokens=5, temperature=0.1)
            return len(resp.strip()) > 0
        except Exception:
            return False
