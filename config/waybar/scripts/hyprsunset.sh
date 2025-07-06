#!/bin/bash

TEMPS=(2500 3500 4500 6000)

get_current_temp() {
    hyprctl hyprsunset temperature 2>/dev/null || echo "6000"
}

set_temp() {
    hyprctl hyprsunset temperature "$1"
}

next_temp() {
    local current_temp=$(get_current_temp)
    local next="${TEMPS[0]}"

    for i in "${!TEMPS[@]}"; do
        if [[ "${TEMPS[$i]}" -eq "$current_temp" ]]; then
            next_index=$(( (i + 1) % ${#TEMPS[@]} ))
            next="${TEMPS[$next_index]}"
            break
        fi
    done

    set_temp "$next"
}

get_status() {
    local current_temp=$(get_current_temp)
    local icon=""

    if (( current_temp <= 3000 )); then
        icon=""
    elif (( current_temp <= 4000 )); then
        icon=""
    fi

    echo "{\"text\": \"$icon ${current_temp}K\", \"class\": \"temp-${current_temp}\"}"
}

case "$1" in
    "toggle")
        next_temp
        ;;
    "set")
        if [[ "$2" =~ ^[0-9]+$ ]]; then
            set_temp "$2"
        else
            echo "Usage: $0 set <temperature>"
            exit 1
        fi
        ;;
    "status"|"")
        get_status
        ;;
    *)
        echo "Usage: $0 [toggle|status|set <temperature>]"
        exit 1
        ;;
esac
