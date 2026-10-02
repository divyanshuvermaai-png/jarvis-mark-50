import subprocess
import json
import logging
import time

class AXBridge:
    """
    Executes JavaScript for Automation (JXA) scripts via osascript.
    This bypasses Python Accessibility limitations and uses the pre-authorized osascript binary
    to perform ultra-fast, robust semantic querying of the WhatsApp Catalyst UI.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AXBridge")

    def run_jxa(self, script_body: str) -> dict:
        # Start WhatsApp when a command is issued before the app is open.
        subprocess.run(['open', '-a', 'WhatsApp'], capture_output=True, text=True)
        time.sleep(1.5)

        jxa_script = f"""
        function run() {{
            try {{
                var se = Application("System Events");
                var processes = se.processes.whose({{name: {{"_contains": "WhatsApp"}}}});
                if (processes.length === 0) return JSON.stringify({{error: "WhatsApp not running"}});
                
                var wa = null;
                for (var i = 0; i < processes.length; i++) {{
                    var name = processes[i].name() || "";
                    if (name.indexOf("AutoFill") === -1) {{
                        wa = processes[i];
                        break;
                    }}
                }}
                
                if (!wa) return JSON.stringify({{error: "Main WhatsApp process not found"}});
                
                {script_body}
                
            }} catch(e) {{
                return JSON.stringify({{error: e.toString()}});
            }}
        }}
        """
        
        try:
            res = subprocess.run(
                ['osascript', '-l', 'JavaScript', '-e', jxa_script], 
                capture_output=True, text=True, timeout=30
            )
            if res.returncode != 0:
                self.logger.error(f"JXA execution failed: {res.stderr}")
                return {"error": res.stderr}
                
            output = res.stdout.strip()
            return json.loads(output) if output else {}
            
        except subprocess.TimeoutExpired:
            self.logger.error("JXA execution timed out.")
            return {"error": "Timeout"}
        except Exception as e:
            self.logger.error(f"Failed to parse JXA output: {e}")
            return {"error": str(e)}
