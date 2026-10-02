"""
J.A.R.V.I.S. Validator Agent
Verifies that the requested objective was genuinely achieved before reporting completion.
"""
from typing import Dict, Any, Tuple
from .base import BaseAgent
from core.task_manager import Task, SubTaskStatus, TaskStatus

class ValidatorAgent(BaseAgent):
    def __init__(self, router, tools=None):
        super().__init__(
            name="ValidatorAgent",
            role="Outcome Verification & Truth Assertion",
            router=router,
            tools=tools
        )

    @property
    def system_prompt(self) -> str:
        return """You are the VALIDATOR AGENT of J.A.R.V.I.S.
Synthesize the final answer based strictly on verified subtask outcomes.
Be articulate, concise, and completely honest.
Never hallucinate or pretend an action occurred if the tool failed."""

    def validate_and_synthesize(self, task: Task) -> Tuple[bool, str]:
        """Verify subtask results and assemble final answer."""
        task.mark_status(TaskStatus.VERIFYING)

        # 1. Deterministic status check
        for st in task.subtasks:
            if st.status != SubTaskStatus.COMPLETED:
                error_msg = f"Task verification failed: Step '{st.title}' status is {st.status.value}. Error: {st.error}"
                task.mark_status(TaskStatus.FAILED, error=error_msg)
                return False, error_msg

        # 2. Extract final step or combine findings
        results = [st.result for st in task.subtasks if st.result is not None]
        if not results:
            error_msg = "Task completed without producing any result."
            task.mark_status(TaskStatus.FAILED, error=error_msg)
            return False, error_msg

        # If it's a simple single-step conversational result, return directly
        if len(task.subtasks) == 1 and isinstance(task.subtasks[0].result, str):
            final_text = task.subtasks[0].result
            task.mark_status(TaskStatus.COMPLETED)
            return True, final_text

        # 3. Multi-step synthesis through router
        prompt = (
            f"Original Objective: {task.objective}\n\n"
            f"Verified Subtask Findings:\n"
        )
        for st in task.subtasks:
            prompt += f"- {st.title} ({st.id}): {st.result}\n"

        prompt += "\nPlease formulate a concise, polished, authoritative summary for the user."

        try:
            summary, _ = self.router.execute(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=1024,
                temperature=0.5
            )
            task.mark_status(TaskStatus.COMPLETED)
            return True, summary
        except Exception:
            # Fallback to direct stringification of results
            raw_summary = "\n".join([f"{st.title}: {st.result}" for st in task.subtasks])
            task.mark_status(TaskStatus.COMPLETED)
            return True, raw_summary
