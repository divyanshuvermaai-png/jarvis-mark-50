import re
clause = "open whatsapp , firefox private window , visual studio code , canva and calculator"
m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
if m:
    targets = re.split(r'\s+and\s+|,', m.group(1))
    print(targets)
