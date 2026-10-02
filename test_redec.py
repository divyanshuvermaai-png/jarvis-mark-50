from whatsapp_controller.ui_engine.ax_bridge import AXBridge
bridge = AXBridge()
res = bridge.run_jxa('var se = Application("System Events"); se.keystroke("a", {using: ["command down", "shift down"]}); return JSON.stringify({success: true});')
print(res)
