"""
Unit and Integration Tests for J.A.R.V.I.S. Phase 2 Memory & Context Subsystems:
- SemanticMemory (SQLite + FTS5 + Vector Cosine)
- EpisodicMemory (Chronological Task & Milestone Logger)
- ProceduralMemory (Workflow Recipes & Tool Sequences)
- ContextEngine (Multi-tier context fusion & token budgeting)
- AgentOrchestrator Memory Integration
"""
import unittest
import tempfile
import shutil
from pathlib import Path

from memory.semantic import SemanticMemory, compute_local_embedding
from memory.episodic import EpisodicMemory
from memory.procedural import ProceduralMemory
from memory.short_term import ShortTermMemory
from memory.preferences import PreferenceStore
from intelligence.context.context_engine import ContextEngine
from core.orchestration.orchestrator import AgentOrchestrator
from intelligence.router.model_router import ModelRouter
from app.config import JarvisConfig
from tools.registry import ToolRegistry
from tools.builtins.system_info import SystemInfoTool
from core.task_manager.task import TaskPriority
from security.trust import TrustLevel


class TestSemanticMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_semantic.db"
        self.mem = SemanticMemory(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_get_and_count(self):
        doc_id = self.mem.add(
            content="Divyanshu Verma is the Founder and CEO of Divyanshu Industries.",
            category="fact",
            metadata={"source": "founder_profile"}
        )
        self.assertIsNotNone(doc_id)
        self.assertEqual(self.mem.count(), 1)
        self.assertEqual(self.mem.count(category="fact"), 1)
        self.assertEqual(self.mem.count(category="other"), 0)

        entry = self.mem.get(doc_id)
        self.assertIsNotNone(entry)
        self.assertIn("Divyanshu Verma", entry["content"])
        self.assertEqual(entry["category"], "fact")
        self.assertEqual(entry["metadata"]["source"], "founder_profile")

    def test_fts5_text_search(self):
        self.mem.add("Building Apple Silicon M5 optimized AI architecture", category="tech")
        self.mem.add("Jaipur is the capital city of Rajasthan", category="geo")
        self.mem.add("Quantum computing utilizes superconducting qubits", category="science")

        # Exact / Stemmed query
        results = self.mem.search("Apple Silicon", mode="text")
        self.assertTrue(len(results) >= 1)
        self.assertIn("Apple Silicon", results[0]["content"])

        geo_results = self.mem.search("Jaipur", mode="text")
        self.assertEqual(len(geo_results), 1)
        self.assertIn("Rajasthan", geo_results[0]["content"])

    def test_vector_similarity_search(self):
        self.mem.add("Apple MacBook Air M5 with 32 gigabytes of unified memory", category="hardware")
        self.mem.add("Chocolate chip cookies baking recipe with butter and sugar", category="food")

        # Query conceptually close to hardware
        results = self.mem.search("MacBook laptop RAM", mode="vector", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("MacBook Air", results[0]["content"])

    def test_hybrid_search(self):
        self.mem.add("High security defense-in-depth zero-trust kernel", category="security")
        self.mem.add("Local offline MLX Gemma 4 inference engine", category="ai")

        hybrid_hits = self.mem.search("security defense zero-trust", mode="hybrid")
        self.assertTrue(len(hybrid_hits) >= 1)
        self.assertEqual(hybrid_hits[0]["category"], "security")
        self.assertIn("rrf_score", hybrid_hits[0])

    def test_delete_and_clear(self):
        doc_id = self.mem.add("Temporary secret data", category="temp")
        self.assertEqual(self.mem.count(), 1)
        deleted = self.mem.delete(doc_id)
        self.assertTrue(deleted)
        self.assertEqual(self.mem.count(), 0)

        self.mem.add("Item 1")
        self.mem.add("Item 2")
        self.assertEqual(self.mem.count(), 2)
        self.mem.clear()
        self.assertEqual(self.mem.count(), 0)

    def test_format_context(self):
        self.mem.add("Owner prefers dark mode and concise summaries", category="preference")
        ctx = self.mem.format_context("What are owner preferences?")
        self.assertIn("[RELEVANT MEMORY FACTS]", ctx)
        self.assertIn("Owner prefers dark mode", ctx)
        self.assertIn("[END RELEVANT MEMORY]", ctx)


class TestEpisodicMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_episodic.db"
        self.mem = EpisodicMemory(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_record_and_query_episodes(self):
        ep_id = self.mem.record_episode(
            summary="Deployed production microservice v1.0",
            event_type="deployment",
            session_id="sess_001",
            importance=3,
            details={"version": "1.0", "target": "local"}
        )
        self.assertIsNotNone(ep_id)
        self.assertEqual(self.mem.count(), 1)

        episodes = self.mem.get_recent_episodes(limit=5)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["event_type"], "deployment")
        self.assertEqual(episodes[0]["importance"], 3)
        self.assertEqual(episodes[0]["details"]["version"], "1.0")

    def test_filter_by_importance_and_event_type(self):
        self.mem.record_episode("Low priority routine ping", event_type="heartbeat", importance=1)
        self.mem.record_episode("Critical security firewall alert", event_type="security", importance=5)
        self.mem.record_episode("Task executed successfully", event_type="task_completed", importance=2)

        # Min importance = 2
        important = self.mem.get_recent_episodes(min_importance=2)
        self.assertEqual(len(important), 2)

        # Filter by event_type
        sec_events = self.mem.get_recent_episodes(event_type="security")
        self.assertEqual(len(sec_events), 1)
        self.assertIn("Critical security", sec_events[0]["summary"])

    def test_format_recent_context(self):
        self.mem.record_episode("Completed full system audit", event_type="milestone", importance=3)
        ctx = self.mem.format_recent_context()
        self.assertIn("[RECENT ACTIVITY & MILESTONES]", ctx)
        self.assertIn("Completed full system audit", ctx)


class TestProceduralMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_procedural.db"
        self.mem = ProceduralMemory(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_seed_procedures_exist(self):
        procs = self.mem.list_procedures()
        self.assertTrue(len(procs) >= 2)
        names = [p["name"] for p in procs]
        self.assertIn("Inspect Hardware Performance", names)

    def test_find_matching_procedure(self):
        match = self.mem.find_matching_procedure("Please check current cpu usage and diagnostics")
        self.assertIsNotNone(match)
        self.assertEqual(match["name"], "Inspect Hardware Performance")
        self.assertEqual(match["steps"][0]["tool"], "system_info")

    def test_record_outcome(self):
        match = self.mem.find_matching_procedure("cpu usage")
        proc_id = match["id"]
        initial_success = match["success_count"]

        self.mem.record_outcome(proc_id, success=True)
        updated = self.mem.get_procedure(proc_id)
        self.assertEqual(updated["success_count"], initial_success + 1)

        self.mem.record_outcome(proc_id, success=False)
        updated2 = self.mem.get_procedure(proc_id)
        self.assertEqual(updated2["failure_count"], 1)


class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        p = Path(self.test_dir)
        self.semantic = SemanticMemory(db_path=p / "sem.db")
        self.episodic = EpisodicMemory(db_path=p / "ep.db")
        self.procedural = ProceduralMemory(db_path=p / "proc.db")
        self.short_term = ShortTermMemory(max_turns=4)
        self.prefs = PreferenceStore(storage_path=p / "prefs.json")

        self.soul_file = p / "soul.md"
        self.soul_file.write_text("Custom test soul for J.A.R.V.I.S.")

        self.engine = ContextEngine(
            short_term=self.short_term,
            preferences=self.prefs,
            semantic=self.semantic,
            episodic=self.episodic,
            procedural=self.procedural,
            soul_path=self.soul_file
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_assemble_context(self):
        self.semantic.add("Divyanshu is building a humanoid robotic laboratory", category="project")
        self.episodic.record_episode("Bootstrapped core subsystems", event_type="startup", importance=3)
        self.short_term.add_user_message("Hello Jarvis")
        self.short_term.add_assistant_message("Good day, Sir.")

        block = self.engine.assemble("Tell me about the robotic laboratory", max_budget_tokens=4096)

        self.assertIn("[SYSTEM_INSTRUCTION]", block.assembled_prompt)
        self.assertIn("Custom test soul for J.A.R.V.I.S.", block.assembled_prompt)
        self.assertIn("[ENVIRONMENT & PREFERENCES]", block.assembled_prompt)
        self.assertIn("robotic laboratory", block.assembled_prompt)
        self.assertIn("[USER_INPUT]", block.assembled_prompt)
        self.assertIn("Tell me about the robotic laboratory", block.user_prompt)
        self.assertTrue(block.estimated_tokens > 0)


class TestOrchestratorMemoryIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        p = Path(self.test_dir)
        self.episodic = EpisodicMemory(db_path=p / "ep.db")
        self.procedural = ProceduralMemory(db_path=p / "proc.db")
        
        cfg = JarvisConfig(system_name="JARVIS-TEST", version="5.1.0-test")
        self.router = ModelRouter(config=cfg)
        self.tools = ToolRegistry()
        self.tools.register(SystemInfoTool())

        self.orchestrator = AgentOrchestrator(
            router=self.router,
            tools=self.tools,
            episodic_memory=self.episodic,
            procedural_memory=self.procedural
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_procedural_fast_path_and_episodic_logging(self):
        # "check cpu usage" matches seed procedure "Inspect Hardware Performance"
        success, response, task = self.orchestrator.run(
            objective="check cpu usage",
            trust_level=TrustLevel.LOCAL_OWNER
        )
        self.assertTrue(success)
        self.assertTrue(task.is_completed())
        self.assertEqual(task.artifacts.get("matched_procedure_id"), self.procedural.find_matching_procedure("cpu usage")["id"])

        # Verify episodic memory logged the event
        episodes = self.episodic.get_recent_episodes(limit=5)
        self.assertTrue(len(episodes) >= 1)
        self.assertEqual(episodes[0]["event_type"], "task_completed")
        self.assertIn("Successfully completed", episodes[0]["summary"])

        # Verify procedure success count was incremented
        proc = self.procedural.get_procedure(task.artifacts["matched_procedure_id"])
        self.assertGreaterEqual(proc["success_count"], 1)


if __name__ == "__main__":
    unittest.main()
