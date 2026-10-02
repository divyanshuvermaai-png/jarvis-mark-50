"""
Test suite for J.A.R.V.I.S. Continuous Screen Awareness Engine and Voice Transcribe Endpoint.
"""
import io
import unittest
from unittest.mock import patch, MagicMock

from core.screen_awareness import ScreenAwarenessEngine, screen_awareness
from main import app

class TestScreenAwarenessEngine(unittest.TestCase):
    def setUp(self):
        self.engine = screen_awareness
        self.engine.toggle(True)

    def test_singleton(self):
        engine2 = ScreenAwarenessEngine()
        self.assertIs(self.engine, engine2)

    def test_toggle(self):
        self.assertFalse(self.engine.toggle(False))
        self.assertFalse(self.engine.enabled)
        self.assertTrue(self.engine.toggle(True))
        self.assertTrue(self.engine.enabled)

    def test_get_status(self):
        status = self.engine.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn("monitoring", status)
        self.assertIn("active_app", status)
        self.assertIn("watching_summary", status)

    def test_synthesize_watching_summary_youtube(self):
        summary = self.engine._synthesize_watching_summary(
            app="Google Chrome",
            window="Iron Man HUD in Real Life - YouTube",
            url="https://www.youtube.com/watch?v=12345",
            tab_title="Iron Man HUD in Real Life - YouTube"
        )
        self.assertIn("Watching YouTube video", summary)
        self.assertIn("Iron Man HUD in Real Life", summary)

    def test_synthesize_watching_summary_coding(self):
        summary = self.engine._synthesize_watching_summary(
            app="Visual Studio Code",
            window="screen_awareness.py",
            url="",
            tab_title=""
        )
        self.assertIn("Coding in Visual Studio Code", summary)

    def test_synthesize_watching_summary_terminal(self):
        summary = self.engine._synthesize_watching_summary(
            app="Terminal",
            window="zsh - python3",
            url="",
            tab_title=""
        )
        self.assertIn("Working in command line Terminal", summary)

    def test_synthesize_watching_summary_whatsapp(self):
        summary = self.engine._synthesize_watching_summary(
            app="WhatsApp",
            window="Tony Stark",
            url="",
            tab_title=""
        )
        self.assertIn("Communicating on WhatsApp", summary)

    def test_synthesize_watching_summary_generic_browsing(self):
        summary = self.engine._synthesize_watching_summary(
            app="Safari",
            window="Apple Developer Documentation",
            url="https://developer.apple.com",
            tab_title="Apple Developer Documentation"
        )
        self.assertIn("Browsing 'Apple Developer Documentation'", summary)

    def test_get_perception_context(self):
        ctx = self.engine.get_perception_context()
        self.assertIn("Foreground App", ctx)
        self.assertIn("User Screen Activity", ctx)

        # When disabled
        self.engine.toggle(False)
        disabled_ctx = self.engine.get_perception_context()
        self.assertIn("Standby", disabled_ctx)
        self.engine.toggle(True)


class TestScreenAndVoiceEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_screen_status_endpoint(self):
        res = self.client.get("/api/screen/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("monitoring", data)
        self.assertIn("active_app", data)

    def test_screen_toggle_endpoint(self):
        # Explicit toggle to False
        res = self.client.post("/api/screen/toggle", json={"enabled": False})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data.get("monitoring"))

        # Explicit toggle to True
        res2 = self.client.post("/api/screen/toggle", json={"enabled": True})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertTrue(data2.get("monitoring"))

    def test_screen_refresh_endpoint(self):
        with patch.object(screen_awareness, "force_refresh", return_value={"watching_summary": "Testing display"}):
            res = self.client.post("/api/screen/refresh")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("state", {}).get("watching_summary"), "Testing display")

    def test_voice_transcribe_no_file(self):
        res = self.client.post("/api/voice/transcribe")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))

    @patch("voice.stt.SpeechToTextEngine.transcribe_file")
    @patch("subprocess.run")
    def test_voice_transcribe_success(self, mock_subproc, mock_transcribe_file):
        mock_subproc.return_value = MagicMock(returncode=0)
        mock_transcribe_file.return_value = "what am I watching on my screen"

        audio_file = (io.BytesIO(b"RIFFdummywavecontent"), "audio.wav")
        res = self.client.post(
            "/api/voice/transcribe",
            data={"audio": audio_file},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("text"), "what am I watching on my screen")


if __name__ == "__main__":
    unittest.main()
