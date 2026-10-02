"""
Test Suite: Tri-Agent Autonomous Pipeline (Planner -> Executor -> Validator)
"""
import unittest
from app.bootstrap import bootstrap_jarvis
from security import TrustLevel

class TestAgentPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = bootstrap_jarvis()

    def test_01_conversational_task(self):
        success, response, task = self.container.orchestrator.run(
            objective="State your name, creator, and current status.",
            trust_level=TrustLevel.LOCAL_OWNER
        )
        self.assertTrue(success)
        self.assertGreater(len(response), 10)
        self.assertEqual(task.status.value, "COMPLETED")
        self.assertGreaterEqual(len(task.subtasks), 1)

    def test_02_tool_integrated_task(self):
        success, response, task = self.container.orchestrator.run(
            objective="Check the current CPU and RAM metrics and tell me how the system is performing.",
            trust_level=TrustLevel.LOCAL_OWNER
        )
        self.assertTrue(success)
        self.assertEqual(task.status.value, "COMPLETED")
        # Subtasks should have executed successfully
        for st in task.subtasks:
            self.assertEqual(st.status.value, "COMPLETED")

if __name__ == "__main__":
    unittest.main()
