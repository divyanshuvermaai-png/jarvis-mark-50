"""
J.A.R.V.I.S. Voice & Audio Processing Subsystem
"""
from .tts import TextToSpeechEngine
from .stt import SpeechToTextEngine
from .interface import VoiceInterface

__all__ = [
    "TextToSpeechEngine",
    "SpeechToTextEngine",
    "VoiceInterface"
]
