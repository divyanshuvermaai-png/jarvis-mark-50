import re
import json

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    split_regex = r'(?:\s+and\s+|\s+then\s+|\s+along\s+(?:with\s+)?(?:that\s+)?|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp|call)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        # Whatsapp Call
        m = re.match(r'(?:call|phone|ring)\s+(.+?)(?:\s+(?:on|using)\s+whatsapp)?$', clause)
        if m:
            actions.append({'action': 'whatsapp_call', 'params': {'contact': m.group(1).strip()}})
            continue
            
    return actions

print(json.dumps(parse_commands("i said it must send and make calls on whatsapp"), indent=2))
