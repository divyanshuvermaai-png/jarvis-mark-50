with open('/Users/divyanshu/Documents/anti/main.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("                        if not exec_res.get('success', True):"):
        lines[i] = "            if not exec_res.get('success', True):\n"
        break

with open('/Users/divyanshu/Documents/anti/main.py', 'w') as f:
    f.writelines(lines)
