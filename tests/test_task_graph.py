"""
Test Suite: Task Graph & Dependency Resolution
"""
import unittest
from core.task_manager import Task, SubTask, TaskGraph, CyclicDependencyError, SubTaskStatus

class TestTaskGraph(unittest.TestCase):
    def test_01_simple_dependency_resolution(self):
        task = Task(objective="Inspect system and report")
        graph = TaskGraph(task)
        
        st1 = SubTask(id="step_1", title="Get Info", tool_hint="system_info")
        st2 = SubTask(id="step_2", title="Summarize", dependencies=["step_1"])
        graph.add_subtask(st1)
        graph.add_subtask(st2)
        
        self.assertTrue(graph.validate())
        
        # Initially only step_1 is ready
        ready = graph.get_ready_subtasks()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "step_1")

        # Mark step_1 completed -> step_2 becomes ready
        ready[0].status = SubTaskStatus.COMPLETED
        ready2 = graph.get_ready_subtasks()
        self.assertEqual(len(ready2), 1)
        self.assertEqual(ready2[0].id, "step_2")

    def test_02_cycle_detection(self):
        task = Task(objective="Cycle test")
        graph = TaskGraph(task)
        
        st1 = SubTask(id="a", dependencies=["b"])
        st2 = SubTask(id="b", dependencies=["a"])
        graph.add_subtask(st1)
        graph.add_subtask(st2)

        with self.assertRaises(CyclicDependencyError):
            graph.validate()

    def test_03_missing_dependency(self):
        task = Task(objective="Missing dep test")
        graph = TaskGraph(task)
        st1 = SubTask(id="a", dependencies=["non_existent"])
        graph.add_subtask(st1)

        with self.assertRaises(ValueError):
            graph.validate()

if __name__ == "__main__":
    unittest.main()
