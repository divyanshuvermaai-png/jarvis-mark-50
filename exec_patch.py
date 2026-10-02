with open('/Users/divyanshu/Documents/anti/main.py', 'r') as f:
    content = f.read()

new_exec = """        if action == 'whatsapp' or action == 'whatsapp_call' or action == 'whatsapp_read':
            contact = params.get('contact', '')
            msg_text = params.get('message', '')
            is_call = (action == 'whatsapp_call')
            is_read = (action == 'whatsapp_read')
            
            # Using the new modular WhatsAppController
            from whatsapp_controller import WhatsAppController
            wa = WhatsAppController()
            
            if is_call:
                video = params.get('video', False)
                res = wa.initiate_call(contact, video=video)
                if res['success']:
                    result['data'] = f"Calling {res.get('contact', contact)} on WhatsApp"
                else:
                    result['success'] = False
                    result['data'] = res.get('error', res.get('status', 'Unknown Error')) + ": " + res.get('details', '')
            elif is_read:
                res = wa.read_chat(contact)
                if res['success']:
                    msgs = res.get('messages', [])
                    if msgs:
                        result['data'] = f"Recent messages with {res.get('contact', contact)}: " + " | ".join(msgs)
                    else:
                        result['data'] = f"No recent messages found with {res.get('contact', contact)}."
                else:
                    result['success'] = False
                    result['data'] = res.get('error', res.get('status', 'Unknown Error')) + ": " + res.get('details', '')
            else:
                if msg_text == '':
                    result['success'] = False
                    result['data'] = "empty_message"
                else:
                    res = wa.send_message(contact, msg_text)
                    if res['success']:
                        result['data'] = f"Sending message to {res.get('contact', contact)}"
                    else:
                        result['success'] = False
                        result['data'] = res.get('error', res.get('status', 'Unknown Error')) + ": " + res.get('details', '')"""

start_idx = content.find("if action == 'whatsapp' or action == 'whatsapp_call':")
end_search = "        elif action == 'play_song':"
end_idx = content.find(end_search, start_idx)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_exec + '\n\n' + content[end_idx:]
    with open('/Users/divyanshu/Documents/anti/main.py', 'w') as f:
        f.write(new_content)
    print("Execute Patched!")
else:
    print("Could not find start or end index.")
