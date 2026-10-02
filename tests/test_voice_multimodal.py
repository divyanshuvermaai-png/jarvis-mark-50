"""
Unit and Integration Tests for J.A.R.V.I.S. Phase 5 Voice & Multimodal Interface:
- TextToSpeechEngine (edge-tts + afplay + say fallback)
- SpeechToTextEngine (MLX Whisper on Apple Silicon)
- VoiceInterface (Hands-free voice pipeline)
"""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import time

from voice.tts import TextToSpeechEngine
from voice.stt import SpeechToTextEngine
from voice.interface import VoiceInterface
from core.orchestration.orchestrator import AgentOrchestrator
from intelligence.router.model_router import ModelRouter
from app.config import JarvisConfig
from tools.registry import ToolRegistry


class TestTextToSpeechEngine(unittest.TestCase):
    def setUp(self):
        self.tts = TextToSpeechEngine()

    def tearDown(self):
        self.tts.shutdown()

    @patch("subprocess.Popen")
    def test_speak_asynchronous_queue(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        self.tts.speak("Good morning, Sir. All systems operational.", blocking=False)
        time.sleep(0.3)
        self.assertTrue(self.tts._speech_queue.empty())

    @patch("subprocess.Popen")
    def test_stop_clears_queue_and_kills_process(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        self.tts._current_process = mock_proc
        self.tts.speak("Long message 1", blocking=False)
        self.tts.speak("Long message 2", blocking=False)

        self.tts.stop()
        self.assertTrue(self.tts._speech_queue.empty())
        mock_proc.terminate.assert_called()


class TestSpeechToTextEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.stt = SpeechToTextEngine()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_transcribe_missing_file_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            self.stt.transcribe_file("/nonexistent/audio.wav")

    @patch("voice.stt.SpeechToTextEngine._load_model")
    def test_transcribe_file(self, mock_load):
        fake_whisper = MagicMock()
        fake_whisper.transcribe.return_value = {"text": "What is the CPU usage?"}
        mock_load.return_value = fake_whisper

        dummy_file = Path(self.test_dir) / "dummy.wav"
        dummy_file.write_bytes(b"RIFFdummywavecontent")

        text = self.stt.transcribe_file(str(dummy_file))
        self.assertEqual(text, "What is the CPU usage?")


class TestVoiceInterface(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        cfg = JarvisConfig(system_name="JARVIS-TEST", version="5.1.0-test")
        self.router = ModelRouter(config=cfg)
        self.tools = ToolRegistry()
        self.orchestrator = AgentOrchestrator(router=self.router, tools=self.tools)

        self.mock_tts = MagicMock()
        self.mock_stt = MagicMock()

        self.voice_iface = VoiceInterface(
            orchestrator=self.orchestrator,
            tts_engine=self.mock_tts,
            stt_engine=self.mock_stt
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_interact_turn(self):
        # Simulate user speech: "hello jarvis"
        self.mock_stt.record_and_transcribe.return_value = "hello jarvis"

        user_input, response = self.voice_iface.interact_turn(duration_seconds=1.0)
        self.assertEqual(user_input, "hello jarvis")
        self.assertTrue(len(response) > 0)
        self.mock_tts.speak.assert_called_once()

    def test_start_interactive_session_exit(self):
        # Simulate user immediately saying "exit"
        self.mock_stt.record_and_transcribe.return_value = "exit"
        self.voice_iface.start_interactive_session(turn_duration=0.1)
        self.assertTrue(self.mock_tts.speak.called)


if __name__ == "__main__":
    unittest.main()
