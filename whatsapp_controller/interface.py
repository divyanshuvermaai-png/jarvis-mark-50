from abc import ABC, abstractmethod

class CommunicationProvider(ABC):
    @abstractmethod
    def send_message(self, contact: str, message: str) -> dict:
        """Sends a message to the specified contact."""
        pass

    @abstractmethod
    def initiate_call(self, contact: str, video: bool = False) -> dict:
        """Initiates an audio or video call."""
        pass
