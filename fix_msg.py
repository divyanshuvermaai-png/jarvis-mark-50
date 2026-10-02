with open('/Users/divyanshu/Documents/anti/whatsapp_controller/actions/messaging.py', 'r') as f:
    content = f.read()

content = content.replace('se.keyCode(125); // Down Arrow\n            delay(0.5);\n            se.keyCode(36); // Enter to send', 'se.keyCode(36); // Enter to send')

with open('/Users/divyanshu/Documents/anti/whatsapp_controller/actions/messaging.py', 'w') as f:
    f.write(content)
