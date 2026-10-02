"""
J.A.R.V.I.S. Master Agent Orchestrator
Coordinates Planner, Executor, and Validator agents into an autonomous, verified pipeline.
"""
import time
from typing import Dict, Any, Tuple, Optional
from core.task_manager import Task, TaskStatus, TaskPriority
from core.events import event_bus, Event, EventType
from security import TrustLevel, audit_chain
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.validator import ValidatorAgent
from intelligence.router import ModelRouter
from tools.registry import ToolRegistry, tool_registry

class AgentOrchestrator:
    def __init__(
        self,
        router: ModelRouter,
        tools: Optional[ToolRegistry] = None,
        episodic_memory: Optional[Any] = None,
        procedural_memory: Optional[Any] = None,
        context_engine: Optional[Any] = None
    ):
        self.router = router
        self.tools = tools or tool_registry
        self.episodic_memory = episodic_memory
        self.procedural_memory = procedural_memory
        self.context_engine = context_engine
        self.planner = PlannerAgent(self.router, self.tools, procedural_memory=self.procedural_memory)
        self.executor = ExecutorAgent(self.router, self.tools)
        self.validator = ValidatorAgent(self.router, self.tools)


    def run(
        self,
        objective: str,
        trust_level: TrustLevel = TrustLevel.LOCAL_OWNER,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Tuple[bool, str, Task]:
        """Execute the complete Tri-Agent lifecycle: Plan -> Execute -> Validate."""
        task = Task(objective=objective, priority=priority)
        
        event_bus.publish(Event(
            event_type=EventType.TASK_CREATED,
            source="AgentOrchestrator",
            payload={"task_id": task.id, "objective": objective}
        ))

        audit_chain.log_event(
            event_type="TASK_INITIATED",
            action="orchestrator_run",
            result="STARTED",
            trust_level=trust_level.value,
            risk_level="MEDIUM",
            details={"task_id": task.id, "objective": objective}
        )

        try:
            # 1. Planning Phase
            graph = self.planner.plan(task)
            event_bus.publish(Event(
                event_type=EventType.TASK_STATUS_CHANGED,
                source="AgentOrchestrator",
                payload={"task_id": task.id, "status": task.status.value, "steps": len(task.subtasks)}
            ))

            # 2. Execution Phase
            exec_ok = self.executor.execute_graph(graph, trust_level=trust_level)
            if not exec_ok:
                event_bus.publish(Event(
                    event_type=EventType.TASK_FAILED,
                    source="AgentOrchestrator",
                    payload={"task_id": task.id, "error": task.error}
                ))
                if self.episodic_memory:
                    self.episodic_memory.record_episode(
                        summary=f"Task execution failed: {objective} ({task.error})",
                        event_type="task_failed",
                        task_id=task.id,
                        importance=3
                    )
                if self.procedural_memory and task.artifacts.get("matched_procedure_id"):
                    self.procedural_memory.record_outcome(task.artifacts["matched_procedure_id"], False)
                return False, f"Execution halted: {task.error}", task

            # 3. Validation Phase
            val_ok, response_text = self.validator.validate_and_synthesize(task)
            if not val_ok:
                event_bus.publish(Event(
                    event_type=EventType.TASK_FAILED,
                    source="AgentOrchestrator",
                    payload={"task_id": task.id, "error": response_text}
                ))
                if self.episodic_memory:
                    self.episodic_memory.record_episode(
                        summary=f"Task validation failed: {objective}",
                        event_type="task_failed",
                        task_id=task.id,
                        importance=3
                    )
                if self.procedural_memory and task.artifacts.get("matched_procedure_id"):
                    self.procedural_memory.record_outcome(task.artifacts["matched_procedure_id"], False)
                return False, response_text, task

            # Success
            event_bus.publish(Event(
                event_type=EventType.TASK_COMPLETED,
                source="AgentOrchestrator",
                payload={"task_id": task.id}
            ))

            audit_chain.log_event(
                event_type="TASK_COMPLETED",
                action="orchestrator_run",
                result="SUCCESS",
                trust_level=trust_level.value,
                risk_level="LOW",
                details={"task_id": task.id, "steps_completed": len(task.subtasks)}
            )

            if self.episodic_memory:
                self.episodic_memory.record_episode(
                    summary=f"Successfully completed: {objective}",
                    event_type="task_completed",
                    task_id=task.id,
                    importance=2,
                    details={"steps_count": len(task.subtasks)}
                )

            if self.procedural_memory and task.artifacts.get("matched_procedure_id"):
                self.procedural_memory.record_outcome(task.artifacts["matched_procedure_id"], True)

            return True, response_text, task

        except Exception as e:
            task.mark_status(TaskStatus.FAILED, error=str(e))
            audit_chain.log_event(
                event_type="TASK_EXCEPTION",
                action="orchestrator_run",
                result="EXCEPTION",
                trust_level=trust_level.value,
                risk_level="HIGH",
                details={"task_id": task.id, "exception": str(e)}
            )
            if self.episodic_memory:
                self.episodic_memory.record_episode(
                    summary=f"Exception during task: {objective} ({e})",
                    event_type="task_exception",
                    task_id=task.id,
                    importance=4
                )
            return False, f"Orchestration failure: {e}", task

