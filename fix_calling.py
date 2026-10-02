with open('/Users/divyanshu/Documents/anti/whatsapp_controller/actions/calling.py', 'r') as f:
    content = f.read()

content = content.replace('var se = Application("System Events");\n', '')

with open('/Users/divyanshu/Documents/anti/whatsapp_controller/actions/calling.py', 'w') as f:
    f.write(content)
