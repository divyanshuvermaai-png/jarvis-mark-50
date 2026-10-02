def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    
    split_regex = r'(?:\s+and\s+|\s+then\s+|\s+along\s+(?:with\s+)?(?:that\s+)?|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp)'
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
            
        m = re.match(r'(?:play|listen to)\s+(.+?)(?:\s+on\s+spotify)?$', clause)
        if m:
            song = m.group(1).strip()
            if song not in ('music', 'pause', 'stop', 'next', 'previous'):
                actions.append({'action': 'play_song', 'params': {'song': song}})
            continue
            
        m = re.match(r'(?:send|message|whatsapp)\s+(?:a\s+message\s+to\s+)?(.+?)\s+(?:on|using)?\s*whatsapp\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue
            
        m = re.match(r'(?:whatsapp|message)\s+(.+?)\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue

        m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
        if not m: m = re.match(r"let'?s?\s+open\s+(.+)", clause)
        if m:
            target_str = m.group(1)
            parts = re.split(r'\s+and\s+|,', target_str)
            keys = sorted(APP_MAP.keys(), key=len, reverse=True)
            
            for p in parts:
                p = p.strip()
                if not p: continue
                
                found_in_part = []
                temp = p
                for k in keys:
                    idx = temp.find(k)
                    while idx != -1:
                        found_in_part.append((idx, k))
                        temp = temp[:idx] + ' ' * len(k) + temp[idx+len(k):]
                        idx = temp.find(k)
                        
                if len(found_in_part) > 1:
                    found_in_part.sort()
                    for pos, k in found_in_part:
                        if k in ('terminal', 'the terminal', 'a terminal'): k = 'terminal'
                        actions.append({'action': 'open_app', 'params': {'name': k}})
                else:
                    t = p.rstrip('.')
                    if t in ('terminal', 'the terminal', 'a terminal'): t = 'terminal'
                    actions.append({'action': 'open_app', 'params': {'name': t}})
            continue
            
        m = re.match(r'(?:close|quit|kill|stop|exit|shut down)\s+(.+)', clause)
        if m:
            target_str = m.group(1)
            parts = re.split(r'\s+and\s+|,', target_str)
            keys = sorted(APP_MAP.keys(), key=len, reverse=True)
            for p in parts:
                p = p.strip()
                if not p: continue
                found_in_part = []
                temp = p
                for k in keys:
                    idx = temp.find(k)
                    while idx != -1:
                        found_in_part.append((idx, k))
                        temp = temp[:idx] + ' ' * len(k) + temp[idx+len(k):]
                        idx = temp.find(k)
                if len(found_in_part) > 1:
                    found_in_part.sort()
                    for pos, k in found_in_part:
                        actions.append({'action': 'close_app', 'params': {'name': k}})
                else:
                    t = p.rstrip('.')
                    actions.append({'action': 'close_app', 'params': {'name': t}})
            continue
            
        if any(k in clause for k in ['screenshot', 'screen capture']):
            actions.append({'action': 'screenshot'})
            continue
            
        m = re.search(r'volume\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'volume', 'params': {'level': int(m.group(1))}})
            continue
            
        m = re.search(r'brightness\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'brightness', 'params': {'level': int(m.group(1))}})
            continue
            
        if any(k in clause for k in ['system info', 'system status', 'diagnostics', 'cpu usage', 'ram usage']):
            actions.append({'action': 'system_info'})
            continue
            
        if any(k in clause for k in ['lock screen', 'lock my mac']):
            actions.append({'action': 'lock_screen'})
            continue
        if clause in ('sleep', 'go to sleep'):
            actions.append({'action': 'sleep'})
            continue
            
        m = re.match(r'(?:search|google|look up|find)\s+(?:for\s+)?(.+)', clause)
        if m:
            actions.append({'action': 'web_search', 'params': {'query': m.group(1).strip()}})
            continue
            
    return actions
