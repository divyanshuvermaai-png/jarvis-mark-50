"""
OpenRouter Provider Adapter
Multi-model fallback aggregator ensuring provider redundancy.
"""
import os
from typing import Generator, List, Dict, Any, Optional
from .base import LLMProvider, ProviderMetadata

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "google/gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name
        self._client = None
        self._metadata = ProviderMetadata(
            provider_id="openrouter",
            model_name=self.model_name,
            is_local=False,
            latency_tier="MEDIUM",
            context_window=131072,
            supports_tools=True,
            supports_vision=True,
            cost_per_million_tokens=0.20
        )
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key
                )
            except Exception:
                self._client = None

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def is_available(self) -> bool:
        return self._client is not None and bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenRouterProvider is not available (missing OPENROUTER_API_KEY).")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for h in history:
                messages.append(h)
        messages.append({"role": "user", "content": prompt})

        resp = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return resp.choices[0].message.content or ""

    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        if not self.is_available():
            raise RuntimeError("OpenRouterProvider is not available (missing OPENROUTER_API_KEY).")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for h in history:
                messages.append(h)
        messages.append({"role": "user", "content": prompt})

        stream_resp = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )
        for chunk in stream_resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
