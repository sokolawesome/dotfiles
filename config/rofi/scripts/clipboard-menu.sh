#!/bin/bash

if ! command -v cliphist &> /dev/null; then
    notify-send "Error" "cliphist not found"
    exit 1
fi

run_rofi() {
    cliphist list | rofi -dmenu -p "󰅇 Clipboard" -config ~/.config/rofi/clipboard.rasi \
        -kb-custom-1 "Alt+d" \
        -kb-custom-2 "Alt+Delete"
}

while true; do
    selected=$(run_rofi)
    rofi_exit_code=$?

    case $rofi_exit_code in
        0) # Entry selected
            if [ -n "$selected" ]; then
                echo "$selected" | cliphist decode | wl-copy
            fi
            # Exit the loop as an item was selected and copied
            break
            ;;
        10) # Alt+d was pressed (delete)
            if [ -n "$selected" ]; then
                echo "$selected" | cliphist delete
                notify-send "Clipboard" "Entry deleted."
            fi
            # Relaunch rofi to show updated list
            ;;
        11) # Alt+Delete was pressed (clear)
            cliphist wipe
            notify-send "Clipboard" "History cleared."
            # Relaunch rofi to show empty/updated list
            ;;
        *) # Rofi was cancelled (e.g., by pressing Escape)
            break
            ;;
    esac
done
