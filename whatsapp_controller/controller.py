from .tools import WhatsAppTools

class WhatsAppController:
    """Legacy backward-compatible wrapper for main.py."""
    def __init__(self):
        self.tools = WhatsAppTools()

    def send_message(self, contact: str, message: str) -> dict:
        return self.tools.send_message(contact, message)

    def initiate_call(self, contact: str, video: bool = False) -> dict:
        return self.tools.initiate_call(contact, video)

    def read_chat(self, contact: str) -> dict:
        return self.tools.read_chat(contact)

    def send_media(self, contact: str, file_path: str, caption: str = "") -> dict:
        return self.tools.send_media(contact, file_path, caption=caption)

