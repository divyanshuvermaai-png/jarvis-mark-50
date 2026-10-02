"""
J.A.R.V.I.S. Task Data Models
Defines the lifecycle, priority, states, and verification constraints of tasks.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"

class TaskPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

class SubTaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass
class SubTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    assigned_agent: str = "ExecutorAgent"
    tool_hint: Optional[str] = None
    tool_params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    verification_rule: Optional[str] = None
    execution_time_ms: float = 0.0

@dataclass
class Task:
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    objective: str = ""
    requester: str = "user"
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str = "PlannerAgent"
    selected_model: Optional[str] = None
    subtasks: List[SubTask] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None
    audit_events: List[str] = field(default_factory=list)

    def mark_status(self, new_status: TaskStatus, error: Optional[str] = None):
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat()
        if error:
            self.error = error
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = datetime.utcnow().isoformat()

    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        for st in self.subtasks:
            if st.id == subtask_id:
                return st
        return None

    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        return self.status in (TaskStatus.FAILED, TaskStatus.CANCELLED)

