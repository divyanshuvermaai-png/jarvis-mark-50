import json
import os
import subprocess
import time
from whatsapp_controller.ui_engine.ax_bridge import AXBridge
from whatsapp_controller.actions.messaging import MessagingAction, set_clipboard_text


def set_clipboard_media(filepath: str) -> bool:
    """
    Copies an image or file to the macOS pasteboard so it can be pasted directly
    into WhatsApp Catalyst as an attachment.
    """
    if not os.path.exists(filepath):
        return False

    abs_path = os.path.abspath(filepath)

    # 1. Try PyObjC AppKit (preferred, native macOS pasteboard)
    try:
        from AppKit import NSPasteboard, NSImage, NSURL, NSArray
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()

        url = NSURL.fileURLWithPath_(abs_path)
        ext = os.path.splitext(filepath)[1].lower()

        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heic']:
            image = NSImage.alloc().initWithContentsOfFile_(abs_path)
            if image:
                # Provide both image object and file URL for maximum app compatibility
                pb.writeObjects_(NSArray.arrayWithObjects_(image, url, None))
                return True

        # Provide file URL for documents, videos, and audio
        pb.writeObjects_(NSArray.arrayWithObject_(url))
        return True
    except Exception:
        pass

    # 2. Fallback using osascript
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.png']:
            script = f'set the clipboard to (read (POSIX file "{abs_path}") as «class PNGf»)'
        elif ext in ['.jpg', '.jpeg']:
            script = f'set the clipboard to (read (POSIX file "{abs_path}") as JPEG picture)'
        else:
            script = f'set the clipboard to (POSIX file "{abs_path}")'
        proc = subprocess.run(['osascript', '-e', script], capture_output=True)
        return proc.returncode == 0
    except Exception:
        return False


class MediaAction:
    def __init__(self, bridge: AXBridge):
        self.bridge = bridge
        self.messaging = MessagingAction(bridge)

    def send_media(self, contact_name: str, filepath: str, caption: str = "") -> dict:
        """
        Sends an image, video, or document to the contact via WhatsApp macOS.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found on filesystem.")

        # Step 1: Open chat with contact
        chat_res = self.messaging.open_chat(contact_name)
        if not chat_res.get("success", False):
            return chat_res

        # Step 2: Set media onto macOS pasteboard
        if not set_clipboard_media(filepath):
            return {
                "success": False,
                "status": "error",
                "error": "ClipboardError",
                "details": f"Failed to place '{filepath}' onto macOS pasteboard."
            }

        # Step 3: Paste media into WhatsApp chat (Cmd+V)
        paste_script = """
        wa.frontmost = true;
        delay(0.2);
        
        // Paste media from clipboard
        se.keystroke("v", {using: "command down"});
        delay(0.8);
        return JSON.stringify({success: true, step: "pasted"});
        """
        self.bridge.run_jxa(paste_script)

        # Step 4: Optional caption
        if caption and caption.strip():
            set_clipboard_text(caption.strip())
            caption_script = """
            wa.frontmost = true;
            delay(0.2);
            se.keystroke("v", {using: "command down"});
            delay(0.3);
            return JSON.stringify({success: true, step: "caption_pasted"});
            """
            self.bridge.run_jxa(caption_script)

        # Step 5: Send (Enter key)
        send_script = """
        wa.frontmost = true;
        delay(0.2);
        se.keyCode(36); // Enter key to send media preview
        delay(0.5);
        return JSON.stringify({success: true, step: "sent"});
        """
        self.bridge.run_jxa(send_script)

        return {
            "success": True,
            "status": "completed",
            "contact": contact_name,
            "file": filepath,
            "caption": caption
        }

