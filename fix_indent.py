with open('/Users/divyanshu/Documents/anti/main.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("                if action == 'whatsapp' or action == 'whatsapp_call' or action == 'whatsapp_read':"):
        lines[i] = "        if action == 'whatsapp' or action == 'whatsapp_call' or action == 'whatsapp_read':\n"
        break

with open('/Users/divyanshu/Documents/anti/main.py', 'w') as f:
    f.writelines(lines)
