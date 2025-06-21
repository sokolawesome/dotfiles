#!/bin/bash

if ! command -v cliphist &> /dev/null; then
    notify-send "Error" "cliphist not found"
    exit 1
fi

case "$1" in
    "clear")
        cliphist wipe
        notify-send "Clipboard" "History cleared"
        ;;
    "delete")
        selected=$(cliphist list | rofi -dmenu -p "Delete Entry" -config ~/.config/rofi/clipboard.rasi)
        if [ -n "$selected" ]; then
            echo "$selected" | cliphist delete
            notify-send "Clipboard" "Entry deleted"
        fi
        ;;
    *)
        selected=$(cliphist list | rofi -dmenu -p "Clipboard" -config ~/.config/rofi/clipboard.rasi)

        case $? in
            0)
                if [ -n "$selected" ]; then
                    echo "$selected" | cliphist decode | wl-copy
                fi
                ;;
            10)
                echo "$selected" | cliphist delete
                notify-send "Clipboard" "Entry deleted"
                ;;
            11)
                cliphist wipe
                notify-send "Clipboard" "History cleared"
                ;;
        esac
        ;;
esac
