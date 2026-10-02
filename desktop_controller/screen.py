import subprocess
import os
import tempfile

class ScreenController:
    """macOS screen capture and OCR."""
    
    @staticmethod
    def capture_full(save_path=None):
        """Capture the entire screen."""
        if not save_path:
            save_path = os.path.join(tempfile.gettempdir(), 'jarvis_screen.png')
        try:
            subprocess.run(['screencapture', '-x', save_path], capture_output=True, timeout=10)
            if os.path.exists(save_path):
                return {'success': True, 'data': save_path}
            return {'success': False, 'data': 'Screenshot failed'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def capture_region(x, y, w, h, save_path=None):
        """Capture a specific screen region."""
        if not save_path:
            save_path = os.path.join(tempfile.gettempdir(), 'jarvis_region.png')
        try:
            subprocess.run(['screencapture', '-x', '-R', f'{x},{y},{w},{h}', save_path], 
                         capture_output=True, timeout=10)
            if os.path.exists(save_path):
                return {'success': True, 'data': save_path}
            return {'success': False, 'data': 'Region capture failed'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def capture_window(save_path=None):
        """Capture the front window."""
        if not save_path:
            save_path = os.path.join(tempfile.gettempdir(), 'jarvis_window.png')
        try:
            subprocess.run(['screencapture', '-x', '-w', save_path], capture_output=True, timeout=10)
            if os.path.exists(save_path):
                return {'success': True, 'data': save_path}
            return {'success': False, 'data': 'Window capture failed'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod
    def ocr_screen(image_path=None):
        """Extract text from screen using macOS Vision framework."""
        if not image_path:
            # Capture screen first
            result = ScreenController.capture_full()
            if not result['success']:
                return result
            image_path = result['data']
        
        # Use macOS built-in Foundation & Vision framework for native Apple Silicon OCR
        script = f'''
        use framework "Foundation"
        use framework "Vision"
        
        set fileURL to current application's |NSURL|'s fileURLWithPath:"{image_path}"
        set requestHandler to current application's VNImageRequestHandler's alloc()'s initWithURL:fileURL options:(current application's NSDictionary's dictionary())
        
        set ocrRequest to current application's VNRecognizeTextRequest's alloc()'s init()
        ocrRequest's setRecognitionLevel:(current application's VNRequestTextRecognitionLevelAccurate)
        
        requestHandler's performRequests:({{ocrRequest}}) |error|:(missing value)
        
        set ocrResults to ocrRequest's results()
        set extractedText to ""
        
        repeat with observation in ocrResults
            set topCandidate to (observation's topCandidates:1)'s firstObject()
            if topCandidate is not missing value then
                set extractedText to extractedText & (topCandidate's |string|() as text) & linefeed
            end if
        end repeat
        
        return extractedText
        '''
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return {'success': True, 'data': result.stdout.strip()}
            return {'success': False, 'data': 'OCR returned no text'}
        except Exception as e:
            return {'success': False, 'data': str(e)}
    
    @staticmethod 
    def get_screen_size():
        """Get the screen resolution."""
        script = '''
        tell application "Finder"
            set _bounds to bounds of window of desktop
            return (item 3 of _bounds as text) & "x" & (item 4 of _bounds as text)
        end tell
        '''
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            return {'success': True, 'data': result.stdout.strip()}
        except Exception as e:
            return {'success': False, 'data': str(e)}
