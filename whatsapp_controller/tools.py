from whatsapp_controller.actions.media import MediaAction
from whatsapp_controller.actions.messaging import MessagingAction
from whatsapp_controller.actions.calling import CallingAction
from whatsapp_controller.ui_engine.inspector import WhatsAppInspector
from whatsapp_controller.contact_resolver import ContactResolver
from whatsapp_controller.ui_engine.ax_bridge import AXBridge


def _ensure_success(result: dict) -> dict:
    if result.get("error") or result.get("success") is False:
        raise RuntimeError(result.get("error") or "WhatsApp action was not completed")
    return result

class WhatsAppTools:
    """Structured action layer for Jarvis NL reasoning."""
    def __init__(self):
        self.bridge = AXBridge()
        self.messaging = MessagingAction(self.bridge)
        self.calling = CallingAction(self.bridge)
        self.inspector = WhatsAppInspector()
        self.resolver = ContactResolver()
        self.media = MediaAction(self.bridge)

    def send_message(self, contact_name: str, message: str) -> dict:
        try:
            safe_contact = self.resolver.check_ambiguity(contact_name)
            _ensure_success(self.messaging.open_chat(safe_contact))
            result = _ensure_success(self.messaging.send_text(message))
            return {**result, "success": True, "status": "completed", "contact": safe_contact}
        except Exception as e:
            return {"success": False, "status": "error", "error": type(e).__name__, "details": str(e)}

    def initiate_call(self, contact_name: str, video: bool = False) -> dict:
        try:
            safe_contact = self.resolver.check_ambiguity(contact_name)
            result = _ensure_success(self.calling.initiate_call(safe_contact, video))
            return {**result, "success": True, "status": "completed", "contact": safe_contact}
        except Exception as e:
            return {"success": False, "status": "error", "error": type(e).__name__, "details": str(e)}

    def read_chat(self, contact_name: str, max_messages: int = 10) -> dict:
        try:
            safe_contact = self.resolver.check_ambiguity(contact_name)
            # Open chat
            _ensure_success(self.messaging.open_chat(safe_contact))
            return _ensure_success(self.inspector.get_chat_history(max_messages))
        except Exception as e:
            return {"success": False, "status": "error", "error": type(e).__name__, "details": str(e)}

    def send_media(self, contact_name: str, file_path: str, caption: str = "") -> dict:
        try:
            safe_contact = self.resolver.check_ambiguity(contact_name)
            result = _ensure_success(self.media.send_media(safe_contact, file_path, caption=caption))
            return {**result, "success": True, "status": "completed", "contact": safe_contact, "file": file_path}
        except Exception as e:
            return {"success": False, "status": "error", "error": type(e).__name__, "details": str(e)}

