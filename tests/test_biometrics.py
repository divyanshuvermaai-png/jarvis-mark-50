"""
Unit and Integration Tests for macOS Touch ID Biometrics (Milestone 2 - Track 3):
- BiometricAuthenticator (Native LocalAuthentication LAContext evaluation)
- BiometricTool (J.A.R.V.I.S. tool registration & schema)
- SecurityKernel.elevate_with_biometrics & get_status
- Bootstrap integration
"""
import unittest
from unittest.mock import patch, MagicMock
import os

from security.biometrics import BiometricAuthenticator, biometric_authenticator
from tools.builtins.biometrics_tool import BiometricTool
from security.security_kernel import security_kernel, SecurityKernel
from security.capabilities import Capability, RiskTier
from app.bootstrap import bootstrap_jarvis


class TestBiometricAuthenticator(unittest.TestCase):
    def setUp(self):
        self.auth = BiometricAuthenticator()

    def test_hardware_detection(self):
        # On this M5 Mac, is_touch_id_supported returns boolean without crashing
        is_supported = self.auth.is_touch_id_supported()
        self.assertIsInstance(is_supported, bool)
        is_device_auth = self.auth.is_device_owner_auth_supported()
        self.assertIsInstance(is_device_auth, bool)

    def test_test_override_allow(self):
        with patch.dict(os.environ, {"JARVIS_BYPASS_BIOMETRICS_TESTING": "allow"}):
            success, err = self.auth.authenticate(reason="Unit test verification")
            self.assertTrue(success)
            self.assertIsNone(err)

    def test_test_override_deny(self):
        with patch.dict(os.environ, {"JARVIS_BYPASS_BIOMETRICS_TESTING": "deny"}):
            success, err = self.auth.authenticate(reason="Unit test rejection")
            self.assertFalse(success)
            self.assertIn("rejected", err.lower())

    @patch("security.biometrics.LocalAuthentication")
    def test_mocked_touch_id_success(self, mock_la):
        mock_context = MagicMock()
        mock_la.LAContext.alloc.return_value.init.return_value = mock_context
        mock_la.LAPolicyDeviceOwnerAuthentication = 2
        mock_context.canEvaluatePolicy_error_.return_value = (True, None)

        def mock_eval_policy(policy, reason, reply):
            reply(True, None)

        mock_context.evaluatePolicy_localizedReason_reply_.side_effect = mock_eval_policy

        with patch.dict(os.environ, {}, clear=True):
            # Ensure no test override is set
            os.environ.pop("JARVIS_BYPASS_BIOMETRICS_TESTING", None)
            auth = BiometricAuthenticator()
            auth._available = True
            success, err = auth.authenticate(reason="Verify operation")
            self.assertTrue(success)
            self.assertIsNone(err)

    @patch("security.biometrics.LocalAuthentication")
    def test_mocked_touch_id_user_cancelled(self, mock_la):
        mock_context = MagicMock()
        mock_la.LAContext.alloc.return_value.init.return_value = mock_context
        mock_la.LAPolicyDeviceOwnerAuthentication = 2
        mock_context.canEvaluatePolicy_error_.return_value = (True, None)

        mock_error = MagicMock()
        mock_error.localizedDescription.return_value = "User canceled authentication."

        def mock_eval_policy(policy, reason, reply):
            reply(False, mock_error)

        mock_context.evaluatePolicy_localizedReason_reply_.side_effect = mock_eval_policy

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("JARVIS_BYPASS_BIOMETRICS_TESTING", None)
            auth = BiometricAuthenticator()
            auth._available = True
            success, err = auth.authenticate(reason="Verify operation")
            self.assertFalse(success)
            self.assertIn("canceled", err.lower())

    @patch("security.biometrics.LocalAuthentication")
    def test_mocked_policy_evaluation_failure(self, mock_la):
        mock_context = MagicMock()
        mock_la.LAContext.alloc.return_value.init.return_value = mock_context
        mock_la.LAPolicyDeviceOwnerAuthentication = 2

        mock_err = MagicMock()
        mock_err.localizedDescription.return_value = "No biometrics enrolled."
        mock_context.canEvaluatePolicy_error_.return_value = (False, mock_err)

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("JARVIS_BYPASS_BIOMETRICS_TESTING", None)
            auth = BiometricAuthenticator()
            auth._available = True
            success, err = auth.authenticate(reason="Verify operation")
            self.assertFalse(success)
            self.assertIn("cannot evaluate", err.lower())


class TestBiometricTool(unittest.TestCase):
    def setUp(self):
        self.tool = BiometricTool()

    def test_schema_and_metadata(self):
        self.assertEqual(self.tool.id, "biometrics")
        self.assertEqual(self.tool.required_capability, Capability.SECURITY_ADMIN)
        self.assertEqual(self.tool.risk_tier, RiskTier.MODERATE)
        self.assertIn("action", self.tool.parameters_schema["properties"])

    def test_tool_status_action(self):
        res = self.tool.execute({"action": "status"})
        self.assertTrue(res.success)
        self.assertIn("Biometric Status", res.data)
        self.assertIn("touch_id", res.metadata)

    def test_tool_verify_action_allow(self):
        with patch.dict(os.environ, {"JARVIS_BYPASS_BIOMETRICS_TESTING": "allow"}):
            res = self.tool.execute({"action": "verify", "reason": "Testing Touch ID"})
            self.assertTrue(res.success)
            self.assertIn("verified via touch id", res.data.lower())

    def test_tool_verify_action_deny(self):
        with patch.dict(os.environ, {"JARVIS_BYPASS_BIOMETRICS_TESTING": "deny"}):
            res = self.tool.execute({"action": "verify", "reason": "Testing Touch ID"})
            self.assertFalse(res.success)
            self.assertIn("rejected", res.error.lower())


class TestSecurityKernelBiometricIntegration(unittest.TestCase):
    def test_elevate_with_biometrics(self):
        with patch.dict(os.environ, {"JARVIS_BYPASS_BIOMETRICS_TESTING": "allow"}):
            success, err = security_kernel.elevate_with_biometrics(
                action_name="shell_exec",
                reason="Authorize high-privilege diagnostics"
            )
            self.assertTrue(success)
            self.assertIsNone(err)

    def test_security_kernel_status_includes_biometrics(self):
        status = security_kernel.get_status()
        self.assertIn("biometrics", status)
        self.assertIn("touch_id", status["biometrics"])
        self.assertIn("device_owner_auth", status["biometrics"])


class TestBootstrapBiometricsIntegration(unittest.TestCase):
    def test_bootstrap_registers_biometrics_tool_and_procedure(self):
        container = bootstrap_jarvis()
        tool = container.tools.get_tool("biometrics")
        self.assertIsNotNone(tool)

        match = container.procedural_memory.find_matching_procedure("verify identity with touch id")
        self.assertIsNotNone(match)
        self.assertEqual(match["name"], "Biometric Identity Verification")


if __name__ == "__main__":
    unittest.main()
