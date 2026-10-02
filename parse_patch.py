import re

with open('/Users/divyanshu/Documents/anti/main.py', 'r') as f:
    content = f.read()

new_parse_commands = """def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    
    split_regex = r'(?:\\s+and\\s+|\\s+then\\s+|\\s+along\\s+(?:with\\s+)?(?:that\\s+)?|,\\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp|call|video call|audio call)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        if any(k in clause for k in ['look at my screen', "what's on my screen", 'read my screen', 'see this', 'what am i looking at']):
            actions.append({'action': 'analyze_screen'})
            continue
            
        if clause in ('play music', 'play', 'resume'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'play'}})
            continue
        if clause in ('pause music', 'pause', 'stop music', 'stop'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'pause'}})
            continue
        if clause in ('next track', 'next song', 'skip'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'next track'}})
            continue
        if clause in ('previous track', 'previous song', 'back'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'previous track'}})
            continue
            
        m = re.match(r'(?:play|listen to)\\s+(.+?)(?:\\s+on\\s+spotify)?$', clause)
        if m:
            song = m.group(1).strip()
            if song not in ('music', 'pause', 'stop', 'next', 'previous'):
                actions.append({'action': 'play_song', 'params': {'song': song}})
            continue
            
        # WhatsApp Call parsing
        m_call = re.match(r'(?:call|audio call|video call)\\s+(.+?)(?:\\s+on\\s+whatsapp)?$', clause)
        if m_call:
            video = 'video' in clause
            actions.append({'action': 'whatsapp_call', 'params': {'contact': m_call.group(1).strip(), 'video': video}})
            continue
            
        # WhatsApp Message parsing with explicit message
        m_msg = re.match(r'(?:send\\s+a?\\s*message\\s+to|message|whatsapp)\\s+(.+?)\\s+(?:on|using)?\\s*whatsapp\\s+(?:saying|that|with)\\s+(.+)', clause)
        if not m_msg:
             m_msg = re.match(r'(?:whatsapp|message)\\s+(.+?)\\s+(?:saying|that|with)\\s+(.+)', clause)
        
        if m_msg: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m_msg.group(1).strip(), 'message': m_msg.group(2).strip()}})
            continue
            
        # WhatsApp Message without explicit message payload
        m_msg_empty = re.match(r'(?:send\\s+a?\\s*message\\s+to|message|whatsapp)\\s+(.+?)(?:\\s+on\\s+whatsapp)?$', clause)
        if m_msg_empty:
             actions.append({'action': 'whatsapp', 'params': {'contact': m_msg_empty.group(1).strip(), 'message': ''}})
             continue
             
        # Read Chat parsing
        m_read = re.match(r'(?:read|check)\\s+(?:my\\s+)?(?:chat|messages)\\s+(?:with|from)\\s+(.+?)(?:\\s+on\\s+whatsapp)?$', clause)
        if m_read:
             actions.append({'action': 'whatsapp_read', 'params': {'contact': m_read.group(1).strip()}})
             continue

        m = re.match(r'(?:open|launch|start|run)\\s+(.+)', clause)"""

content = re.sub(r'def parse_commands\(msg\):.*?m = re\.match\(r\'\(\?:open\|launch\|start\|run\)\\s\+\(\.\+\)\', clause\)', new_parse_commands, content, flags=re.DOTALL)

with open('/Users/divyanshu/Documents/anti/main.py', 'w') as f:
    f.write(content)
