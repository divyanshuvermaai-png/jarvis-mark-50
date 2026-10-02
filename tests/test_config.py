"""
Test Suite: Unified Configuration Engine
"""
import unittest
import os
from app.config import JarvisConfig

class TestJarvisConfig(unittest.TestCase):
    def test_01_defaults(self):
        cfg = JarvisConfig.load()
        self.assertEqual(cfg.owner_name, "Divyanshu Verma")
        self.assertEqual(cfg.organization, "Divyanshu Industries")
        self.assertEqual(cfg.hardware.chip, "Apple M5")
        self.assertEqual(cfg.hardware.unified_memory_gb, 32)
        self.assertTrue(cfg.security.defense_in_depth)
        self.assertTrue(cfg.security.kill_switch_enabled)

    def test_02_env_override(self):
        os.environ["JARVIS_OWNER_NAME"] = "Test Architect"
        cfg = JarvisConfig.load()
        self.assertEqual(cfg.owner_name, "Test Architect")
        del os.environ["JARVIS_OWNER_NAME"]

if __name__ == "__main__":
    unittest.main()
