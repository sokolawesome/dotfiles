#!/bin/bash

function validate-environment
{
    for cmd in cliphist rofi wl-copy notify-send
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function run-rofi
{
    cliphist list | rofi -dmenu -p " Clipboard" -config ~/.config/rofi/clipboard.rasi \
        -kb-custom-1 "Alt+d" \
        -kb-custom-2 "Alt+Delete" \
        -kb-custom-3 "Alt+c" \
        -mesg "Alt+d: Delete | Alt+Del: Clear All | Alt+c: Copy Raw"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    while true
    do
        selected=$(run-rofi)
        local rofi_exit_code=$?

        case $rofi_exit_code in
            0)
                if [ -n "$selected" ]
                then
                    echo "$selected" | cliphist decode | wl-copy
                    notify-send "Clipboard" "Copied to clipboard"
                fi
                break
                ;;
            10)
                if [ -n "$selected" ]
                then
                    echo "$selected" | cliphist delete
                    notify-send "Clipboard" "Entry deleted"
                fi
                ;;
            11)
                cliphist wipe
                notify-send "Clipboard" "History cleared"
                ;;
            12)
                if [ -n "$selected" ]
                then
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
