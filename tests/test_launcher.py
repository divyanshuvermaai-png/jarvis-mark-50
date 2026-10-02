"""
Tests for J.A.R.V.I.S. Master Launcher and Packaging (Phase 8)
Verifies CLI argument dispatch, diagnostics runner, telemetry export,
and LaunchAgent plist generation.
"""
import unittest
import sys
import io
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from launcher import run_diagnostics, run_telemetry, manage_service


class TestLauncher(unittest.TestCase):
    def test_run_diagnostics(self):
        f = io.StringIO()
        with patch('sys.stdout', f):
            code = run_diagnostics()
        output = f.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("DIAGNOSTIC HEALTH REPORT", output)
        self.assertIn("Unified RAM", output)
        self.assertIn("Disk Storage", output)

    def test_run_telemetry(self):
        f = io.StringIO()
        with patch('sys.stdout', f):
            run_telemetry()
        output = f.getvalue()
        data = json.loads(output)
        self.assertIn("hardware", data)
        self.assertIn("security", data)
        self.assertIn("timestamp", data)

    def test_manage_service_install_and_uninstall(self):
        test_plist = Path("/tmp/test_jarvis.plist")
        with patch("launcher.LAUNCHAGENT_PLIST", test_plist), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test Install
            res = manage_service("install")
            self.assertEqual(res, 0)
            self.assertTrue(test_plist.exists())

            content = test_plist.read_text()
            self.assertIn("com.divyanshu.jarvis", content)
            self.assertIn("ProgramArguments", content)
            self.assertIn("RunAtLoad", content)

            # Test Uninstall
            res = manage_service("uninstall")
            self.assertEqual(res, 0)
            self.assertFalse(test_plist.exists())

    def test_manage_service_invalid_action(self):
        f = io.StringIO()
        with patch('sys.stdout', f):
            res = manage_service("invalid_action_xyz")
        self.assertEqual(res, 1)
        self.assertIn("Unknown service action", f.getvalue())


if __name__ == '__main__':
    unittest.main()
