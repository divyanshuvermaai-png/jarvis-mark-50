with open('/Users/divyanshu/Documents/anti/whatsapp_controller/tools.py', 'r') as f:
    content = f.read()

new_imports = "from whatsapp_controller.actions.media import MediaAction\n"
content = new_imports + content

# Add init hook
content = content.replace("self.resolver = ContactResolver()", "self.resolver = ContactResolver()\n        self.media = MediaAction()")

new_func = """
    def send_media(self, contact_name: str, file_path: str) -> dict:
        try:
            safe_contact = self.resolver.check_ambiguity(contact_name)
            return self.media.send_media(safe_contact, file_path)
        except Exception as e:
            return {"success": False, "status": "error", "error": type(e).__name__, "details": str(e)}
"""
content += new_func

with open('/Users/divyanshu/Documents/anti/whatsapp_controller/tools.py', 'w') as f:
    f.write(content)

with open('/Users/divyanshu/Documents/anti/whatsapp_controller/controller.py', 'r') as f:
    content2 = f.read()

content2 += """
    def send_media(self, contact: str, file_path: str) -> dict:
        return self.tools.send_media(contact, file_path)
"""
with open('/Users/divyanshu/Documents/anti/whatsapp_controller/controller.py', 'w') as f:
    f.write(content2)
