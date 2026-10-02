import subprocess
import json

class WindowController:
    """macOS window management using AppleScript."""
    
    @staticmethod
    def get_frontmost_app():
        """Get the name of the frontmost application."""
        script = 'tell application "System Events" to return name of first application process whose frontmost is true'
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            return {'success': True, 'data': result.stdout.strip()}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def focus_app(app_name):
        """Bring an app to the front."""
        script = f'tell application "{app_name}" to activate'
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': f'Focused: {app_name}'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def resize_window(app_name, width, height):
        """Resize the front window of an app."""
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set size of front window to {{{width}, {height}}}
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': f'Resized {app_name} to {width}x{height}'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def move_window(app_name, x, y):
        """Move the front window of an app."""
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set position of front window to {{{x}, {y}}}
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': f'Moved {app_name} to ({x}, {y})'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def snap_window(position='left'):
        """Snap the front window to left/right/maximize."""
        script_map = {
            'left': '''
                tell application "Finder" to set _bounds to bounds of window of desktop
                set _w to item 3 of _bounds
                set _h to item 4 of _bounds
                tell application "System Events"
                    set _proc to first application process whose frontmost is true
                    tell _proc
                        set position of front window to {0, 25}
                        set size of front window to {_w / 2, _h - 25}
                    end tell
                end tell
            ''',
            'right': '''
                tell application "Finder" to set _bounds to bounds of window of desktop
                set _w to item 3 of _bounds
                set _h to item 4 of _bounds
                tell application "System Events"
                    set _proc to first application process whose frontmost is true
                    tell _proc
                        set position of front window to {_w / 2, 25}
                        set size of front window to {_w / 2, _h - 25}
                    end tell
                end tell
            ''',
            'maximize': '''
                tell application "Finder" to set _bounds to bounds of window of desktop
                set _w to item 3 of _bounds
                set _h to item 4 of _bounds
                tell application "System Events"
                    set _proc to first application process whose frontmost is true
                    tell _proc
                        set position of front window to {0, 25}
                        set size of front window to {_w, _h - 25}
                    end tell
                end tell
            ''',
        }
        script = script_map.get(position, script_map['maximize'])
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
            return {'success': True, 'data': f'Window snapped to {position}'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def minimize_window():
        """Minimize the front window."""
        script = '''
        tell application "System Events"
            set _proc to first application process whose frontmost is true
            tell _proc
                set miniaturized of front window to true
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': 'Window minimized'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def close_window():
        """Close the front window."""
        script = '''
        tell application "System Events"
            set _proc to first application process whose frontmost is true
            tell _proc
                click button 1 of front window
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {'success': True, 'data': 'Window closed'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def list_windows():
        """List all open windows."""
        script = '''
        set output to ""
        tell application "System Events"
            set _procs to every application process whose visible is true
            repeat with _p in _procs
                try
                    set _name to name of _p
                    set _wins to name of every window of _p
                    repeat with _w in _wins
                        set output to output & _name & " | " & _w & linefeed
                    end repeat
                end try
            end repeat
        end tell
        return output
        '''
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            windows = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return {'success': True, 'data': windows}
        except Exception as e:
            return {'success': False, 'data': str(e)}
