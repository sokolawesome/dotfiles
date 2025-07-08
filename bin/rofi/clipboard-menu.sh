#!/bin/bash

check_dependencies() {
    local deps=("cliphist" "rofi" "wl-copy" "notify-send")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            notify-send "Error" "$dep not found"
            exit 1
        fi
    done
}

run_rofi() {
    cliphist list | rofi -dmenu -p " Clipboard" -config ~/.config/rofi/clipboard.rasi \
        -kb-custom-1 "Alt+d" \
        -kb-custom-2 "Alt+Delete" \
        -kb-custom-3 "Alt+c" \
        -mesg "Alt+d: Delete | Alt+Del: Clear All | Alt+c: Copy Raw"
}

main() {
    check_dependencies

    while true; do
        selected=$(run_rofi)
        rofi_exit_code=$?

        case $rofi_exit_code in
            0)
                if [ -n "$selected" ]; then
                    echo "$selected" | cliphist decode | wl-copy
                    notify-send "Clipboard" "Copied to clipboard"
                fi
                break
                ;;
            10)
                if [ -n "$selected" ]; then
                    echo "$selected" | cliphist delete
                    notify-send "Clipboard" "Entry deleted"
                fi
                ;;
            11)
                cliphist wipe
                notify-send "Clipboard" "History cleared"
                ;;
            12)
                if [ -n "$selected" ]; then
                    echo "$selected" | cliphist decode
                    notify-send "Clipboard" "Raw content displayed"
                fi
                ;;
            *)
                break
                ;;
        esac
    done
}

main "$@"
