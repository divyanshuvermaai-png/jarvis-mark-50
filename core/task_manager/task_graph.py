"""
J.A.R.V.I.S. Task Graph & Dependency Engine
Provides DAG validation, topological sorting, dependency checks, and execution ordering.
"""
from typing import List, Dict, Set, Optional
from .task import Task, SubTask, SubTaskStatus, TaskStatus

class CyclicDependencyError(Exception):
    pass

class TaskGraph:
    def __init__(self, task: Task):
        self.task = task

    def add_subtask(self, subtask: SubTask):
        self.task.subtasks.append(subtask)

    def validate(self) -> bool:
        """Validate DAG: check that all dependencies exist and there are no cycles."""
        ids = {st.id for st in self.task.subtasks}
        for st in self.task.subtasks:
            for dep in st.dependencies:
                if dep not in ids:
                    raise ValueError(f"SubTask '{st.id}' depends on non-existent SubTask '{dep}'")
        
        # Cycle detection via topological sort (Kahn's Algorithm)
        in_degree = {st.id: len(st.dependencies) for st in self.task.subtasks}
        adj = {st.id: [] for st in self.task.subtasks}
        for st in self.task.subtasks:
            for dep in st.dependencies:
                adj[dep].append(st.id)

        queue = [st_id for st_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.task.subtasks):
            raise CyclicDependencyError("Cyclic dependency detected in TaskGraph")
        return True

    def get_ready_subtasks(self) -> List[SubTask]:
        """Return subtasks that are PENDING and whose dependencies are all COMPLETED."""
        completed_ids = {st.id for st in self.task.subtasks if st.status == SubTaskStatus.COMPLETED}
        ready = []
        for st in self.task.subtasks:
            if st.status == SubTaskStatus.PENDING:
                if all(dep in completed_ids for dep in st.dependencies):
                    ready.append(st)
        return ready

    def is_complete(self) -> bool:
        """True if all subtasks are COMPLETED."""
        return len(self.task.subtasks) > 0 and all(st.status == SubTaskStatus.COMPLETED for st in self.task.subtasks)

    def has_failures(self) -> bool:
        """True if any subtask has status FAILED."""
        return any(st.status == SubTaskStatus.FAILED for st in self.task.subtasks)
