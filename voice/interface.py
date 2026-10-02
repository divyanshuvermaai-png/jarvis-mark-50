"""
J.A.R.V.I.S. Voice Interface Coordinator
Integrates Text-to-Speech and Speech-to-Text directly into the Tri-Agent autonomous pipeline.
"""
import logging
import time
from typing import Optional, Tuple
from voice.tts import TextToSpeechEngine
from voice.stt import SpeechToTextEngine
from core.orchestration.orchestrator import AgentOrchestrator
from security.trust import TrustLevel

logger = logging.getLogger("jarvis.voice.interface")

class VoiceInterface:
    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        tts_engine: Optional[TextToSpeechEngine] = None,
        stt_engine: Optional[SpeechToTextEngine] = None
    ):
        self.orchestrator = orchestrator
        self.tts = tts_engine or TextToSpeechEngine()
        self.stt = stt_engine or SpeechToTextEngine()

    def speak(self, text: str, blocking: bool = False):
        """Speak response to the user."""
        self.tts.speak(text, blocking=blocking)

    def listen(self, duration_seconds: float = 5.0) -> str:
        """Listen from the microphone and transcribe."""
        return self.stt.record_and_transcribe(duration_seconds=duration_seconds)

    def interact_turn(self, duration_seconds: float = 5.0) -> Tuple[str, str]:
        """
        Executes one full voice turn:
        1. Listen & transcribe user speech
        2. Execute through Tri-Agent orchestrator
        3. Speak synthesized response back
        Returns (user_text, agent_response).
        """
        user_text = self.listen(duration_seconds=duration_seconds)
        if not user_text.strip():
            return "", ""

        success, response_text, task = self.orchestrator.run(
            objective=user_text,
            trust_level=TrustLevel.LOCAL_OWNER
        )

        self.speak(response_text, blocking=False)
        return user_text, response_text

    def start_interactive_session(self, turn_duration: float = 4.0):
        """
        Runs a continuous, hands-free conversational voice loop.
        Listens, plans, executes tools, and speaks verified responses.
        Exits on Ctrl+C or voice command ('exit', 'goodbye', 'stop').
        """
        print("\n" + "=" * 62)
        print(" J.A.R.V.I.S.  •  HANDS-FREE NEURAL VOICE INTERFACE")
        print(" Engine: Apple Silicon MLX Whisper · Voice: British RyanNeural")
        print(" Address J.A.R.V.I.S. directly. Say 'exit' or press Ctrl+C to quit.")
        print("=" * 62 + "\n")

        # Initial verbal greeting
        try:
            self.speak("J.A.R.V.I.S. neural voice interface active. I am listening, Sir.", blocking=True)
        except Exception as e:
            logger.warning("Greeting speech warning: %s", e)

        while True:
            try:
                print("🎤 [Listening... Speak now]")
                user_text = self.listen(duration_seconds=turn_duration)
                user_text = user_text.strip()

                if not user_text:
                    # Silence or background noise
                    continue

                print(f"👤 [You]: {user_text}")

                # Check for voice exit intent
                cleaned = user_text.lower().rstrip(".!? ")
                if cleaned in ("exit", "quit", "stop", "goodbye", "bye", "shutdown", "go to sleep"):
                    print("🤖 [J.A.R.V.I.S.]: Standing by, Sir. Have a pleasant day.")
                    self.speak("Standing by, Sir. Have a pleasant day.", blocking=True)
                    break

                print("⚡ [J.A.R.V.I.S. Thinking & Planning...]")
                success, response_text, task = self.orchestrator.run(
                    objective=user_text,
                    trust_level=TrustLevel.LOCAL_OWNER
                )

                print(f"🤖 [J.A.R.V.I.S.]: {response_text}\n")
                # Speak response, blocking so microphone does not pick up the AI's own audio
                self.speak(response_text, blocking=True)

            except KeyboardInterrupt:
                print("\n\n🛑 Voice session ended by user.")
                self.tts.stop()
                break
            except Exception as e:
                logger.error(f"Error during voice interaction turn: {e}")
                print(f"⚠️ [Voice Loop Error]: {e}")
