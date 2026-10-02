"""
J.A.R.V.I.S. Short-Term Working Memory
Maintains the active conversation history with token/length bounding and role classification.
"""
from typing import List, Dict, Any
from collections import deque

class ShortTermMemory:
    def __init__(self, max_turns: int = 12):
        self.max_turns = max_turns
        self._history: deque = deque(maxlen=max_turns * 2)

    def add_user_message(self, content: str):
        self._history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self._history.append({"role": "assistant", "content": content})

    def get_context(self) -> List[Dict[str, str]]:
        return list(self._history)

    def clear(self):
        self._history.clear()

    def format_history_string(self) -> str:
        lines = []
        for msg in self._history:
            role = "User" if msg["role"] == "user" else "J.A.R.V.I.S."
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)
