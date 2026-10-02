import json

files = {}
with open('/Users/divyanshu/.gemini/antigravity/brain/b8566a2f-854e-4523-937c-18285cadf861/.system_generated/logs/transcript_full.jsonl') as f:
    for line in f:
        obj = json.loads(line)
        if 'tool_calls' in obj:
            for tc in obj['tool_calls']:
                if tc['name'] == 'write_to_file' or tc['name'] == 'replace_file_content':
                    target = tc['args'].get('TargetFile', '')
                    if 'index.html' in target or 'style.css' in target or 'script.js' in target:
                        # Capture the last write before step 200 (V2 UI was done around step 187)
                        if obj['step_index'] < 200:
                            files[target] = tc['args'].get('CodeContent', tc['args'].get('ReplacementContent', ''))

with open('v2_index.html', 'w') as f: f.write(files['/Users/divyanshu/Documents/anti/index.html'])
with open('v2_style.css', 'w') as f: f.write(files['/Users/divyanshu/Documents/anti/style.css'])
with open('v2_script.js', 'w') as f: f.write(files['/Users/divyanshu/Documents/anti/script.js'])

