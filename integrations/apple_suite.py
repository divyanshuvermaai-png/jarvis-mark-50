"""
J.A.R.V.I.S. Apple Suite Integration Tool
Direct AppleScript automation for macOS Messages (iMessage), Notes, Reminders, and Mail.
"""
import subprocess
from typing import Dict, Any
from tools.base import BaseTool, ToolResult
from security.capabilities import Capability, RiskLevel
from security.action_validator import sanitize_applescript_string

class AppleSuiteTool(BaseTool):
    @property
    def id(self) -> str:
        return "apple_suite"

    @property
    def name(self) -> str:
        return "Apple Native Suite"

    @property
    def description(self) -> str:
        return (
            "Automate macOS native applications. "
            "Supports actions: 'imessage' (send iMessage with contact and content), "
            "'note' (create Apple Note with content), "
            "'reminder' (create reminder task), "
            "'mail' (check unread Mail subjects), and "
            "'sticky' (create quick sticky note on desktop)."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["imessage", "note", "reminder", "mail", "sticky"],
                    "description": "The Apple app action to perform."
                },
                "contact": {
                    "type": "string",
                    "description": "Recipient name or phone number (for 'imessage')."
                },
                "content": {
                    "type": "string",
                    "description": "Message or note content (for 'imessage', 'note', 'sticky')."
                },
                "task": {
                    "type": "string",
                    "description": "Reminder task description (for 'reminder')."
                }
            },
            "required": ["action"]
        }

    @property
    def required_capability(self) -> Capability:
        return Capability.APP_CONTROL

    @property
    def risk_tier(self) -> RiskLevel:
        return RiskLevel.MODERATE

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "").lower().strip()

        try:
            if action == "imessage":
                contact = params.get("contact", "").strip()
                content = params.get("content", "").strip()
                if not contact or not content:
                    return ToolResult(success=False, error="Both 'contact' and 'content' are required for iMessage.")
                return self._send_imessage(contact, content)

            elif action == "note":
                content = params.get("content", "").strip()
                if not content:
                    return ToolResult(success=False, error="Parameter 'content' is required for creating an Apple Note.")
                return self._create_note(content)

            elif action == "reminder":
                task = params.get("task") or params.get("content", "").strip()
                if not task:
                    return ToolResult(success=False, error="Parameter 'task' is required for creating a Reminder.")
                return self._create_reminder(task)

            elif action == "mail":
                return self._check_mail()

            elif action == "sticky":
                content = params.get("content", "").strip()
                if not content:
                    return ToolResult(success=False, error="Parameter 'content' is required for Sticky Note.")
                return self._create_sticky(content)

            else:
                return ToolResult(success=False, error=f"Unknown Apple Suite action: '{action}'")

        except Exception as e:
            return ToolResult(success=False, error=f"Apple Suite execution failed: {e}")

    def _send_imessage(self, contact: str, content: str) -> ToolResult:
        safe_contact = sanitize_applescript_string(contact)
        safe_content = sanitize_applescript_string(content)
        script = f'''
        tell application "Messages"
            set targetBuddy to participant "{safe_contact}" of account "iMessage"
            send "{safe_content}" to targetBuddy
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
            return ToolResult(success=True, data=f"iMessage dispatched to '{contact}': {content[:40]}...")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to dispatch iMessage: {e}")

    def _create_note(self, content: str) -> ToolResult:
        safe_content = sanitize_applescript_string(content)
        script = f'''
        tell application "Notes"
            activate
            ignoring application responses
                make new note with properties {{body:"{safe_content}"}}
            end ignoring
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=8)
            return ToolResult(success=True, data=f"Apple Note created: '{content[:50]}...'")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create Apple Note: {e}")

    def _create_reminder(self, task: str) -> ToolResult:
        safe_task = sanitize_applescript_string(task)
        script = f'''
        tell application "Reminders"
            make new reminder with properties {{name:"{safe_task}"}}
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=8)
            return ToolResult(success=True, data=f"Reminder created: '{task}'")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create reminder: {e}")

    def _check_mail(self) -> ToolResult:
        script = '''
        tell application "Mail"
            set unreadMsgs to (messages of inbox whose read status is false)
            set msgCount to count of unreadMsgs
            return (msgCount as string)
        end tell
        '''
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                count_str = res.stdout.strip()
                return ToolResult(success=True, data=f"Apple Mail: {count_str} unread message(s) in inbox.")
            return ToolResult(success=True, data="Apple Mail: 0 unread messages.")
        except Exception as e:
            return ToolResult(success=False, error=f"Error checking Apple Mail: {e}")

    def _create_sticky(self, content: str) -> ToolResult:
        safe_content = sanitize_applescript_string(content)
        script = f'''
        tell application "Stickies"
            activate
            tell application "System Events"
                keystroke "n" using command down
                delay 0.2
                keystroke "{safe_content}"
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=8)
            return ToolResult(success=True, data=f"Sticky note posted: '{content[:40]}...'")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create sticky note: {e}")
