import re

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    split_regex = r'(?:\s+and\s+|\s+then\s+|\s+along\s+(?:with\s+)?(?:that\s+)?|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp|call|video call|audio call)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        # WhatsApp Call parsing
        m_call = re.match(r'(?:call|audio call|video call)\s+(.+?)(?:\s+on\s+whatsapp)?$', clause)
        if m_call:
            video = 'video' in clause
            actions.append({'action': 'whatsapp_call', 'params': {'contact': m_call.group(1).strip(), 'video': video}})
            continue
            
        # WhatsApp Message parsing with explicit message
        m_msg = re.match(r'(?:send\s+a?\s*message\s+to|message|whatsapp)\s+(.+?)\s+(?:on|using)?\s*whatsapp\s+(?:saying|that|with)\s+(.+)', clause)
        if not m_msg:
             m_msg = re.match(r'(?:whatsapp|message)\s+(.+?)\s+(?:saying|that|with)\s+(.+)', clause)
        
        if m_msg: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m_msg.group(1).strip(), 'message': m_msg.group(2).strip()}})
            continue
            
        # WhatsApp Message without explicit message payload
        m_msg_empty = re.match(r'(?:send\s+a?\s*message\s+to|message|whatsapp)\s+(.+?)(?:\s+on\s+whatsapp)?$', clause)
        if m_msg_empty:
             actions.append({'action': 'whatsapp', 'params': {'contact': m_msg_empty.group(1).strip(), 'message': ''}})
             continue
             
        # Read Chat parsing
        m_read = re.match(r'(?:read|check)\s+(?:my\s+)?(?:chat|messages)\s+(?:with|from)\s+(.+?)(?:\s+on\s+whatsapp)?$', clause)
        if m_read:
             actions.append({'action': 'whatsapp_read', 'params': {'contact': m_read.group(1).strip()}})
             continue
             
        print(f"Clause fell through: {clause}")
