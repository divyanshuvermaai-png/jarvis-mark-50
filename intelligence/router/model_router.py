"""
J.A.R.V.I.S. Multi-Factor Intelligence Model Router
Intelligently selects the optimal model (Local Gemma MLX vs Gemini vs Groq vs OpenRouter)
based on task complexity, privacy tier, latency constraints, system RAM, and provider health.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import psutil
import logging

from intelligence.providers.base import LLMProvider
from intelligence.providers.local_gemma import LocalGemmaProvider
from intelligence.providers.gemini_provider import GeminiProvider
from intelligence.providers.groq_provider import GroqProvider
from intelligence.providers.openrouter_provider import OpenRouterProvider
from core.events import event_bus, Event, EventType

logger = logging.getLogger("jarvis.router")

class TaskComplexity(str, Enum):
    CONVERSATIONAL = "CONVERSATIONAL"
    LIGHTWEIGHT = "LIGHTWEIGHT"
    TOOL_ORCHESTRATION = "TOOL_ORCHESTRATION"
    CODING = "CODING"
    RESEARCH = "RESEARCH"
    COMPLEX_REASONING = "COMPLEX_REASONING"
    MULTIMODAL = "MULTIMODAL"

class PrivacyTier(str, Enum):
    STRICT_LOCAL = "STRICT_LOCAL"      # Must never leave the MacBook
    BALANCED = "BALANCED"              # Cloud permitted if required for task
    CLOUD_PREFERRED = "CLOUD_PREFERRED" # Highest intelligence priority

@dataclass
class RoutingPlan:
    primary_provider_id: str
    fallback_chain: List[str]
    complexity: TaskComplexity
    privacy: PrivacyTier
    reason: str

class ModelRouter:
    def __init__(self, config=None):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        # 1. Local MLX Gemma 4 E2B
        try:
            self.providers["local_gemma_4_e2b"] = LocalGemmaProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize LocalGemmaProvider: {e}")

        # 2. Google Gemini
        try:
            self.providers["google_gemini"] = GeminiProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiProvider: {e}")

        # 3. Groq Cloud
        try:
            self.providers["groq_cloud"] = GroqProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize GroqProvider: {e}")

        # 4. OpenRouter
        try:
            self.providers["openrouter"] = OpenRouterProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenRouterProvider: {e}")

    def classify_task(self, prompt: str, has_image: bool = False, tool_count: int = 0) -> TaskComplexity:
        """Classify task requirements from prompt characteristics and context."""
        if has_image:
            return TaskComplexity.MULTIMODAL
        
        prompt_lower = prompt.lower()
        
        # Coding markers
        code_markers = ["def ", "class ", "function", "refactor", "debug", "python", "javascript", "swift", "bug in", "traceback"]
        if any(m in prompt_lower for m in code_markers):
            return TaskComplexity.CODING

        # Deep research markers
        research_markers = ["research", "investigate", "synthesize", "compare and contrast", "in-depth analysis", "market study"]
        if any(m in prompt_lower for m in research_markers):
            return TaskComplexity.RESEARCH

        # Complex reasoning / planning
        reasoning_markers = ["plan a", "break down", "step by step strategy", "architect", "solve this puzzle", "complex"]
        if any(m in prompt_lower for m in reasoning_markers):
            return TaskComplexity.COMPLEX_REASONING

        # Tool heavy
        if tool_count > 0 or any(m in prompt_lower for m in ["search the web", "look up", "find file", "schedule", "send email"]):
            return TaskComplexity.TOOL_ORCHESTRATION

        # Short/routine conversation
        if len(prompt.split()) < 30 and not any(k in prompt_lower for k in ["why", "how does", "explain in detail"]):
            return TaskComplexity.CONVERSATIONAL

        return TaskComplexity.LIGHTWEIGHT

    def route(
        self,
        prompt: str,
        privacy: PrivacyTier = PrivacyTier.BALANCED,
        has_image: bool = False,
        tool_count: int = 0
    ) -> RoutingPlan:
        """Determine primary provider and fallback order based on multi-factor heuristics."""
        complexity = self.classify_task(prompt, has_image=has_image, tool_count=tool_count)
        
        # Check system memory pressure
        mem = psutil.virtual_memory()
        high_ram_pressure = mem.percent > 85.0

        primary = "local_gemma_4_e2b"
        fallbacks = []
        reason = ""

        # Rule 1: Strict local privacy constraint
        if privacy == PrivacyTier.STRICT_LOCAL:
            primary = "local_gemma_4_e2b"
            fallbacks = []
            reason = "Strict local privacy policy enforced: Zero cloud egress allowed."
            return RoutingPlan(primary, fallbacks, complexity, privacy, reason)

        # Rule 2: Multimodal workloads (Images / Screen)
        if complexity == TaskComplexity.MULTIMODAL:
            if self.providers.get("google_gemini") and self.providers["google_gemini"].is_available():
                primary = "google_gemini"
                fallbacks = ["local_gemma_4_e2b", "openrouter"]
                reason = "Multimodal workload routed to Google Gemini 2.5."
            else:
                primary = "local_gemma_4_e2b"
                fallbacks = ["openrouter"]
                reason = "Gemini cloud unavailable; fallback to Local Gemma VLM."
            return RoutingPlan(primary, fallbacks, complexity, privacy, reason)

        # Rule 3: Complex Reasoning & In-Depth Research
        if complexity in (TaskComplexity.COMPLEX_REASONING, TaskComplexity.RESEARCH, TaskComplexity.CODING):
            if self.providers.get("google_gemini") and self.providers["google_gemini"].is_available():
                primary = "google_gemini"
                fallbacks = ["groq_cloud", "local_gemma_4_e2b", "openrouter"]
                reason = f"High-complexity {complexity.value} routed to Gemini 2.5 for deep reasoning."
            elif self.providers.get("groq_cloud") and self.providers["groq_cloud"].is_available():
                primary = "groq_cloud"
                fallbacks = ["local_gemma_4_e2b", "openrouter"]
                reason = "Gemini unavailable; routed to Groq Llama-3.3-70B."
            else:
                primary = "local_gemma_4_e2b"
                fallbacks = ["openrouter"]
                reason = "Cloud providers unconfigured; routed to resident Local Gemma 4."
            return RoutingPlan(primary, fallbacks, complexity, privacy, reason)

        # Rule 4: Ultra-low latency tool orchestration
        if complexity == TaskComplexity.TOOL_ORCHESTRATION:
            if self.providers.get("groq_cloud") and self.providers["groq_cloud"].is_available():
                primary = "groq_cloud"
                fallbacks = ["google_gemini", "local_gemma_4_e2b"]
                reason = "Tool orchestration routed to Groq for sub-second planning."
            elif self.providers.get("local_gemma_4_e2b") and self.providers["local_gemma_4_e2b"].is_available():
                primary = "local_gemma_4_e2b"
                fallbacks = ["google_gemini", "openrouter"]
                reason = "Local Gemma 4 selected for low-latency tool dispatch."
            else:
                primary = "google_gemini"
                fallbacks = ["openrouter"]
                reason = "Routed to Gemini cloud."
            return RoutingPlan(primary, fallbacks, complexity, privacy, reason)

        # Rule 5: Conversational / Lightweight (Default to Local Gemma 4 on Apple M5)
        if not high_ram_pressure and self.providers.get("local_gemma_4_e2b") and self.providers["local_gemma_4_e2b"].is_available():
            primary = "local_gemma_4_e2b"
            fallbacks = ["groq_cloud", "google_gemini", "openrouter"]
            reason = "Standard conversational interaction routed to local MLX GPU (private & fast)."
        else:
            primary = "groq_cloud" if (self.providers.get("groq_cloud") and self.providers["groq_cloud"].is_available()) else "google_gemini"
            fallbacks = ["local_gemma_4_e2b", "openrouter"]
            reason = "High memory pressure or local offline; routed to fast cloud."

        return RoutingPlan(primary, fallbacks, complexity, privacy, reason)

    def execute(
        self,
        prompt: str,
        system_prompt: str = "",
        history: Optional[List[Dict[str, Any]]] = None,
        privacy: PrivacyTier = PrivacyTier.BALANCED,
        has_image: bool = False,
        tool_count: int = 0,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Tuple[str, str]:
        """Execute generation with automatic primary -> secondary -> fallback failover."""
        plan = self.route(prompt, privacy=privacy, has_image=has_image, tool_count=tool_count)
        
        chain = [plan.primary_provider_id] + [f for f in plan.fallback_chain if f != plan.primary_provider_id]
        last_error = None

        for provider_id in chain:
            provider = self.providers.get(provider_id)
            if not provider or not provider.is_available():
                continue

            try:
                event_bus.publish(Event(
                    event_type=EventType.MODEL_ROUTED,
                    source="ModelRouter",
                    payload={"provider": provider_id, "complexity": plan.complexity.value, "reason": plan.reason}
                ))
                
                result = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    history=history,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                if result:
                    return result, provider_id
            except Exception as e:
                logger.warning(f"Provider {provider_id} failed: {e}. Falling back...")
                last_error = e

        raise RuntimeError(f"All routed model providers failed. Last error: {last_error}")
