import json
from whatsapp_controller.ui_engine.ax_bridge import AXBridge

class CallingAction:
    def __init__(self, bridge: AXBridge):
        self.bridge = bridge

    def initiate_call(self, contact_name: str, video: bool = False) -> dict:
        """
        Searches for the contact, opens their chat, and presses the call shortcut.
        All in one atomic JXA script for maximum reliability.
        """
        shortcut = "v" if video else "a"
        
        script = f"""
        wa.frontmost = true;
        delay(0.1);
        
        // Open the contact picker, select the first matching contact, and call.
        se.keystroke("n", {{using: "command down"}});
        delay(0.4);
        se.keystroke("a", {{using: "command down"}});
        delay(0.2);
        se.keystroke({json.dumps(contact_name)});
        delay(1.0);
        se.keyCode(36);
        delay(0.8);
        se.keystroke("{shortcut}", {{using: ["command down", "shift down"]}});
        delay(0.5);
        return JSON.stringify({{success: true, contact: {json.dumps(contact_name)}, video: {str(video).lower()}}});
        """
        
        return self.bridge.run_jxa(script)
