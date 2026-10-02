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
            
        # send a message to subham saying hello
        m = re.match(r'(?:send|message|whatsapp)\s+(?:a\s+message\s+to\s+)?(.+?)(?:\s+(?:on|using)\s+whatsapp)?\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue
            
        # send "hello" to "subham" [on whatsapp]
        m = re.match(r'(?:send|message)\s+(.+?)\s+to\s+(.+?)(?:\s+(?:on|using)\s+whatsapp)?$', clause)
        if m:
            msg_text = m.group(1).strip()
            contact = m.group(2).strip()
            if msg_text == "a message":
                actions.append({'action': 'whatsapp', 'params': {'contact': contact, 'message': ''}})
            else:
                actions.append({'action': 'whatsapp', 'params': {'contact': contact, 'message': msg_text}})
            continue
            
        # whatsapp subham saying hello
        m = re.match(r'(?:whatsapp|message)\s+(.+?)\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue
            
    return actions

print(json.dumps(parse_commands("call subham on whatsapp and send hello to subham on whatsapp and send a message to john saying how are you"), indent=2))
