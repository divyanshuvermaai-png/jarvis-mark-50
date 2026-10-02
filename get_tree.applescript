tell application "System Events"
    set wa to first application process whose name contains "WhatsApp"
    set win to first window of wa
    
    set UI_list to every UI element of win
    set output_str to ""
    repeat with UI_elem in UI_list
        set r to role of UI_elem
        set d to description of UI_elem
        if d is missing value then
            set d_str to "null"
        else
            set d_str to d
        end if
        set output_str to output_str & r & " - " & d_str & "\n"
    end repeat
    return output_str
end tell
