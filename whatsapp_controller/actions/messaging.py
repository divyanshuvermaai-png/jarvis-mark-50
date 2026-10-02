import json
import re
import subprocess
import time
from whatsapp_controller.ui_engine.ax_bridge import AXBridge


def set_clipboard_text(text: str) -> bool:
    """Safely copies text into macOS pasteboard for instantaneous and emoji-safe paste."""
    try:
        from AppKit import NSPasteboard, NSStringPboardType
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSStringPboardType)
        return True
    except Exception:
        try:
            proc = subprocess.run(['pbcopy'], input=text.encode('utf-8'), capture_output=True)
            return proc.returncode == 0
        except Exception:
            return False


def is_phone_number(contact: str) -> bool:
    """Checks if a contact identifier is a numeric phone number."""
    cleaned = re.sub(r'[\s\-\(\)\+]', '', contact.strip())
    return cleaned.isdigit() and len(cleaned) >= 7


class MessagingAction:
    def __init__(self, bridge: AXBridge):
        self.bridge = bridge

    def open_chat(self, contact_name: str) -> dict:
        """
        Opens a chat using direct WhatsApp URL scheme if phone number,
        or via Cmd+N contact picker if contact name.
        """
        if is_phone_number(contact_name):
            cleaned = re.sub(r'[\s\-\(\)]', '', contact_name.strip())
            if cleaned.startswith('+'):
                cleaned = cleaned[1:]
            url = f"whatsapp://send?phone={cleaned}"
            subprocess.run(['open', url], capture_output=True)
            time.sleep(1.0)
            return {"success": True, "method": "deep_link", "phone": cleaned}

        script = f"""
        wa.frontmost = true;
        delay(0.1);
        
        // Open WhatsApp's new-chat contact picker.
        se.keystroke("n", {{using: "command down"}});
        delay(0.4);
        se.keystroke("a", {{using: "command down"}});
        delay(0.2);
        se.keystroke({json.dumps(contact_name)});
        delay(1.0);
        se.keyCode(36);
        delay(0.8);
        
        return JSON.stringify({{success: true, method: "contact_picker"}});
        """
        return self.bridge.run_jxa(script)

    def send_text(self, text: str) -> dict:
        """
        Pastes text via clipboard (Cmd+V) and sends with Enter (KeyCode 36).
        Guarantees 100% fidelity for emojis, multiline text, and special symbols.
        """
        if not text:
            return {"success": True, "note": "empty_text_omitted"}

        # Copy text to clipboard for instantaneous paste with full Unicode/Emoji support
        clipboard_ok = set_clipboard_text(text)
        
        if clipboard_ok:
            script = """
            wa.frontmost = true;
            delay(0.1);
            
            // Paste from clipboard
            se.keystroke("v", {using: "command down"});
            delay(0.2);
            se.keyCode(36); // Enter to send
            delay(0.1);
            
            return JSON.stringify({success: true, mode: "clipboard_paste"});
            """
            return self.bridge.run_jxa(script)
        else:
            # Fallback to keystrokes
            safe_text = json.dumps(text)
            script = f"""
            wa.frontmost = true;
            delay(0.1);
            
            se.keystroke({safe_text});
            delay(0.1);
            se.keyCode(36); // Enter
            delay(0.1);
            
            return JSON.stringify({{success: true, mode: "keystroke_fallback"}});
            """
            return self.bridge.run_jxa(script)

