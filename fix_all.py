import re

files = [
    '/Users/divyanshu/Documents/anti/whatsapp_controller/actions/calling.py',
    '/Users/divyanshu/Documents/anti/whatsapp_controller/actions/messaging.py',
    '/Users/divyanshu/Documents/anti/whatsapp_controller/actions/media.py'
]

for file in files:
    with open(file, 'r') as f:
        content = f.read()
        
    # Standardize the chat opening block to use Double Enter reliably
    pattern = r'se\.keyCode\(125\);.*?delay\(.*?\);.*?se\.keyCode\(36\);[^\n]*\n.*?delay\(\{WhatsAppConfig\.ACTION_DELAY\}\);'
    replacement = r'''se.keyCode(125); // Down Arrow
            delay(0.5);
            se.keyCode(36); // Enter (Focus)
            delay(0.5);
            se.keyCode(36); // Enter (Open)
            delay({WhatsAppConfig.ACTION_DELAY});'''
            
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Fix the sending block if I messed it up with double enter
    content = content.replace('se.keyCode(36); // Enter\n            delay(0.5);\n            se.keyCode(36); // Enter to send', 'se.keyCode(36); // Enter to send')
    
    with open(file, 'w') as f:
        f.write(content)
