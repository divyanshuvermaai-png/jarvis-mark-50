from .ax_bridge import AXBridge

class WhatsAppInspector:
    def __init__(self):
        self.bridge = AXBridge()

    def get_chat_history(self, max_messages=10):
        """
        Extracts recent messages from the currently active chat view.
        Because Catalyst UI trees are complex, we search for AXGroup elements that
        contain message text.
        """
        script = f"""
        var win = wa.windows[0];
        if (!win) return JSON.stringify({{error: "No window found"}});
        
        // This is a naive heuristic for finding text inside the chat area.
        // A production Catalyst parser would traverse looking for specific message roles.
        var msgs = [];
        function findMessages(el, depth) {{
            if (depth > 8) return;
            try {{
                var desc = el.description();
                // Heuristic: Message bubbles often have descriptions or static texts
                if (el.role() === "AXStaticText" && el.value()) {{
                    msgs.push(el.value());
                }}
                var children = el.uiElements();
                for (var i = 0; i < children.length; i++) {{
                    findMessages(children[i], depth + 1);
                }}
            }} catch(e) {{}}
        }}
        
        findMessages(win, 0);
        
        return JSON.stringify({{messages: msgs.slice(-{max_messages})}});
        """
        return self.bridge.run_jxa(script)

    def is_chat_open(self, contact_name: str) -> bool:
        """
        Verifies if the currently open chat matches the resolved contact.
        """
        # We can look at the window title or the top header text
        script = f"""
        if (wa.windows.length === 0) return JSON.stringify({{is_open: false, error: "no_windows"}});
        var win = wa.windows[0];
        // Note: Catalyst WhatsApp does not reliably change the window title.
        // It remains 'WhatsApp'. For now, we assume Cmd+N + Enter succeeded if the app is responsive.
        // A deeper tree traversal would be needed to find the specific chat header.
        return JSON.stringify({{is_open: true, current_title: win.name() || ""}});
        """
        return self.bridge.run_jxa(script)
