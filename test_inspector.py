from whatsapp_controller.ui_engine.inspector import WhatsAppInspector
import json
inspector = WhatsAppInspector()
res = inspector.is_chat_open('subham')
print(json.dumps(res, indent=2))
