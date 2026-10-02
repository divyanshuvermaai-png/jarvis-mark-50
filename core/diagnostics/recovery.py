"""
J.A.R.V.I.S. Auto-Recovery & Rollback Subsystem
Coordinates graceful degradation, automated provider failovers, and transactional rollback hooks.
"""
import time
import logging
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.diagnostics.recovery")

@dataclass
class RollbackHook:
    id: str
    action_name: str
    rollback_fn: Callable[..., Any]
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)


class RecoveryManager:
    """
    Manages transaction rollbacks, transient failure retries, and provider fallback status.
    """
    def __init__(self, episodic_memory: Optional[Any] = None):
        self.episodic_memory = episodic_memory
        self._rollback_stack: List[RollbackHook] = []
        self._degraded_providers: Dict[str, float] = {}  # provider_name -> degraded_until_ts

    def register_rollback(
        self,
        hook_id: str,
        action_name: str,
        rollback_fn: Callable[..., Any],
        *args,
        **kwargs
    ) -> str:
        """
        Register a rollback action to be executed if a subsequent operation fails.
        """
        hook = RollbackHook(
            id=hook_id,
            action_name=action_name,
            rollback_fn=rollback_fn,
            args=args,
            kwargs=kwargs
        )
        self._rollback_stack.append(hook)
        logger.debug(f"Registered rollback hook '{hook_id}' for '{action_name}'.")
        return hook_id

    def execute_rollbacks(self) -> List[Dict[str, Any]]:
        """
        Execute all registered rollback hooks in reverse (LIFO) order.
        """
        results = []
        while self._rollback_stack:
            hook = self._rollback_stack.pop()
            try:
                hook.rollback_fn(*hook.args, **hook.kwargs)
                results.append({"id": hook.id, "action": hook.action_name, "status": "ROLLED_BACK"})
                logger.info(f"Successfully rolled back action '{hook.action_name}'.")
            except Exception as e:
                results.append({"id": hook.id, "action": hook.action_name, "status": "ROLLBACK_FAILED", "error": str(e)})
                logger.error(f"Failed to execute rollback hook '{hook.id}': {e}")

        if self.episodic_memory and results:
            self.episodic_memory.record_episode(
                summary=f"Executed {len(results)} rollback hook(s) due to task failure",
                event_type="recovery_rollback",
                importance=3,
                details={"hooks": results}
            )

        return results

    def clear_rollbacks(self):
        """Discards rollback stack when task succeeds."""
        self._rollback_stack.clear()

    def mark_provider_degraded(self, provider_name: str, cooldown_seconds: float = 60.0):
        """Temporarily mark a provider as degraded due to rate limit or connection failure."""
        until = time.time() + cooldown_seconds
        self._degraded_providers[provider_name] = until
        logger.warning(f"Provider '{provider_name}' marked degraded for {cooldown_seconds}s.")

        if self.episodic_memory:
            self.episodic_memory.record_episode(
                summary=f"Intelligence provider '{provider_name}' degraded for {cooldown_seconds}s",
                event_type="provider_degraded",
                importance=2
            )

    def is_provider_degraded(self, provider_name: str) -> bool:
        """Check if provider is currently in cooldown."""
        until = self._degraded_providers.get(provider_name, 0.0)
        if time.time() < until:
            return True
        elif provider_name in self._degraded_providers:
            del self._degraded_providers[provider_name]
        return False
