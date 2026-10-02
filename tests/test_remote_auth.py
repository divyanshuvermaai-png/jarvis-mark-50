"""
Test suite for J.A.R.V.I.S. Remote Passcode Authentication Gate & Integrated Capabilities.
Verifies fail-closed authentication on all remote routes, token generation/verification,
and integrated diagnostics, self-test, and CLI console.
"""
import unittest
import json
from unittest.mock import patch

from main_2 import (
    remote_app,
    get_remote_passcode,
    generate_session_token,
    verify_session_token
)

class TestRemoteAuthAndCapabilities(unittest.TestCase):
    def setUp(self):
        self.client = remote_app.test_client()
        self.valid_passcode = get_remote_passcode()
        self.token = generate_session_token()
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def test_token_verification(self):
        valid, msg = verify_session_token(self.token)
        self.assertTrue(valid, msg)

        # Invalid signatures must fail
        invalid, _ = verify_session_token("12345.fake_signature")
        self.assertFalse(invalid)

        # None token must fail
        none_token, _ = verify_session_token(None)
        self.assertFalse(none_token)

    def test_unauthenticated_requests_blocked_when_auth_enforced(self):
        endpoints = [
            ("/api/chat", "POST", {"message": "hello"}),
            ("/remote/chat", "POST", {"message": "hello"}),
            ("/api/diagnostics", "GET", None),
            ("/api/test", "GET", None),
            ("/api/cli", "POST", {"command": "help"}),
            ("/api/tts", "POST", {"text": "Good day"}),
        ]
        with patch("main_2.REQUIRE_AUTH", True):
            for path, method, payload in endpoints:
                with self.subTest(endpoint=path, method=method):
                    if method == "POST":
                        res = self.client.post(path, json=payload or {})
                    else:
                        res = self.client.get(path)
                    self.assertEqual(res.status_code, 401, f"{path} should reject unauthenticated requests with 401")
                    data = res.get_json()
                    self.assertFalse(data.get("success", True))
                    self.assertTrue(data.get("auth_required", False))

    def test_open_mode_allows_direct_requests(self):
        with patch("main_2.REQUIRE_AUTH", False):
            res = self.client.get("/api/diagnostics")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("success", False))

    def test_passcode_auth_route_invalid(self):
        with patch("main_2.REQUIRE_AUTH", True):
            res = self.client.post("/api/auth", json={"passcode": "wrong-code-xyz"})
            self.assertEqual(res.status_code, 401)
            data = res.get_json()
            self.assertFalse(data.get("success", True))
            self.assertIn("Invalid access passcode", data.get("error", ""))

    def test_passcode_auth_route_valid(self):
        res = self.client.post("/api/auth", json={"passcode": self.valid_passcode})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success", False))
        token = data.get("token", "")
        self.assertTrue(token)
        valid, _ = verify_session_token(token)
        self.assertTrue(valid)

    def test_auth_verify_endpoint(self):
        with patch("main_2.REQUIRE_AUTH", True):
            # Without token -> 401
            res_fail = self.client.get("/api/auth/verify")
            self.assertEqual(res_fail.status_code, 401)
            self.assertFalse(res_fail.get_json().get("authenticated", True))

            # With token -> 200
            res_ok = self.client.get("/api/auth/verify", headers=self.auth_headers)
            self.assertEqual(res_ok.status_code, 200)
            self.assertTrue(res_ok.get_json().get("authenticated", False))

    def test_authenticated_diagnostics(self):
        res = self.client.get("/api/diagnostics", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success", False))
        self.assertEqual(data.get("status"), "OPERATIONAL")
        self.assertIn("ai_engine", data)
        self.assertIn("security", data)

    def test_authenticated_self_test(self):
        res = self.client.post("/api/test", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success", False))
        self.assertIn("tests", data)
        self.assertGreater(data.get("total", 0), 0)

    def test_authenticated_cli_commands(self):
        commands = ["help", "status", "health", "test", "model"]
        for cmd in commands:
            with self.subTest(command=cmd):
                res = self.client.post("/api/cli", json={"command": cmd}, headers=self.auth_headers)
                self.assertEqual(res.status_code, 200)
                data = res.get_json()
                self.assertTrue(data.get("success", False))
                self.assertTrue(len(data.get("output", "")) > 0)

    @patch("main_2.gemma_local.infer_gemma", return_value="Mocked remote response.")
    def test_authenticated_chat_success(self, mock_infer):
        res = self.client.post(
            "/api/chat",
            json={"message": "What is the speed of light?"},
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success", False))
    def test_random_passcode_generation_and_uniqueness(self):
        from main_2 import generate_random_passcode
        code1 = generate_random_passcode(8)
        code2 = generate_random_passcode(8)
        self.assertEqual(len(code1), 8)
        self.assertEqual(len(code2), 8)
        self.assertNotEqual(code1, code2)
        # Verify no ambiguous characters (0, O, 1, I, L)
        for ch in "0O1IL":
            self.assertNotIn(ch, code1)
            self.assertNotIn(ch, code2)

    def test_passcode_auth_case_and_hyphen_insensitive(self):
        from main_2 import verify_passcode_match
        real = "7K9M4P2X"
        # Exact match
        self.assertTrue(verify_passcode_match("7K9M4P2X", real))
        # Lowercase match
        self.assertTrue(verify_passcode_match("7k9m4p2x", real))
        # Hyphenated match
        self.assertTrue(verify_passcode_match("7K9M-4P2X", real))
        # Space match
        self.assertTrue(verify_passcode_match("7K9M 4P2X", real))
        # Invalid match
        self.assertFalse(verify_passcode_match("WRONG123", real))

if __name__ == "__main__":
    unittest.main()
