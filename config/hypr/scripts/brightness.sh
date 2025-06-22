#!/bin/bash

CHANGE="$1"
BUS=$(ddcutil detect | awk '/I2C bus/ {print $3}' | sed 's|/dev/i2c-||' | head -n1)

CURRENT=$(ddcutil getvcp 10 --bus=$BUS | awk -F'current value = |,' '{print $2}')
MAX=$(ddcutil getvcp 10 --bus=$BUS | awk -F'max value = |,' '{print $3}')

NEW=$((CURRENT + CHANGE))

if [ "$NEW" -gt "$MAX" ]; then
    NEW=$MAX
elif [ "$NEW" -lt 0 ]; then
    NEW=0
fi

ddcutil setvcp 10 "$NEW" --bus=$BUS
notify-send "Brightness" "$NEW"
