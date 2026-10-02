"""
Apple Suite Plugin for J.A.R.V.I.S.
Integrates directly with native macOS applications using AppleScript.
Supports: Messages (iMessage), Notes, and Mail.
"""
import subprocess
import re
import sys
sys.path.insert(0, '..')
from plugin_system import PluginBase
try:
    from security.action_validator import sanitize_applescript_string
except Exception:
    def sanitize_applescript_string(val: str) -> str:
        return val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

class AppleSuitePlugin(PluginBase):
    name = "apple_suite"
    description = "Control native Apple apps (Messages, Notes, Mail)"
    version = "1.0.0"
    commands = [
        'send imessage', 'imessage',
        'create apple note', 'make an apple note',
        'check apple mail', 'read apple mail',
        'remind me to', 'create reminder', 'add reminder',
        'create a sticky', 'make a sticky', 'sticky note',
        'open spotlight', 'trigger spotlight',
        'trigger siri', 'hey siri'
    ]
    
    def execute(self, message, params=None):
        msg = message.lower().strip()
        
        # Apple Messages (iMessage)
        imessage_match = re.search(r'(?:send imessage|imessage)\s+(?:to\s+)?(.+?)\s+(?:saying|that|with)\s+(.+)', msg)
        if imessage_match:
            contact = imessage_match.group(1).strip()
            content = imessage_match.group(2).strip()
            return self._send_imessage(contact, content)
            
        # Apple Notes
        note_match = re.search(r'(?:create apple note|make an apple note)\s*(?:saying|about)?\s+(.+)', msg)
        if note_match:
            content = note_match.group(1).strip()
            return self._create_apple_note(content)
            
        # Apple Mail
        if 'check apple mail' in msg or 'read apple mail' in msg:
            return self._check_apple_mail()
            
        # Apple Reminders
        remind_match = re.search(r'(?:remind me to|create reminder|add reminder)\s+(.+)', msg)
        if remind_match:
            return self._create_reminder(remind_match.group(1).strip())
            
        # Apple Stickies
        sticky_match = re.search(r'(?:create a sticky|make a sticky|sticky note)(?:\s+(?:saying|with))?\s+(.+)', msg)
        if sticky_match:
            return self._create_sticky(sticky_match.group(1).strip())
            
        # Spotlight & Siri Triggers
        if 'open spotlight' in msg or 'trigger spotlight' in msg:
            return self._trigger_spotlight()
        if 'trigger siri' in msg or 'hey siri' in msg:
            return self._trigger_siri()
            
        return {'success': False, 'response': 'Apple Suite command not fully recognized, sir. Try "send imessage to John saying Hello" or "remind me to buy milk"'}

    def _send_imessage(self, contact, content):
        """Sends an iMessage using AppleScript."""
        safe_contact = sanitize_applescript_string(contact)
        safe_content = sanitize_applescript_string(content)
        script = f'''
        tell application "Messages"
            set targetBuddy to participant "{safe_contact}" of account "iMessage"
            send "{safe_content}" to targetBuddy
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': f"✉️ iMessage sent to {contact.title()}: '{content}'"}
        except Exception as e:
            return {'success': False, 'response': f"Failed to send iMessage. Ensure '{contact}' is an exact match in Contacts or use their phone number."}

    def _create_apple_note(self, content):
        """Creates a note in the native macOS Notes app."""
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
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': f"📝 Created Apple Note: '{content}'"}
        except Exception as e:
            return {'success': False, 'response': f"Failed to create Apple Note: {e}"}

    def _check_apple_mail(self):
        """Fetches the subjects of unread emails in Apple Mail."""
        script = '''
        tell application "Mail"
            set unreadMsgs to (messages of inbox whose read status is false)
            set msgList to ""
            set msgCount to 0
            repeat with msg in unreadMsgs
                if msgCount < 5 then
                    set msgList to msgList & "• " & sender of msg & ": " & subject of msg & "\n"
                end if
                set msgCount to msgCount + 1
            end repeat
            return (msgCount as string) & " unread emails.|" & msgList
        end tell
        '''
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                count_str = parts[0]
                if count_str.startswith("0"):
                    return {'success': True, 'response': "📬 You have no unread emails in Apple Mail, sir."}
                
                details = parts[1] if len(parts) > 1 else ""
                return {'success': True, 'response': f"📬 {count_str}\n\nHere are the latest:\n{details}"}
            else:
                return {'success': False, 'response': "Failed to read Apple Mail. Ensure Mail app is configured."}
        except Exception as e:
            return {'success': False, 'response': f"Error accessing Apple Mail: {e}"}

    def _create_reminder(self, task):
        safe_task = sanitize_applescript_string(task)
        script = f'''
        tell application "Reminders"
            make new reminder with properties {{name:"{safe_task}"}}
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': f"✅ Reminder added: '{task}'"}
        except Exception as e:
            return {'success': False, 'response': f"Failed to create reminder: {e}"}

    def _create_sticky(self, content):
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
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': f"📌 Sticky note created."}
        except Exception as e:
            return {'success': False, 'response': f"Failed to create sticky: {e}"}

    def _trigger_spotlight(self):
        script = 'tell application "System Events" to key code 49 using command down'
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': "🔍 Spotlight opened."}
        except Exception as e:
            return {'success': False, 'response': f"Failed to open Spotlight: {e}"}

    def _trigger_siri(self):
        script = 'tell application "Siri" to activate'
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'response': "🎙️ Siri activated."}
        except Exception as e:
            return {'success': False, 'response': f"Failed to activate Siri: {e}"}
