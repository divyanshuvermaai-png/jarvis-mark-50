import subprocess
import time

class KeyboardController:
    """macOS keyboard control using AppleScript."""
    
    # Map of common key names to AppleScript key codes
    KEY_MAP = {
        'return': 36, 'enter': 36, 'tab': 48, 'space': 49,
        'delete': 51, 'escape': 53, 'esc': 53,
        'up': 126, 'down': 125, 'left': 123, 'right': 124,
        'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118, 'f5': 96,
        'f6': 97, 'f7': 98, 'f8': 100, 'f9': 101, 'f10': 109,
        'f11': 103, 'f12': 111,
    }
    
    @staticmethod
    def type_text(text):
        """Type a string of text."""
        escaped = text.replace('\\', '\\\\').replace('"', '\\"')
        script = f'''
        tell application "System Events"
            keystroke "{escaped}"
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
            return {'success': True, 'data': f'Typed: {text[:50]}...'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def press_key(key_name):
        """Press a special key."""
        key_name = key_name.lower().strip()
        key_code = KeyboardController.KEY_MAP.get(key_name)
        if key_code is not None:
            script = f'''
            tell application "System Events"
                key code {key_code}
            end tell
            '''
        else:
            # Try as a single character keystroke
            script = f'''
            tell application "System Events"
                keystroke "{key_name}"
            end tell
            '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': f'Pressed key: {key_name}'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def hotkey(*keys):
        """Press a keyboard shortcut (e.g., hotkey('command', 'c') for copy)."""
        modifier_map = {
            'command': 'command down', 'cmd': 'command down',
            'shift': 'shift down', 'option': 'option down', 'alt': 'option down',
            'control': 'control down', 'ctrl': 'control down',
        }
        
        modifiers = []
        main_key = None
        for k in keys:
            k = k.lower().strip()
            if k in modifier_map:
                modifiers.append(modifier_map[k])
            else:
                main_key = k
        
        if not main_key:
            return {'success': False, 'data': 'No main key specified'}
        
        modifier_str = ', '.join(modifiers)
        if modifier_str:
            script = f'''
            tell application "System Events"
                keystroke "{main_key}" using {{{modifier_str}}}
            end tell
            '''
        else:
            script = f'''
            tell application "System Events"
                keystroke "{main_key}"
            end tell
            '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': f'Hotkey: {" + ".join(keys)}'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
