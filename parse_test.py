import re

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    
    # Split by " and " or "," ONLY if followed by a verb keyword, to avoid splitting song names or queries incorrectly.
    # We also split by " then ".
    split_regex = r'(?:\s+and\s+|\s+then\s+|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        # Analyze screen
        if any(k in clause for k in ['look at my screen', "what's on my screen", 'read my screen', 'see this', 'what am i looking at']):
            actions.append({'action': 'analyze_screen'})
            continue
            
        # Media controls (explicit)
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
            
        # Play song
        m = re.match(r'(?:play|listen to)\s+(.+?)(?:\s+on\s+spotify)?$', clause)
        if m:
            song = m.group(1).strip()
            if song not in ('music', 'pause', 'stop', 'next', 'previous'):
                actions.append({'action': 'play_song', 'params': {'song': song}})
            continue
            
        # Whatsapp
        m = re.match(r'(?:send|message|whatsapp)\s+(?:a\s+message\s+to\s+)?(.+?)\s+(?:on|using)?\s*whatsapp\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue
            
        m = re.match(r'(?:whatsapp|message)\s+(.+?)\s+(?:saying|that)\s+(.+)', clause)
        if m: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m.group(1).strip(), 'message': m.group(2).strip()}})
            continue

        # Open apps (supports multiple apps like "open A and B")
        m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
        if not m: m = re.match(r"let'?s?\s+open\s+(.+)", clause)
        if m:
            targets = re.split(r'\s+and\s+|,', m.group(1))
            for t in targets:
                t = t.strip().rstrip('.')
                if t:
                    if t in ('terminal', 'the terminal', 'a terminal'): t = 'terminal'
                    actions.append({'action': 'open_app', 'params': {'name': t}})
            continue
            
        # Close apps (supports multiple apps)
        m = re.match(r'(?:close|quit|kill|stop|exit|shut down)\s+(.+)', clause)
        if m:
            targets = re.split(r'\s+and\s+|,', m.group(1))
            for t in targets:
                t = t.strip().rstrip('.')
                if t: actions.append({'action': 'close_app', 'params': {'name': t}})
            continue
            
        # Screenshot
        if any(k in clause for k in ['screenshot', 'screen capture']):
            actions.append({'action': 'screenshot'})
            continue
            
        # Volume
        m = re.search(r'volume\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'volume', 'params': {'level': int(m.group(1))}})
            continue
            
        # Brightness
        m = re.search(r'brightness\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'brightness', 'params': {'level': int(m.group(1))}})
            continue
            
        # System info
        if any(k in clause for k in ['system info', 'system status', 'diagnostics', 'cpu usage', 'ram usage']):
            actions.append({'action': 'system_info'})
            continue
            
        # Sleep / Lock
        if any(k in clause for k in ['lock screen', 'lock my mac']):
            actions.append({'action': 'lock_screen'})
            continue
        if clause in ('sleep', 'go to sleep'):
            actions.append({'action': 'sleep'})
            continue
            
        # Search
        m = re.match(r'(?:search|google|look up|find)\s+(?:for\s+)?(.+)', clause)
        if m:
            actions.append({'action': 'web_search', 'params': {'query': m.group(1).strip()}})
            continue
            
    return actions

print(parse_commands("play tum ho toh song on spotify and open whatsapp and firefox private window and close terminal and set volume to 50"))
