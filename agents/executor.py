"""
J.A.R.V.I.S. Executor Agent
Dispatches tools and executes subtask steps under strict deterministic security policy.
"""
import time
from typing import Dict, Any, Optional
from .base import BaseAgent
from core.task_manager import Task, SubTask, SubTaskStatus, TaskStatus, TaskGraph
from security import TrustLevel

class ExecutorAgent(BaseAgent):
    def __init__(self, router, tools=None):
        super().__init__(
            name="ExecutorAgent",
            role="Autonomous Task Execution & Tool Invocation",
            router=router,
            tools=tools
        )

    @property
    def system_prompt(self) -> str:
        return """You are the EXECUTOR AGENT of J.A.R.V.I.S.
You execute action steps, formulate answers, and analyze tool findings.
Maintain an intelligent, precise, and authoritative tone.
Always refer to yourself as J.A.R.V.I.S. and creator Divyanshu Verma when applicable."""

    def execute_subtask(
        self,
        subtask: SubTask,
        context: Dict[str, Any],
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER
    ) -> bool:
        """Execute a single SubTask."""
        subtask.status = SubTaskStatus.RUNNING
        t0 = time.time()

        try:
            # Case 1: Tool execution
            if subtask.tool_hint:
                tool = self.tools.get_tool(subtask.tool_hint)
                if not tool:
                    subtask.status = SubTaskStatus.FAILED
                    subtask.error = f"Tool '{subtask.tool_hint}' not registered."
                    return False

                result = self.tools.execute_tool(
                    tool_id=subtask.tool_hint,
                    params=subtask.tool_params,
                    trust_level=trust_level
                )

                if result.success:
                    subtask.status = SubTaskStatus.COMPLETED
                    subtask.result = result.data
                    return True
                else:
                    subtask.status = SubTaskStatus.FAILED
                    subtask.error = result.error
                    return False

            # Case 2: Direct model reasoning / synthesis
            else:
                prompt = (
                    f"Objective: {subtask.description}\n"
                    f"Prior Context: {json_safe(context)}"
                )
                response, provider_used = self.router.execute(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=1024,
                    temperature=0.7
                )
                subtask.status = SubTaskStatus.COMPLETED
                subtask.result = response
                return True

        except Exception as e:
            subtask.status = SubTaskStatus.FAILED
            subtask.error = str(e)
            return False

        finally:
            subtask.execution_time_ms = round((time.time() - t0) * 1000, 2)

    def execute_graph(
        self,
        graph: TaskGraph,
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER,
        max_iterations: int = 15
    ) -> bool:
        """Iteratively execute ready nodes in the TaskGraph until complete or failed."""
        graph.task.mark_status(TaskStatus.EXECUTING)
        context = {}

        for _ in range(max_iterations):
            ready_steps = graph.get_ready_subtasks()
            if not ready_steps:
                break

            for step in ready_steps:
                success = self.execute_subtask(step, context, trust_level=trust_level)
                if success:
                    context[step.id] = step.result
                else:
                    graph.task.mark_status(TaskStatus.FAILED, error=step.error)
                    return False

            if graph.is_complete():
                return True

        if graph.is_complete():
            return True
        else:
            graph.task.mark_status(TaskStatus.FAILED, error="Execution loop limit reached before task completion.")
            return False

def json_safe(obj: Any) -> str:
    try:
        import json
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)
