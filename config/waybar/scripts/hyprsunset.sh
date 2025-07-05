#!/bin/bash

get_current_temp() {
    hyprctl hyprsunset temperature 2>/dev/null || echo "6000"
}

toggle_temp() {
    local current_temp=$(get_current_temp)

    if [[ "$current_temp" -eq 2500 ]]; then
        hyprctl hyprsunset temperature 6000
    else
        hyprctl hyprsunset temperature 2500
    fi
}

get_status() {
    local current_temp=$(get_current_temp)

    if [[ "$current_temp" -eq 2500 ]]; then
        echo '{"text": " ", "tooltip": "Night mode (2500K)", "class": "night"}'
    else
        echo '{"text": " ", "tooltip": "Day mode (6000K)", "class": "day"}'
    fi
}

case "$1" in
    "toggle")
        toggle_temp
        ;;
    "status"|"")
        get_status
        ;;
    *)
        echo "Usage: $0 [toggle|status]"
        exit 1
        ;;
esac
