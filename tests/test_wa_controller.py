import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from whatsapp_controller import WhatsAppController
from whatsapp_controller.contact_resolver import ContactResolver, is_phone_number
from whatsapp_controller.errors import ContactAmbiguousError, WhatsAppPermissionError
from integrations.whatsapp import WhatsAppTool
from main import parse_commands


class TestWhatsAppController(unittest.TestCase):
    def setUp(self):
        self.controller = WhatsAppController()

    def test_successful_message(self):
        self.controller.tools.resolver.check_ambiguity = MagicMock(return_value="Subham")
        self.controller.tools.messaging.open_chat = MagicMock(return_value={"success": True})
        self.controller.tools.messaging.send_text = MagicMock(return_value={"success": True})

        res = self.controller.send_message("subham", "hello")

        self.assertTrue(res['success'])
        self.assertEqual(res['status'], 'completed')
        self.assertEqual(res['contact'], 'Subham')
        self.controller.tools.messaging.open_chat.assert_called_once_with("Subham")
        self.controller.tools.messaging.send_text.assert_called_once_with("hello")

    def test_ambiguous_contact(self):
        self.controller.tools.resolver.check_ambiguity = MagicMock(side_effect=ContactAmbiguousError("Multiple contacts found"))

        res = self.controller.initiate_call("john")

        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 'error')
        self.assertEqual(res['error'], 'ContactAmbiguousError')

    def test_permission_error(self):
        self.controller.tools.resolver.check_ambiguity = MagicMock(return_value="Subham")
        self.controller.tools.messaging.open_chat = MagicMock(side_effect=WhatsAppPermissionError("Accessibility permission denied"))

        res = self.controller.send_message("subham", "hello")

        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 'error')
        self.assertEqual(res['error'], 'WhatsAppPermissionError')

    def test_phone_number_resolver_bypass(self):
        resolver = ContactResolver()
        phone = "+1 (555) 234-5678"
        self.assertTrue(is_phone_number(phone))
        # Resolver must return cleaned phone string without running osascript
        with patch('subprocess.run') as mock_sub:
            res = resolver.check_ambiguity(phone)
            self.assertEqual(res, "+15552345678")
            mock_sub.assert_not_called()

    def test_send_media_file_not_found(self):
        self.controller.tools.resolver.check_ambiguity = MagicMock(return_value="Subham")
        res = self.controller.send_media("Subham", "/tmp/non_existent_file_jarvis_12345.png")
        self.assertFalse(res['success'])
        self.assertEqual(res['status'], 'error')
        self.assertIn("FileNotFoundError", res['error'])

    def test_send_media_success(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(b"fake image data")
            temp_path = tf.name

        try:
            self.controller.tools.resolver.check_ambiguity = MagicMock(return_value="Subham")
            self.controller.tools.media.messaging.open_chat = MagicMock(return_value={"success": True})
            self.controller.tools.media.bridge.run_jxa = MagicMock(return_value={"success": True})

            with patch('whatsapp_controller.actions.media.set_clipboard_media', return_value=True):
                with patch('whatsapp_controller.actions.media.set_clipboard_text', return_value=True):
                    res = self.controller.send_media("subham", temp_path, caption="Tactical telemetry")

            self.assertTrue(res['success'])
            self.assertEqual(res['status'], 'completed')
            self.assertEqual(res['contact'], 'Subham')
            self.assertEqual(res['file'], temp_path)
            self.assertEqual(res['caption'], "Tactical telemetry")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_main_parse_whatsapp_media(self):
        cmd = "send photo /tmp/analysis.png to Subham on whatsapp with caption Review this"
        actions = parse_commands(cmd)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'whatsapp_media')
        self.assertEqual(actions[0]['params']['contact'], 'subham')
        self.assertEqual(actions[0]['params']['file_path'], '/tmp/analysis.png')
        self.assertEqual(actions[0]['params']['caption'], 'review this')

    def test_integrations_whatsapp_tool_media(self):
        tool = WhatsAppTool()
        mock_wa = MagicMock()
        mock_wa.send_media.return_value = {
            "success": True,
            "status": "completed",
            "contact": "+919876543210",
            "file": "/tmp/scan.pdf"
        }
        tool._wa_tools = mock_wa

        result = tool.execute({
            "action": "send_media",
            "contact": "+919876543210",
            "file_path": "/tmp/scan.pdf",
            "caption": "Encrypted Sitrep"
        })

        self.assertTrue(result.success)
        mock_wa.send_media.assert_called_once_with("+919876543210", "/tmp/scan.pdf", caption="Encrypted Sitrep")


if __name__ == '__main__':
    unittest.main()
