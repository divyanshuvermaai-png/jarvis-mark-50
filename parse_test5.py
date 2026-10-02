import re
import json

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    split_regex = r'(?:\s+and\s+|\s+then\s+|\s+along\s+(?:with\s+)?(?:that\s+)?|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
        if not m: m = re.match(r"let'?s?\s+open\s+(.+)", clause)
        if m:
            targets = re.split(r'\s+and\s+|,', m.group(1))
            for t in targets:
                t = t.strip().rstrip('.')
                if t: actions.append({'action': 'open_app', 'params': {'name': t}})
            continue
    return actions

print(json.dumps(parse_commands("open spotify and play tum ho toh along that open whatsapp firefox private window visual studio code canva and calculator"), indent=2))
