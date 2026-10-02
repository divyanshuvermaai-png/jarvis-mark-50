"""
J.A.R.V.I.S. Text-to-Speech (TTS) Engine
High-fidelity neural voice synthesis using edge-tts with native macOS afplay and fallback to say.
Features non-blocking background queue and immediate playback cancellation.
"""
import os
import asyncio
import subprocess
import tempfile
import threading
import queue
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.voice.tts")

DEFAULT_VOICE = "en-GB-RyanNeural"  # Cultured, sophisticated British AI voice
FALLBACK_MACOS_VOICE = "Daniel"

class TextToSpeechEngine:
    def __init__(self, voice_name: str = DEFAULT_VOICE):
        self.voice_name = voice_name
        self._speech_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._current_process: Optional[subprocess.Popen] = None
        self._worker_thread: Optional[threading.Thread] = None

        self._start_worker()

    def _start_worker(self):
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_queue, name="JarvisTTSWorker", daemon=True)
        self._worker_thread.start()

    def speak(self, text: str, blocking: bool = False, voice: Optional[str] = None):
        """
        Synthesizes and speaks the given text.
        If blocking=False, queues the speech request asynchronously.
        """
        text = text.strip()
        if not text:
            return

        selected_voice = voice or self.voice_name

        if blocking:
            self._synthesize_and_play(text, selected_voice)
        else:
            self._speech_queue.put((text, selected_voice))

    def stop(self):
        """
        Immediately halts any currently playing speech and flushes the queue.
        """
        # Clear queue
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except queue.Empty:
                break

        # Terminate active audio process
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
            except Exception:
                pass
            self._current_process = None

    def shutdown(self):
        self.stop()
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def _process_queue(self):
        while not self._stop_event.is_set():
            try:
                text, voice = self._speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                self._synthesize_and_play(text, voice)
            except Exception as e:
                logger.error(f"Error in TTS worker: {e}")
            finally:
                self._speech_queue.task_done()

    def _synthesize_and_play(self, text: str, voice: str):
        # Truncate extremely long outputs for speech comfort
        spoken_text = (text[:400] + "...") if len(text) > 400 else text

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            temp_audio_path = tmp_file.name

        try:
            # 1. Primary: edge-tts (Microsoft Neural)
            try:
                import edge_tts
                async def _gen():
                    communicate = edge_tts.Communicate(spoken_text, voice)
                    await communicate.save(temp_audio_path)
                
                asyncio.run(_gen())

                if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 0:
                    self._current_process = subprocess.Popen(
                        ["/usr/bin/afplay", temp_audio_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self._current_process.wait()
                    return
            except Exception as edge_err:
                logger.warning(f"edge-tts failed, using native macOS say fallback: {edge_err}")

            # 2. Fallback: macOS native say command
            try:
                self._current_process = subprocess.Popen(
                    ["/usr/bin/say", "-v", FALLBACK_MACOS_VOICE, spoken_text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self._current_process.wait()
            except Exception as say_err:
                logger.error(f"Native macOS say command failed: {say_err}")

        finally:
            self._current_process = None
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass
