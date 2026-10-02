"""
Test Suite: Model Router Intelligence & Fallbacks
"""
import unittest
from intelligence.router import ModelRouter, TaskComplexity, PrivacyTier

class TestModelRouter(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()

    def test_01_classification(self):
        # Conversational
        c1 = self.router.classify_task("Hello Jarvis, good morning!")
        self.assertEqual(c1, TaskComplexity.CONVERSATIONAL)

        # Coding
        c2 = self.router.classify_task("Write a python function to compute fibonacci")
        self.assertEqual(c2, TaskComplexity.CODING)

        # Research
        c3 = self.router.classify_task("Research and compare quantum computing vs neuromorphic chips")
        self.assertEqual(c3, TaskComplexity.RESEARCH)

        # Multimodal
        c4 = self.router.classify_task("What is on this screen?", has_image=True)
        self.assertEqual(c4, TaskComplexity.MULTIMODAL)

    def test_02_strict_local_privacy(self):
        plan = self.router.route("Analyze confidential financials", privacy=PrivacyTier.STRICT_LOCAL)
        self.assertEqual(plan.primary_provider_id, "local_gemma_4_e2b")
        self.assertEqual(len(plan.fallback_chain), 0)

    def test_03_multimodal_routing(self):
        plan = self.router.route("Inspect this screenshot", has_image=True)
        # Should route to Gemini if available, else local Gemma
        self.assertIn(plan.primary_provider_id, ("google_gemini", "local_gemma_4_e2b"))

if __name__ == "__main__":
    unittest.main()
