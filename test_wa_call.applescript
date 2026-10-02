tell application "WhatsApp" to activate
delay 1
tell application "System Events"
    keystroke "f" using command down
    delay 0.5
    keystroke "Subham"
    delay 1
    key code 36 -- Enter
    delay 1
    -- Try typing message
    -- keystroke "hello"
    -- key code 36
end tell
