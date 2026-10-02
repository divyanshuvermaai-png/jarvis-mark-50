import subprocess
import os
import json
from .config import WhatsAppConfig
from .errors import WhatsAppPermissionError, ActionTimeoutError

class MacOSAutomation:
    """Handles the native macOS UI scripting for WhatsApp."""
    
    @staticmethod
    def _run_applescript(script: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                ['osascript', '-e', script], 
                capture_output=True, 
                text=True,
                timeout=WhatsAppConfig.TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired:
            raise ActionTimeoutError("AppleScript execution timed out.")
            
    def activate_whatsapp(self):
        script = f'tell application "{WhatsAppConfig.APP_NAME}" to activate\ndelay {WhatsAppConfig.APP_LAUNCH_DELAY}'
        res = self._run_applescript(script)
        if res.returncode != 0:
            raise Exception(f"Failed to activate WhatsApp: {res.stderr}")

    def execute_contact_action(self, contact: str, action_type: str, message: str = None):
        """
        Executes a sequence of keystrokes to search for a contact and perform an action.
        action_type can be 'audio_call', 'video_call', or 'message'.
        """
        
        # Base script: activate app, open new chat, type name, hit enter
        script = f"""
        tell application "{WhatsAppConfig.APP_NAME}" to activate
        delay {WhatsAppConfig.APP_LAUNCH_DELAY}
        tell application "System Events"
            -- Open new chat search globally
            keystroke "n" using command down
            delay {WhatsAppConfig.MODAL_OPEN_DELAY}
            keystroke "{contact}"
            delay {WhatsAppConfig.SEARCH_TYPE_DELAY}
            key code 36
            delay {WhatsAppConfig.ACTION_DELAY}
        """
        
        # Append specific action logic
        if action_type == "audio_call":
            script += '\nkeystroke "a" using {command down, shift down}'
        elif action_type == "video_call":
            script += '\nkeystroke "v" using {command down, shift down}'
        elif action_type == "message" and message:
            # We replace double quotes to prevent AppleScript injection/syntax errors
            safe_msg = message.replace('"', '\\"')
            script += f'\nkeystroke "{safe_msg}"\ndelay 0.5\nkey code 36'
            
        script += "\nend tell"
        
        res = self._run_applescript(script)
        
        # Handle specific macOS Accessibility Permission errors (1002 and -1719)
        if res.returncode != 0:
            if "1002" in res.stderr or "1719" in res.stderr:
                raise WhatsAppPermissionError("Accessibility permissions denied. Cannot simulate keystrokes.")
            else:
                raise Exception(f"AppleScript Error: {res.stderr}")
                
        return True
