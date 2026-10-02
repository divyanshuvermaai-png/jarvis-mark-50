import re

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    
    # Pre-process: if they say "open A and B", we can expand it to "open A and open B"
    # But it's easier to just split the string into logical clauses.
    
    # We'll split by " and " and ","
    # But wait, "play X and Y" shouldn't be split if "X and Y" is a song.
    # To be safe, we'll split by " and " IF it is followed by a command verb,
    # OR if we are currently parsing an "open" command, we can handle multiple targets.
    
    # Let's use a simpler heuristic:
    # First, split the message by verbs! 
    # Actually, we can just look for independent clauses.
    
    # Let's split by " and " explicitly, but intelligently.
    clauses = re.split(r'\s+and\s+(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|volume|brightness|lock|sleep|analyze|read)', msg)
    
    # Now, for each clause, we might have multiple targets like "open whatsapp and firefox"
    for clause in clauses:
        clause = clause.strip()
        
        # Check play
        m = re.match(r'(?:play|listen to)\s+(.+?)(?:\s+on\s+spotify)?$', clause)
        if m:
            song = m.group(1).strip()
            if song not in ('music', 'pause', 'stop', 'next', 'previous'):
                actions.append({'action': 'play_song', 'params': {'song': song}})
                continue
            else:
                actions.append({'action': 'media_control', 'params': {'cmd': song if song != 'music' else 'play'}})
                continue
                
        # Check open
        m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
        if m:
            targets = re.split(r'\s+and\s+|,', m.group(1))
            for t in targets:
                t = t.strip().rstrip('.')
                if t: actions.append({'action': 'open_app', 'params': {'name': t}})
            continue
            
        # Add other checks here...
        
    return actions

print(parse_commands("play tum ho toh song on spotify and open whatsapp and firefox private window"))
