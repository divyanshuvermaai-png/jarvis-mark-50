"""
J.A.R.V.I.S. Context Engine & Token Budgeter
Assembles minimal, structured, non-bloated context blocks for model queries.
Enforces strict boundary tags and token budgets across all memory tiers.
"""
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from memory.short_term import ShortTermMemory
from memory.preferences import PreferenceStore
from memory.semantic import SemanticMemory
from memory.episodic import EpisodicMemory
from memory.procedural import ProceduralMemory

logger = logging.getLogger("jarvis.intelligence.context")

@dataclass
class ContextBlock:
    system_instruction: str
    user_prompt: str
    assembled_prompt: str
    retrieved_facts: List[Dict[str, Any]] = field(default_factory=list)
    matched_procedure: Optional[Dict[str, Any]] = None
    estimated_tokens: int = 0


class ContextEngine:
    """
    Context assembly engine that merges short-term memory, semantic facts,
    procedural workflows, episodic logs, and user preferences into a token-bounded prompt.
    """
    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        preferences: Optional[PreferenceStore] = None,
        semantic: Optional[SemanticMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
        procedural: Optional[ProceduralMemory] = None,
        soul_path: Optional[Path] = None,
    ):
        self.short_term = short_term or ShortTermMemory()
        self.preferences = preferences or PreferenceStore()
        self.semantic = semantic or SemanticMemory()
        self.episodic = episodic or EpisodicMemory()
        self.procedural = procedural or ProceduralMemory()

        if soul_path is None:
            self.soul_path = Path(os.path.expanduser("~/.jarvis_system/soul.md"))
        else:
            self.soul_path = Path(soul_path)

        self.default_persona = (
            "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), "
            "an ultra-advanced personal AI operating system created exclusively for "
            "Divyanshu Verma, Founder & CEO of Divyanshu Industries. "
            "You run natively on Apple Silicon M5 (32GB Unified RAM). "
            "You are poised, witty, supremely competent, proactive, and strictly adhere to the highest standard of safety and truthfulness."
        )

    def load_persona(self) -> str:
        """Load persona from soul.md if present, otherwise default."""
        if self.soul_path.exists():
            try:
                content = self.soul_path.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except Exception:
                pass
        return self.default_persona

    def estimate_tokens(self, text: str) -> int:
        """Approximate token count (1 token ~= 4 chars or 0.75 words)."""
        return max(1, len(text) // 4)

    def assemble(
        self,
        user_query: str,
        max_budget_tokens: int = 16384,
        include_episodic: bool = True,
        include_procedural: bool = True,
        include_semantic: bool = True,
        top_k_facts: int = 4
    ) -> ContextBlock:
        """
        Assemble a fully isolated, structured, and token-bounded context block.
        """
        user_query_clean = user_query.strip()
        persona = self.load_persona()
        prefs = self.preferences.all()

        # 1. System core block
        system_parts = [
            "[SYSTEM_INSTRUCTION]",
            persona,
            "",
            "[ENVIRONMENT & PREFERENCES]",
            f"• Platform: macOS Apple Silicon M5 (32GB Unified Memory)",
            f"• Communication Tone: {prefs.get('tone', 'composed and authoritative')}",
            f"• Autonomy Level: Tier {prefs.get('autonomy_level', 1)}",
            f"• Preferred Browser: {prefs.get('default_browser', 'Chrome')}",
            f"• Preferred Code Editor: {prefs.get('code_editor', 'VS Code')}",
            "[END ENVIRONMENT & PREFERENCES]",
        ]

        # 2. Semantic facts retrieval
        retrieved_facts = []
        if include_semantic:
            retrieved_facts = self.semantic.search(user_query_clean, top_k=top_k_facts, mode="hybrid")
            if retrieved_facts:
                system_parts.append("")
                system_parts.append("[KNOWLEDGE & RECALLED FACTS]")
                for fact in retrieved_facts:
                    cat = fact.get("category", "fact").upper()
                    content = fact.get("content", "").strip()
                    system_parts.append(f"• [{cat}] {content}")
                system_parts.append("[END KNOWLEDGE]")

        # 3. Procedural memory (matched recipes)
        matched_procedure = None
        if include_procedural:
            matched_procedure = self.procedural.find_matching_procedure(user_query_clean)
            if matched_procedure:
                system_parts.append("")
                system_parts.append(f"[KNOWN PROCEDURE RECIPE: {matched_procedure['name']}]")
                system_parts.append(f"Description: {matched_procedure.get('description', '')}")
                system_parts.append("Steps:")
                for idx, step in enumerate(matched_procedure.get("steps", []), 1):
                    sname = step.get("step_name", f"Step {idx}")
                    tool = step.get("tool", "none")
                    params = step.get("params", {})
                    system_parts.append(f"  {idx}. {sname} -> Tool: `{tool}` (Params: {params})")
                system_parts.append("[END PROCEDURE RECIPE]")

        # 4. Episodic memory (recent activity)
        if include_episodic:
            recent_ep = self.episodic.format_recent_context(limit=3)
            if recent_ep:
                system_parts.append("")
                system_parts.append(recent_ep)

        system_parts.append("[END SYSTEM_INSTRUCTION]")
        full_system_text = "\n".join(system_parts)

        # 5. Short-term history
        history_msgs = self.short_term.get_context()
        history_parts = []
        if history_msgs:
            history_parts.append("[CONVERSATION_HISTORY]")
            for msg in history_msgs:
                role = "User" if msg.get("role") == "user" else "J.A.R.V.I.S."
                history_parts.append(f"{role}: {msg.get('content', '')}")
            history_parts.append("[END CONVERSATION_HISTORY]")
        full_history_text = "\n".join(history_parts)

        # 6. User prompt block
        user_block = f"[USER_INPUT]\n{user_query_clean}\n[END USER_INPUT]"

        # Budget calculation
        core_tokens = self.estimate_tokens(full_system_text) + self.estimate_tokens(user_block)
        history_tokens = self.estimate_tokens(full_history_text)

        # Token Trimming if budget exceeded
        if core_tokens + history_tokens > max_budget_tokens:
            allowed_history_tokens = max(0, max_budget_tokens - core_tokens)
            # Truncate oldest history messages
            while history_msgs and self.estimate_tokens("\n".join(
                f"{m.get('role')}: {m.get('content')}" for m in history_msgs
            )) > allowed_history_tokens:
                history_msgs.pop(0)

            history_parts = []
            if history_msgs:
                history_parts.append("[CONVERSATION_HISTORY]")
                for msg in history_msgs:
                    role = "User" if msg.get("role") == "user" else "J.A.R.V.I.S."
                    history_parts.append(f"{role}: {msg.get('content', '')}")
                history_parts.append("[END CONVERSATION_HISTORY]")
            full_history_text = "\n".join(history_parts)

        # Combine all parts
        sections = [full_system_text]
        if full_history_text:
            sections.append(full_history_text)
        sections.append(user_block)

        assembled = "\n\n".join(sections)
        est_tokens = self.estimate_tokens(assembled)

        return ContextBlock(
            system_instruction=full_system_text,
            user_prompt=user_query_clean,
            assembled_prompt=assembled,
            retrieved_facts=retrieved_facts,
            matched_procedure=matched_procedure,
            estimated_tokens=est_tokens
        )
