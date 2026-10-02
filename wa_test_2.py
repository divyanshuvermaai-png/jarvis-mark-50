import subprocess
script = """
tell application "WhatsApp" to activate
delay 1.5
tell application "System Events"
    keystroke "f" using command down
    delay 0.5
    keystroke "subham"
    delay 1.0
    key code 36
    delay 1.0

keystroke "d" using {command down, shift down}
end tell
"""
proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
print("RETURN CODE:", proc.returncode)
print("STDOUT:", proc.stdout)
print("STDERR:", proc.stderr)
