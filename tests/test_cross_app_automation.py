"""
Test suite for J.A.R.V.I.S. Cross-Application Automation & Screen Share Frame Ingestion.
Tests:
- Natural language command chaining (WhatsApp, Instagram, YouTube)
- Instagram Direct Automation Tool
- YouTube Video Uploader Tool & AI Metadata Engine
- Screen Frame Ingestion Endpoint (/api/screen/frame)
"""
import os
import io
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from main import app, parse_commands, execute_action
from integrations.instagram import InstagramTool, InstagramController
from integrations.youtube import YouTubeUploaderTool, YouTubeUploader
from core.screen_awareness import screen_awareness

class TestCrossAppParsing(unittest.TestCase):
    def test_whatsapp_chained_command(self):
        actions = parse_commands("open whatsapp and send hello to subham")
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['action'], 'open_app')
        self.assertEqual(actions[0]['params']['name'], 'whatsapp')
        self.assertEqual(actions[1]['action'], 'whatsapp')
        self.assertEqual(actions[1]['params']['contact'], 'subham')
        self.assertEqual(actions[1]['params']['message'], 'hello')

    def test_whatsapp_send_direct(self):
        actions = parse_commands("send hello to subham")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'whatsapp')
        self.assertEqual(actions[0]['params']['contact'], 'subham')
        self.assertEqual(actions[0]['params']['message'], 'hello')

    def test_instagram_explicit_saying(self):
        actions = parse_commands("send message to raghav on instagram saying hello")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'instagram_dm')
        self.assertEqual(actions[0]['params']['recipient'], 'raghav')
        self.assertEqual(actions[0]['params']['message'], 'hello')

    def test_instagram_send_text_to(self):
        actions = parse_commands("send hello to raghav on instagram")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'instagram_dm')
        self.assertEqual(actions[0]['params']['recipient'], 'raghav')
        self.assertEqual(actions[0]['params']['message'], 'hello')

    def test_youtube_video_upload_prompt(self):
        actions = parse_commands('the video named "xyz" just upload it to youtube with suitable titles and description')
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'youtube_upload')
        self.assertEqual(actions[0]['params']['video_name'], 'xyz')

    def test_whatsapp_call_direct(self):
        actions = parse_commands("call raghav narayana on whatsapp")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'whatsapp_call')
        self.assertEqual(actions[0]['params']['contact'], 'raghav narayana')
        self.assertFalse(actions[0]['params']['video'])

    def test_whatsapp_make_call(self):
        actions = parse_commands("make a call to raghav narayana on whatsapp")
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'whatsapp_call')
        self.assertEqual(actions[0]['params']['contact'], 'raghav narayana')

    def test_youtube_video_upload_direct(self):
        actions = parse_commands('upload video demo.mp4 to youtube')
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['action'], 'youtube_upload')
        self.assertEqual(actions[0]['params']['video_name'], 'demo.mp4')


class TestMetaSanitizationAndActions(unittest.TestCase):
    def test_strip_cognitive_meta_layers(self):
        from main import strip_cognitive_meta
        raw_babble = """**(Layer 1: Immediate Intent Recognition)**
*Intent Detected: The user wants to see their screen.*
**(Layer 2: Contextual State Awareness)**
*Context: Requesting visual info.*
**(AGENT 1: The Planner)**
*Goal: Inspect display.*
**(AGENT 2: The Executor)**
*Tool Invocation: Screencapture.*
**(AGENT 3: The Validator)**
*Validation Check: Valid response.*
---
**J.A.R.V.I.S. Response (Output Strategy: Direct)**
"You are viewing VS Code with main.py open, Sir."
**✅ Next Step:** I await your command."""
        cleaned = strip_cognitive_meta(raw_babble)
        self.assertEqual(cleaned, "You are viewing VS Code with main.py open, Sir.")

    def test_parse_action_tags(self):
        from main import parse_action_tags
        speech = 'Placing a WhatsApp call to Raghav Narayana right away, Sir. [ACTION: whatsapp_call("raghav narayana")]'
        tags = parse_action_tags(speech)
        self.assertEqual(len(tags), 1)
        action_dict, tag_str = tags[0]
        self.assertEqual(action_dict['action'], 'whatsapp_call')
        self.assertEqual(action_dict['params']['contact'], 'raghav narayana')
        self.assertEqual(tag_str, '[ACTION: whatsapp_call("raghav narayana")]')

    def test_parse_chained_action_tags(self):
        from main import parse_action_tags
        speech = 'Opening WhatsApp and sending your greeting, Sir. [ACTION: open_app("whatsapp")] [ACTION: whatsapp("subham", "hello")]'
        tags = parse_action_tags(speech)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0][0]['action'], 'open_app')
        self.assertEqual(tags[0][0]['params']['name'], 'whatsapp')
        self.assertEqual(tags[1][0]['action'], 'whatsapp')
        self.assertEqual(tags[1][0]['params']['contact'], 'subham')
        self.assertEqual(tags[1][0]['params']['message'], 'hello')


class TestInstagramTool(unittest.TestCase):
    def setUp(self):
        self.tool = InstagramTool()

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "instagram_automation")
        self.assertEqual(self.tool.name, "Instagram Direct Automation")
        self.assertIn("send_message", self.tool.parameters_schema["properties"]["action"]["enum"])

    @patch("integrations.instagram.subprocess.run")
    def test_send_direct_message(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)
        res = self.tool.execute({
            "action": "send_message",
            "recipient": "raghav",
            "message": "hello from jarvis"
        })
        self.assertTrue(res.success)
        self.assertIn("raghav", res.data)
        self.assertIn("hello from jarvis", res.data)

    @patch("integrations.instagram.subprocess.run")
    def test_open_profile(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)
        res = self.tool.execute({
            "action": "open_profile",
            "recipient": "divyanshu"
        })
        self.assertTrue(res.success)
        self.assertIn("divyanshu", res.data)


class TestYouTubeUploaderTool(unittest.TestCase):
    def setUp(self):
        self.tool = YouTubeUploaderTool()

    def test_tool_metadata(self):
        self.assertEqual(self.tool.id, "youtube_uploader")
        self.assertEqual(self.tool.name, "YouTube Video Uploader")
        self.assertIn("upload_video", self.tool.parameters_schema["properties"]["action"]["enum"])

    def test_find_video_file_nonexistent(self):
        p = YouTubeUploader.find_video_file("definitely_not_a_real_video_file_99999.mp4")
        self.assertIsNone(p)

    def test_generate_ai_metadata(self):
        meta = YouTubeUploader.generate_ai_metadata("quantum_computing_breakthrough")
        self.assertIn("title", meta)
        self.assertIn("description", meta)
        self.assertIn("tags", meta)
        self.assertTrue(len(meta["title"]) > 5)

    @patch("integrations.youtube.subprocess.run")
    def test_initiate_upload_with_dummy_file(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"0" * 1024)
            dummy_path = Path(f.name)

        try:
            res = YouTubeUploader.initiate_upload(
                video_path=dummy_path,
                title="Test Video Title",
                description="Test Description",
                tags="tech, test"
            )
            self.assertTrue(res["success"])
            self.assertEqual(res["title"], "Test Video Title")
            self.assertIn("studio_url", res)
        finally:
            if dummy_path.exists():
                dummy_path.unlink()


class TestScreenFrameEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_screen_frame_no_data(self):
        res = self.client.post("/api/screen/frame", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))

    def test_screen_frame_valid(self):
        # Create a tiny 1x1 GIF / JPEG payload
        dummy_base64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        res = self.client.post("/api/screen/frame", json={"frame": dummy_base64})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertTrue(os.path.exists(data.get("path")))
        self.assertTrue(screen_awareness.get_status().get("shared_screen_active"))


if __name__ == "__main__":
    unittest.main()
