tell application "System Events"
    tell process "WhatsApp"
        get name of every menu bar item of menu bar 1
    end tell
end tell
