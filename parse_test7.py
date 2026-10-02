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
    final_targets = []
    parts = re.split(r'\s+and\s+|,', target_str)
    keys = sorted(APP_MAP.keys(), key=len, reverse=True)
    
    for p in parts:
        p = p.strip()
        if not p: continue
        
        found_in_part = []
        temp = p
        for k in keys:
            # We want to match whole words or exact substrings, but `k in temp` is fine since app names are distinct
            idx = temp.find(k)
            while idx != -1:
                found_in_part.append((idx, k))
                temp = temp[:idx] + ' ' * len(k) + temp[idx+len(k):]
                idx = temp.find(k)
                
        if len(found_in_part) > 1:
            found_in_part.sort()
            for pos, k in found_in_part:
                final_targets.append(k)
        else:
            final_targets.append(p)
            
    return final_targets

print(extract_apps("whatsapp firefox private window visual studio code canva and calculator"))
print(extract_apps("zoom and whatsapp and some unknown app"))
print(extract_apps("spotify whatsapp"))
