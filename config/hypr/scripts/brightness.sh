#!/bin/bash

CHANGE="$1"

hyprctl hyprsunset gamma "$CHANGE"

VALUE=$(hyprctl hyprsunset gamma)

VALUE=$(printf "%.0f" "$VALUE")

notify-send -t 1000 -c "brightness" -h int:value:"$VALUE" "󰳲 $VALUE"
