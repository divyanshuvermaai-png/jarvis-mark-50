import re
import json

APP_MAP = {
    'spotify': 'Spotify', 'whatsapp': 'WhatsApp', 'safari': 'Safari',
    'terminal': 'Terminal', 'mail': 'Mail', 'messages': 'Messages',
    'calendar': 'Calendar', 'notes': 'Notes', 'calculator': 'Calculator',
    'maps': 'Maps', 'photos': 'Photos', 'facetime': 'FaceTime', 'music': 'Music',
    'firefox': 'Firefox', 'firefox private window': 'Firefox', 'visual studio code': 'Visual Studio Code',
    'vscode': 'Visual Studio Code', 'canva': 'Canva'
}

def extract_apps(target_str):
    apps_found = []
    # Sort keys by length descending to match longest apps first
    keys = sorted(APP_MAP.keys(), key=len, reverse=True)
    
    # We will search for these keys in the string
    remaining = target_str
    for k in keys:
        if k in remaining:
            apps_found.append(k)
            remaining = remaining.replace(k, ' ') # remove it so we don't double match
            
    if not apps_found:
        # If we didn't find any known apps, just split by "and" and "," and fallback to the original behavior
        targets = re.split(r'\s+and\s+|,', target_str)
        return [t.strip() for t in targets if t.strip()]
        
    return apps_found

print(extract_apps("whatsapp firefox private window visual studio code canva and calculator"))
print(extract_apps("unknown app"))
