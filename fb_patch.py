with open('/Users/divyanshu/Documents/anti/main.py', 'r') as f:
    content = f.read()

new_fb = """            if not exec_res.get('success', True):
                error_data = str(exec_res.get('data', ''))
                if error_data == 'empty_message':
                    fb = f"Sir, you did not specify what message to send to {action_data['params'].get('contact', 'them').title()}. Please tell me what you'd like to say."
                elif 'WhatsAppPermissionError' in error_data or 'Accessibility permission denied' in error_data:
                    fb = "Sir, I need Accessibility permissions to control WhatsApp. Please grant them to Terminal or your IDE in System Settings under Privacy and Security"
                elif 'ContactAmbiguousError' in error_data:
                    fb = f"I found multiple contacts matching that name, sir. Please be more specific to ensure we contact the right person."
                elif 'WhatsAppNotRunningError' in error_data:
                    fb = "WhatsApp is not running or failed to launch, sir."
                else:
                    fb = f"Sir, the WhatsApp operation failed: {error_data}"
            elif act == 'open_app': fb = f"Opening {action_data['params'].get('name', 'application').title()}"
            elif act == 'close_app': fb = f"Closing {action_data['params'].get('name', 'application').title()}"
            elif act == 'play_song': fb = f"Playing {action_data['params'].get('song', 'track').title()} on Spotify"
            elif act == 'media_control': fb = f"Executing {action_data['params'].get('cmd', 'media')} command"
            elif act == 'whatsapp': fb = f"Sending message to {action_data['params'].get('contact', 'contact').title()}"
            elif act == 'whatsapp_call': fb = f"Calling {action_data['params'].get('contact', 'contact').title()} on WhatsApp"
            elif act == 'whatsapp_read': fb = f"{exec_res.get('data', 'No messages found')}"
            elif act == 'sleep': fb = "Shutting down non-essential systems"
            elif act == 'lock_screen': fb = "Locking the workstation"
            elif act == 'web_search': fb = f"Searching for '{action_data['params'].get('query', 'query')}'"
            elif act == 'volume': fb = f"Setting volume to {action_data['params'].get('level')}%"
            elif act == 'brightness': fb = f"Setting brightness to {action_data['params'].get('level')}%"
            elif act == 'system_info': fb = "Displaying system diagnostics"
            else: fb = f"Protocol executed: {act}" """

start_idx = content.find("if not exec_res.get('success', True):")
end_search = "            responses.append(fb)"
end_idx = content.find(end_search, start_idx)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_fb + '\n' + content[end_idx:]
    with open('/Users/divyanshu/Documents/anti/main.py', 'w') as f:
        f.write(new_content)
    print("Feedback Patched!")
else:
    print("Could not find start or end index for feedback.")
