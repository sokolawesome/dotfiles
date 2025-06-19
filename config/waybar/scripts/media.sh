#!/bin/bash

player_status=$(playerctl status 2>/dev/null)

if [[ "$player_status" == "Playing" || "$player_status" == "Paused" ]]; then
    clean_text() {
        grep -oP '[\p{L}\p{N} -]+' | tr -d '\n' | sed -E 's/ +/ /g; s/^\s+|\s+$//g'
    }

    artist=$(playerctl metadata artist 2>/dev/null | clean_text)
    title=$(playerctl metadata title 2>/dev/null | clean_text)

    if [[ -n "$artist" && -n "$title" ]]; then
        echo "$artist - $title"
    elif [[ -n "$title" ]]; then
        echo "$title"
    else
        echo "Playing media"
    fi
else
    echo ""
fi
