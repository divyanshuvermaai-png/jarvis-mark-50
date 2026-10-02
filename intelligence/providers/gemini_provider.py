"""
Google Gemini Cloud Provider Adapter
Supports Gemini 2.5 Flash / Pro for complex reasoning, large context, and multimodal tasks.
"""
import os
from typing import Generator, List, Dict, Any, Optional
from .base import LLMProvider, ProviderMetadata

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self._client = None
        self._metadata = ProviderMetadata(
            provider_id="google_gemini",
            model_name=self.model_name,
            is_local=False,
            latency_tier="MEDIUM",
            context_window=1048576,
            supports_tools=True,
            supports_vision=True,
            cost_per_million_tokens=0.15
        )
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
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
            raise RuntimeError("GeminiProvider is not available (missing GEMINI_API_KEY).")
        
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return response.text or ""

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
            raise RuntimeError("GeminiProvider is not available (missing GEMINI_API_KEY).")
        
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        stream_resp = self._client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        for chunk in stream_resp:
            if chunk.text:
                yield chunk.text
