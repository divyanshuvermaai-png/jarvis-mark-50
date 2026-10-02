import re

with open('main.py', 'r') as f:
    content = f.read()

# Add missing apps to APP_MAP
new_map = """APP_MAP = {
    'spotify': 'Spotify', 'whatsapp': 'WhatsApp', 'safari': 'Safari',
    'terminal': 'Terminal', 'mail': 'Mail', 'messages': 'Messages',
    'calendar': 'Calendar', 'notes': 'Notes', 'calculator': 'Calculator',
    'maps': 'Maps', 'photos': 'Photos', 'facetime': 'FaceTime', 'music': 'Music',
    'firefox': 'Firefox', 'firefox private window': 'Firefox', 'visual studio code': 'Visual Studio Code',
    'vscode': 'Visual Studio Code', 'canva': 'Canva',
    'keynote': 'Keynote', 'pages': 'Pages', 'numbers': 'Numbers',
    'weather': 'Weather', 'stocks': 'Stocks', 'journal': 'Journal',
    'reminders': 'Reminders', 'stickies': 'Stickies', 'image capture': 'Image Capture',
    'photo booth': 'Photo Booth', 'clock': 'Clock', 'siri': 'Siri'
}"""

content = re.sub(r'APP_MAP = \{.*?\n\}', new_map, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)

print("Patched APP_MAP")
