"""
J.A.R.V.I.S. Speech-to-Text (STT) Engine
High-accuracy on-device speech transcription using Apple Silicon MLX Whisper.
Captures microphone audio via Core Audio (sounddevice) and transcribes locally.
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger("jarvis.voice.stt")

DEFAULT_WHISPER_MODEL = "mlx-community/whisper-tiny"

class SpeechToTextEngine:
    def __init__(self, model_name: str = DEFAULT_WHISPER_MODEL):
        self.model_name = model_name
        self._mlx_whisper = None

    def _load_model(self):
        if self._mlx_whisper is None:
            try:
                import mlx_whisper
                self._mlx_whisper = mlx_whisper
            except ImportError:
                logger.error("mlx_whisper is not installed.")
                raise RuntimeError("mlx_whisper is not installed.")
        return self._mlx_whisper

    def transcribe_file(self, audio_path: str, language: str = "en") -> str:
        """
        Transcribes a WAV or MP3 audio file using MLX Whisper on Apple Silicon.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file '{audio_path}' not found.")

        whisper = self._load_model()
        try:
            result = whisper.transcribe(
                audio_path,
                path_or_hf_repo=self.model_name,
                language=language,
                word_timestamps=False
            )
            return result.get("text", "").strip()
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def record_and_transcribe(self, duration_seconds: float = 5.0, sample_rate: int = 16000) -> str:
        """
        Record audio from the default microphone and transcribe via MLX Whisper.
        """
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wav
        except ImportError as err:
            logger.error(f"Audio recording dependencies missing: {err}")
            return ""

        logger.info(f"Recording {duration_seconds} seconds of audio...")
        try:
            recording = sd.rec(
                int(duration_seconds * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16"
            )
            sd.wait()

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                tmp_path = tmp_wav.name

            try:
                wav.write(tmp_path, sample_rate, recording)
                return self.transcribe_file(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Failed to record and transcribe: {e}")
            return ""
