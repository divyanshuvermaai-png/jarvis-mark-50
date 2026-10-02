"""
Test suite for J.A.R.V.I.S. HUD Backend Integration Endpoints.
Verifies the new unified endpoints for health diagnostics, self-test runner,
voice TTS status, and tactical CLI console execution on main.py.
"""
import unittest
import json
from unittest.mock import patch

from main import app

class TestHudIntegrationEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_system_health_endpoint(self):
        res = self.client.get("/api/system/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("overall_status", data)
        self.assertIn("operational", data)
        self.assertIn("subsystems", data)
        self.assertIn("free_ram_gb", data)
        self.assertIn("disk_free_gb", data)

    def test_voice_status_endpoint(self):
        res = self.client.get("/api/voice/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "available")
        self.assertIn("RyanNeural", data.get("engine", ""))

    def test_voice_speak_validation(self):
        # Empty text -> 400
        res = self.client.post("/api/voice/speak", json={"text": ""})
        self.assertEqual(res.status_code, 400)

    def test_cli_execute_builtins(self):
        commands = ["help", "status", "health"]
        for cmd in commands:
            with self.subTest(command=cmd):
                res = self.client.post("/api/cli/execute", json={"command": cmd})
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get("success", False))
                self.assertTrue(len(data.get("output", "")) > 0)

    def test_system_test_endpoint(self):
        # With patch on unittest runner to keep unit test fast
        with patch("unittest.TextTestRunner.run") as mock_run:
            class MockResult:
                testsRun = 10
                failures = []
                errors = []
                def wasSuccessful(self):
                    return True
            mock_run.return_value = MockResult()

            res = self.client.get("/api/system/test")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("success", False))
            self.assertEqual(data.get("tests_run"), 10)
            self.assertEqual(data.get("passed"), 10)
            self.assertTrue(data.get("was_successful", False))

if __name__ == "__main__":
    unittest.main()
