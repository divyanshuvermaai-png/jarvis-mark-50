tell application "Stickies"
    activate
    tell application "System Events"
        keystroke "n" using command down
        delay 0.2
        keystroke "test sticky"
    end tell
end tell
