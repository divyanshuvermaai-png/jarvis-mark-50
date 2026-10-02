"""
J.A.R.V.I.S. WhatsApp Agent - Desktop Controller
Orchestrates macOS native automation using multi-layer fallbacks:
1. JXA Semantic Accessibility Tree (AXUIElement)
2. AppKit Pasteboard & WhatsApp URL schemes
3. Keyboard shortcuts (Cmd+N, Cmd+V, Cmd+Shift+A, Cmd+Shift+V)
4. Graceful fail-safe without blind clicking
"""
import os
import re
import json
import time
import subprocess
import logging
from typing import Dict, Any, List, Optional
from .models import ActionResult, Message, MessageType, CallType
from .contact_resolver import is_phone_number, normalize_phone

logger = logging.getLogger("jarvis.whatsapp.desktop")


class WhatsAppDesktopController:
    """
    Robust, accessibility-first controller for WhatsApp Desktop on macOS.
    """

    def __init__(self):
        self.app_name = "WhatsApp"

    def _run_jxa(self, script_body: str, timeout: int = 15) -> Dict[str, Any]:
        """Runs a JXA snippet against the WhatsApp process."""
        full_script = f"""
        function run() {{
            try {{
                var se = Application("System Events");
                var processes = se.processes.whose({{name: {{"_contains": "WhatsApp"}}}});
                if (processes.length === 0) return JSON.stringify({{error: "WHATSAPP_NOT_RUNNING"}});

                var wa = null;
                for (var i = 0; i < processes.length; i++) {{
                    var name = processes[i].name() || "";
                    if (name.indexOf("AutoFill") === -1) {{
                        wa = processes[i];
                        break;
                    }}
                }}
                if (!wa) return JSON.stringify({{error: "WHATSAPP_NOT_ACCESSIBLE"}});

                {script_body}
            }} catch(e) {{
                return JSON.stringify({{error: e.toString()}});
            }}
        }}
        """
        try:
            res = subprocess.run(
                ['osascript', '-l', 'JavaScript', '-e', full_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if res.returncode != 0:
                logger.debug(f"JXA execution returned non-zero: {res.stderr}")
                return {"error": res.stderr.strip() or "JXA_FAILED"}
            output = res.stdout.strip()
            data = json.loads(output) if output else {}
            err_msg = str(data.get("error", ""))
            if any(k in err_msg.lower() for k in ["not allowed to send keystrokes", "1002", "1719"]):
                data["error"] = "Accessibility permission denied: macOS requires Accessibility permission for Terminal/Python in System Settings > Privacy & Security > Accessibility."
                data["errorCode"] = "ACCESSIBILITY_PERMISSION_DENIED"
            return data
        except subprocess.TimeoutExpired:
            return {"error": "TIMEOUT"}
        except Exception as e:
            return {"error": str(e)}

    def activate_whatsapp(self) -> ActionResult:
        """Brings WhatsApp Desktop to the foreground, launching it if closed."""
        subprocess.run(['open', '-a', 'WhatsApp'], capture_output=True)
        script = """
        tell application "WhatsApp" to activate
        delay 0.4
        tell application "System Events"
            if exists process "WhatsApp" then
                set frontmost of process "WhatsApp" to true
                return "SUCCESS"
            end if
            return "PROCESS_NOT_FOUND"
        end tell
        """
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=8)
            if res.returncode == 0 and "SUCCESS" in res.stdout:
                return ActionResult(success=True, action="activate_whatsapp", message="WhatsApp activated.")
            return ActionResult(success=True, action="activate_whatsapp", message="WhatsApp launched.")
        except Exception as e:
            return ActionResult(success=False, action="activate_whatsapp", error=str(e))

    def open_conversation(self, contact_name: str, phone: Optional[str] = None) -> ActionResult:
        """
        Opens conversation using deep link if phone number available,
        or WhatsApp Cmd+N new chat contact picker.
        """
        self.activate_whatsapp()

        # 1. If phone number or provided in lookup
        target_phone = phone or (contact_name if is_phone_number(contact_name) else None)
        if target_phone:
            norm = normalize_phone(target_phone)
            url = f"whatsapp://send?phone={norm}"
            subprocess.run(['open', url], capture_output=True)
            time.sleep(1.0)
            return ActionResult(
                success=True,
                action="open_conversation",
                data={"contact": contact_name, "phone": norm, "method": "deep_link"},
                message=f"Opened chat with {contact_name}."
            )

        # 2. Search contact via Cmd+N (New Chat)
        script = f"""
        tell application "WhatsApp" to activate
        delay 0.3
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                delay 0.2
                -- Open New Chat dialog via Command + N
                keystroke "n" using command down
                delay 0.4
                keystroke "a" using command down
                delay 0.1
                -- Type contact query
                keystroke {json.dumps(contact_name)}
                delay 0.8
                -- Confirm chat selection
                key code 36 -- Enter
                delay 0.5
            end tell
        end tell
        """
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            err = res.stderr.strip()
            if any(k in err.lower() for k in ["not allowed to send keystrokes", "1002", "1719"]):
                return ActionResult(
                    success=False,
                    action="open_conversation",
                    error="Accessibility permission denied: macOS requires Accessibility permission for Terminal/Python in System Settings > Privacy & Security > Accessibility.",
                    errorCode="ACCESSIBILITY_PERMISSION_DENIED"
                )
            return ActionResult(
                success=True,
                action="open_conversation",
                data={"contact": contact_name, "method": "new_chat_picker"},
                message=f"Opened chat with {contact_name}."
            )
        except Exception as e:
            try:
                from whatsapp_controller.tools import WhatsAppTools
                tools = WhatsAppTools()
                res = tools.messaging.open_chat(contact_name)
                return ActionResult(success=True, action="open_conversation", data=res)
            except Exception:
                return ActionResult(success=False, action="open_conversation", error=str(e))

    def send_message(self, contact_name: str, message: str, phone: Optional[str] = None) -> ActionResult:
        """
        Sends message using clipboard paste (Cmd+V) + Enter for 100% emoji/multiline safety.
        """
        open_res = self.open_conversation(contact_name, phone=phone)
        if not open_res.success:
            return open_res

        # Set clipboard via AppKit / pbcopy
        try:
            from AppKit import NSPasteboard, NSStringPboardType
            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            pb.setString_forType_(message, NSStringPboardType)
        except Exception:
            subprocess.run(['pbcopy'], input=message.encode('utf-8'), capture_output=True)

        script = """
        tell application "WhatsApp" to activate
        delay 0.2
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                keystroke "v" using command down
                delay 0.3
                key code 36 -- Enter
                delay 0.2
            end tell
        end tell
        """
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            logger.info(f"Dispatched WhatsApp message to {contact_name} ({len(message)} chars)")
            return ActionResult(
                success=True,
                action="send_message",
                data={"contact": contact_name, "length": len(message)},
                message=f"Message sent to {contact_name}."
            )
        err = res.stderr.strip()
        if any(k in err.lower() for k in ["not allowed to send keystrokes", "1002", "1719"]):
            return ActionResult(
                success=False,
                action="send_message",
                error="Accessibility permission denied: macOS requires Accessibility permission for Terminal/Python in System Settings > Privacy & Security > Accessibility.",
                errorCode="ACCESSIBILITY_PERMISSION_DENIED"
            )
        return ActionResult(
            success=False,
            action="send_message",
            error=err or "Failed to send keystroke",
            errorCode="SEND_FAILED"
        )

    def initiate_call(self, contact_name: str, call_type: CallType = CallType.VOICE, phone: Optional[str] = None) -> ActionResult:
        """
        Initiates WhatsApp voice or video call via native keyboard shortcuts and JXA bridge.
        """
        open_res = self.open_conversation(contact_name, phone=phone)
        if not open_res.success:
            return open_res

        shortcut_key = "v" if call_type == CallType.VIDEO else "a"
        script = f"""
        tell application "WhatsApp" to activate
        delay 0.4
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                keystroke "{shortcut_key}" using {{command down, shift down}}
                delay 0.5
            end tell
        end tell
        """
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            err = res.stderr.strip()
            if any(k in err.lower() for k in ["not allowed to send keystrokes", "1002", "1719"]):
                return ActionResult(
                    success=False,
                    action="call",
                    error="Accessibility permission denied: macOS requires Accessibility permission for Terminal/Python in System Settings > Privacy & Security > Accessibility.",
                    errorCode="ACCESSIBILITY_PERMISSION_DENIED"
                )
            return ActionResult(
                success=True,
                action="call",
                data={"contact": contact_name, "call_type": call_type.value},
                message=f"Calling {contact_name} on WhatsApp"
            )
        except Exception as e:
            try:
                from whatsapp_controller.tools import WhatsAppTools
                tools = WhatsAppTools()
                c_res = tools.initiate_call(contact_name, video=(call_type == CallType.VIDEO))
                if c_res.get("success"):
                    return ActionResult(
                        success=True,
                        action="call",
                        data={"contact": contact_name, "call_type": call_type.value},
                        message=f"Calling {contact_name} on WhatsApp"
                    )
            except Exception:
                pass
            return ActionResult(success=False, action="call", error=str(e))

    def read_visible_conversation(self, contact_name: str, max_messages: int = 10, phone: Optional[str] = None) -> List[Message]:
        """
        Reads visible messages from active chat via screen OCR fallback and Accessibility elements.
        """
        self.open_conversation(contact_name, phone=phone)
        time.sleep(0.5)

        # Primary attempt: OCR screen capture of the active WhatsApp window
        try:
            from desktop_controller.screen import ScreenController
            cap = ScreenController.capture_window()
            if cap.get("success") and cap.get("data"):
                ocr = ScreenController.ocr_screen(cap["data"])
                if ocr.get("success") and ocr.get("data"):
                    lines = [line.strip() for line in ocr["data"].split("\n") if line.strip()]
                    filtered = [
                        l for l in lines
                        if not re.search(r'(WhatsApp|Chats|Updates|Calls|Communities|Search|Settings|Starred)', l, re.I)
                        and len(l) > 1
                    ]
                    if filtered:
                        return [
                            Message(sender=contact_name, text=txt, is_outgoing=False)
                            for txt in filtered[-max_messages:]
                        ]
        except Exception as e:
            logger.debug(f"OCR message extraction failed: {e}")

        # Fallback: Accessibility elements via JXA
        script = f"""
        var win = wa.windows[0];
        if (!win) return JSON.stringify({{error: "No window found"}});

        var msgs = [];
        function findMessages(el, depth) {{
            if (depth > 8) return;
            try {{
                if (el.role() === "AXStaticText" && el.value()) {{
                    var val = el.value().trim();
                    if (val.length > 0 && !val.match(/^(WhatsApp|Search|Chats|Settings)$/)) {{
                        msgs.push(val);
                    }}
                }}
                var children = el.uiElements();
                for (var i = 0; i < children.length; i++) {{
                    findMessages(children[i], depth + 1);
                }}
            }} catch(e) {{}}
        }}

        findMessages(win, 0);
        return JSON.stringify({{messages: msgs.slice(-{max_messages})}});
        """
        res = self._run_jxa(script)
        extracted = res.get("messages", [])
        return [
            Message(sender=contact_name, text=txt, is_outgoing=False)
            for txt in extracted
        ]
