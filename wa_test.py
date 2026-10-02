import subprocess

def automate_whatsapp(contact, message=None, call=False):
    script = f"""
    tell application "WhatsApp" to activate
    delay 1.5
    tell application "System Events"
        -- Search for contact
        keystroke "f" using command down
        delay 0.5
        keystroke "{contact}"
        delay 1.0
        key code 36 -- Enter to select the contact
        delay 1.0
    """
    
    if call:
        # Audio call shortcut in WhatsApp Desktop is Cmd+Shift+D or Cmd+Shift+A
        # But we can also use menu bar clicking, which is safer if shortcut changes.
        # But for now, let's just trigger Cmd+Shift+D
        script += """
        keystroke "d" using {command down, shift down}
        """
    elif message:
        script += f"""
        keystroke "{message}"
        delay 0.5
        key code 36 -- Enter to send
        """
        
    script += "\nend tell"
    
    proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if proc.returncode != 0:
        if "1002" in proc.stderr or "1719" in proc.stderr:
            return "PERMISSION_DENIED"
        return f"ERROR: {proc.stderr}"
    return "SUCCESS"

print(automate_whatsapp("subham", "hello"))
