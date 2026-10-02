import subprocess
import time
import os

try:
    import Quartz.CoreGraphics as CG
    HAS_QUARTZ = True
except Exception:
    HAS_QUARTZ = False

class MouseController:
    """macOS high-speed native mouse control using Quartz CoreGraphics with AppleScript fallback."""
    
    @staticmethod
    def get_screen_size():
        """Return primary screen width and height in points."""
        if HAS_QUARTZ:
            try:
                w = int(CG.CGDisplayPixelsWide(CG.CGMainDisplayID()))
                h = int(CG.CGDisplayPixelsHigh(CG.CGMainDisplayID()))
                return {'success': True, 'data': {'width': w, 'height': h}}
            except Exception:
                pass
        return {'success': True, 'data': {'width': 1280, 'height': 832}}

    @staticmethod
    def move(x, y):
        """Move mouse to coordinates."""
        if HAS_QUARTZ:
            try:
                pt = CG.CGPoint(float(x), float(y))
                CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                ev = CG.CGEventCreateMouseEvent(src, CG.kCGEventMouseMoved, pt, CG.kCGMouseButtonLeft)
                CG.CGEventPost(CG.kCGHIDEventTap, ev)
                CG.CGEventPost(CG.kCGSessionEventTap, ev)
                return {'success': True, 'data': f'Moved to ({x}, {y})'}
            except Exception as e:
                pass
        
        # Fallback using cliclick
        try:
            subprocess.run(['cliclick', f'm:{x},{y}'], capture_output=True, timeout=2)
            return {'success': True, 'data': f'Moved to ({x}, {y})'}
        except Exception as e:
            return {'success': False, 'data': str(e)}

    @staticmethod
    def drag(x, y):
        """Move mouse while holding left button (dragging)."""
        if HAS_QUARTZ:
            try:
                pt = CG.CGPoint(float(x), float(y))
                CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                ev = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseDragged, pt, CG.kCGMouseButtonLeft)
                CG.CGEventPost(CG.kCGHIDEventTap, ev)
                CG.CGEventPost(CG.kCGSessionEventTap, ev)
                return {'success': True, 'data': f'Dragged to ({x}, {y})'}
            except Exception as e:
                return {'success': False, 'data': str(e)}
        return {'success': False, 'data': 'Quartz required'}

    @staticmethod
    def click(x=None, y=None):
        """Click at screen coordinates (or current position if omitted)."""
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                if x is None or y is None:
                    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    pt = CG.CGPoint(loc.x, loc.y)
                else:
                    pt = CG.CGPoint(float(x), float(y))
                    CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                down = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseDown, pt, CG.kCGMouseButtonLeft)
                up = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseUp, pt, CG.kCGMouseButtonLeft)
                CG.CGEventSetIntegerValueField(down, CG.kCGMouseEventClickState, 1)
                CG.CGEventSetIntegerValueField(up, CG.kCGMouseEventClickState, 1)
                CG.CGEventPost(CG.kCGHIDEventTap, down)
                CG.CGEventPost(CG.kCGSessionEventTap, down)
                time.sleep(0.035)
                CG.CGEventPost(CG.kCGHIDEventTap, up)
                CG.CGEventPost(CG.kCGSessionEventTap, up)
                return {'success': True, 'data': f'Clicked at ({int(pt.x)}, {int(pt.y)})'}
            except Exception as e:
                pass
        
        if x is not None and y is not None:
            script = f'tell application "System Events" to click at {{{x}, {y}}}'
            try:
                subprocess.run(['osascript', '-e', script], capture_output=True, timeout=3)
                return {'success': True, 'data': f'Clicked at ({x}, {y})'}
            except Exception as e:
                return {'success': False, 'data': str(e)}
        return {'success': False, 'data': 'Click failed'}

    @staticmethod
    def right_click(x=None, y=None):
        """Right click at screen coordinates (or current position if omitted)."""
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                if x is None or y is None:
                    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    pt = CG.CGPoint(loc.x, loc.y)
                else:
                    pt = CG.CGPoint(float(x), float(y))
                    CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                down = CG.CGEventCreateMouseEvent(src, CG.kCGEventRightMouseDown, pt, CG.kCGMouseButtonRight)
                up = CG.CGEventCreateMouseEvent(src, CG.kCGEventRightMouseUp, pt, CG.kCGMouseButtonRight)
                CG.CGEventSetIntegerValueField(down, CG.kCGMouseEventClickState, 1)
                CG.CGEventSetIntegerValueField(up, CG.kCGMouseEventClickState, 1)
                CG.CGEventPost(CG.kCGHIDEventTap, down)
                CG.CGEventPost(CG.kCGSessionEventTap, down)
                time.sleep(0.035)
                CG.CGEventPost(CG.kCGHIDEventTap, up)
                CG.CGEventPost(CG.kCGSessionEventTap, up)
                return {'success': True, 'data': f'Right clicked at ({int(pt.x)}, {int(pt.y)})'}
            except Exception as e:
                return {'success': False, 'data': str(e)}
        return {'success': False, 'data': 'Quartz required'}

    @staticmethod
    def mouse_down(x=None, y=None):
        """Mouse left button press down (for dragging)."""
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                if x is None or y is None:
                    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    pt = CG.CGPoint(loc.x, loc.y)
                else:
                    pt = CG.CGPoint(float(x), float(y))
                    CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                down = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseDown, pt, CG.kCGMouseButtonLeft)
                CG.CGEventSetIntegerValueField(down, CG.kCGMouseEventClickState, 1)
                CG.CGEventPost(CG.kCGHIDEventTap, down)
                CG.CGEventPost(CG.kCGSessionEventTap, down)
                return {'success': True, 'data': 'Mouse down'}
            except Exception as e:
                return {'success': False, 'data': str(e)}
        return {'success': False, 'data': 'Quartz required'}

    @staticmethod
    def mouse_up(x=None, y=None):
        """Mouse left button release (end drag)."""
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                if x is None or y is None:
                    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    pt = CG.CGPoint(loc.x, loc.y)
                else:
                    pt = CG.CGPoint(float(x), float(y))
                    CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                up = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseUp, pt, CG.kCGMouseButtonLeft)
                CG.CGEventSetIntegerValueField(up, CG.kCGMouseEventClickState, 1)
                CG.CGEventPost(CG.kCGHIDEventTap, up)
                CG.CGEventPost(CG.kCGSessionEventTap, up)
                return {'success': True, 'data': 'Mouse up'}
            except Exception as e:
                return {'success': False, 'data': str(e)}
        return {'success': False, 'data': 'Quartz required'}

    @staticmethod
    def double_click(x=None, y=None):
        """Double-click at screen coordinates."""
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                if x is None or y is None:
                    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                    pt = CG.CGPoint(loc.x, loc.y)
                else:
                    pt = CG.CGPoint(float(x), float(y))
                    CG.CGDisplayMoveCursorToPoint(CG.CGMainDisplayID(), pt)
                down1 = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseDown, pt, CG.kCGMouseButtonLeft)
                up1 = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseUp, pt, CG.kCGMouseButtonLeft)
                down2 = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseDown, pt, CG.kCGMouseButtonLeft)
                up2 = CG.CGEventCreateMouseEvent(src, CG.kCGEventLeftMouseUp, pt, CG.kCGMouseButtonLeft)
                CG.CGEventSetIntegerValueField(down1, CG.kCGMouseEventClickState, 1)
                CG.CGEventSetIntegerValueField(up1, CG.kCGMouseEventClickState, 1)
                CG.CGEventSetIntegerValueField(down2, CG.kCGMouseEventClickState, 2)
                CG.CGEventSetIntegerValueField(up2, CG.kCGMouseEventClickState, 2)
                CG.CGEventPost(CG.kCGHIDEventTap, down1)
                CG.CGEventPost(CG.kCGSessionEventTap, down1)
                time.sleep(0.025)
                CG.CGEventPost(CG.kCGHIDEventTap, up1)
                CG.CGEventPost(CG.kCGSessionEventTap, up1)
                time.sleep(0.045)
                CG.CGEventPost(CG.kCGHIDEventTap, down2)
                CG.CGEventPost(CG.kCGSessionEventTap, down2)
                time.sleep(0.025)
                CG.CGEventPost(CG.kCGHIDEventTap, up2)
                CG.CGEventPost(CG.kCGSessionEventTap, up2)
                return {'success': True, 'data': f'Double-clicked at ({int(pt.x)}, {int(pt.y)})'}
            except Exception as e:
                pass
        return {'success': False, 'data': 'Double-click failed'}

    @staticmethod
    def scroll(direction='down', amount=3):
        """Scroll up or down."""
        delta = int(amount if direction == 'up' else -amount)
        if HAS_QUARTZ:
            try:
                src = CG.CGEventSourceCreate(CG.kCGEventSourceStateCombinedSessionState)
                ev = CG.CGEventCreateScrollWheelEvent(src, CG.kCGScrollEventUnitLine, 1, delta)
                CG.CGEventPost(CG.kCGHIDEventTap, ev)
                CG.CGEventPost(CG.kCGSessionEventTap, ev)
                return {'success': True, 'data': f'Scrolled {direction} by {amount}'}
            except Exception as e:
                pass
        return {'success': False, 'data': 'Scroll failed'}

    @staticmethod
    def get_position():
        """Get current mouse position."""
        if HAS_QUARTZ:
            try:
                loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
                return {'success': True, 'data': {'x': int(loc.x), 'y': int(loc.y)}}
            except Exception:
                pass
        return {'success': False, 'data': 'Could not get mouse position'}
