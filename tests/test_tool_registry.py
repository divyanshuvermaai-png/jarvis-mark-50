"""
Test Suite: Secure Tool Registry & Builtins
"""
import unittest
import tempfile
import os
from pathlib import Path
from tools.registry import ToolRegistry
from tools.builtins import SystemInfoTool, FileOpsTool, WebSearchTool
from security import TrustLevel

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(SystemInfoTool())
        self.registry.register(FileOpsTool())
        self.registry.register(WebSearchTool())

    def test_01_registration_and_schemas(self):
        self.assertIsNotNone(self.registry.get_tool("system_info"))
        self.assertIsNotNone(self.registry.get_tool("file_ops"))
        self.assertIsNotNone(self.registry.get_tool("web_search"))
        schemas = self.registry.export_schemas()
        self.assertEqual(len(schemas), 3)

    def test_02_system_info_execution(self):
        res = self.registry.execute_tool("system_info", {"metric": "all"})
        self.assertTrue(res.success)
        self.assertIn("cpu_percent", res.data)
        self.assertIn("ram_total_gb", res.data)

    def test_03_file_ops_execution(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("Hello J.A.R.V.I.S.")
            temp_path = tf.name

        try:
            # Read
            read_res = self.registry.execute_tool("file_ops", {"operation": "read", "path": temp_path})
            self.assertTrue(read_res.success)
            self.assertIn("Hello J.A.R.V.I.S.", read_res.data)

            # Traversal block test
            bad_res = self.registry.execute_tool("file_ops", {"operation": "read", "path": "/etc/passwd"})
            # Should be blocked by action_validator path containment
            self.assertFalse(bad_res.success)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == "__main__":
    unittest.main()
