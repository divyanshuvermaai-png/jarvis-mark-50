with open('/Users/divyanshu/Documents/anti/whatsapp_controller/config.py', 'r') as f:
    content = f.read()

content = content.replace('MODAL_OPEN_DELAY = float(os.getenv("WA_MODAL_OPEN_DELAY", "1.0"))', 'MODAL_OPEN_DELAY = float(os.getenv("WA_MODAL_OPEN_DELAY", "2.0"))')
content = content.replace('SEARCH_TYPE_DELAY = float(os.getenv("WA_SEARCH_TYPE_DELAY", "1.5"))', 'SEARCH_TYPE_DELAY = float(os.getenv("WA_SEARCH_TYPE_DELAY", "2.0"))')
content = content.replace('ACTION_DELAY = float(os.getenv("WA_ACTION_DELAY", "1.5"))', 'ACTION_DELAY = float(os.getenv("WA_ACTION_DELAY", "2.0"))')

with open('/Users/divyanshu/Documents/anti/whatsapp_controller/config.py', 'w') as f:
    f.write(content)
