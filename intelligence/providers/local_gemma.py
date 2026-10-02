"""
Local Apple Silicon MLX Gemma 4 E2B Provider
Delivers ultra-fast, 100% private offline inference (~88 tok/s) on Apple M5 GPU/ANE.
"""
from typing import Generator, List, Dict, Any, Optional
from .base import LLMProvider, ProviderMetadata
import gemma_local

class LocalGemmaProvider(LLMProvider):
    def __init__(self, model_id: str = "mlx-community/gemma-4-e2b-it-4bit"):
        self.model_id = model_id
        self._metadata = ProviderMetadata(
            provider_id="local_gemma_4_e2b",
            model_name=self.model_id,
            is_local=True,
            latency_tier="LOW",
            context_window=8192,
            supports_tools=True,
            supports_vision=True,
            cost_per_million_tokens=0.0
        )

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def is_available(self) -> bool:
        return gemma_local.is_gemma_available()

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        image_path = kwargs.get("image_path")
        return gemma_local.infer_gemma(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            image_path=image_path,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        image_path = kwargs.get("image_path")
        for chunk in gemma_local.stream_gemma(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            image_path=image_path,
            max_tokens=max_tokens,
            temperature=temperature
        ):
            yield chunk
