#!/bin/bash

if [[ "$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print $3}')" == "[MUTED]" ]]; then
    notify-send -t 1000 -c "volume" -h int:value:0 ""
    exit 0
fi

VALUE=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
VALUE=$(echo "$VALUE" | awk '{print $2}')
VALUE=$(echo "( $VALUE * 100 ) / 1" | bc)

if (( VALUE >= 70 )); then
    ICON=""
elif (( VALUE >= 30 )); then
    ICON=""
elif (( VALUE > 1 )); then
    ICON=""
else
    ICON=""
fi

notify-send -t 1000 -c "volume" -h int:value:$VALUE "$ICON $VALUE%"
