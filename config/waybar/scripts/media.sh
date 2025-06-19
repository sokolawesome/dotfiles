#!/bin/bash

player_status=$(playerctl status 2>/dev/null)

if [ "$player_status" = "Playing" ] || [ "$player_status" = "Paused" ]; then
    artist=$(playerctl metadata artist 2>/dev/null)
    title=$(playerctl metadata title 2>/dev/null)
    if [ -n "$artist" ] && [ -n "$title" ]; then
        echo "$artist - $title"
    elif [ -n "$title" ]; then
        echo "$title"
    else
        echo "Playing media"
    fi
else
    echo ""
fi
