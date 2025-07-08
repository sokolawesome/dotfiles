#!/bin/bash

function validate-environment
{
    for cmd in wpctl notify-send
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function get-volume
{
    local volume_data=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
    local muted=$(echo "$volume_data" | awk '{print $3}')
    local value=$(echo "$volume_data" | awk '{print $2}')

    if [ "$muted" = "[MUTED]" ]
    then
        echo "muted"
        return 0
    fi

    local percentage=$(echo "( $value * 100 ) / 1" | bc)
    echo "$percentage"
    return 0
}

function display-volume
{
    local volume="$1"

    if [ "$volume" = "muted" ]
    then
        notify-send -t 1000 -c "volume" -h int:value:0 ""
        return
    fi

    local icon
    if [ "$volume" -ge 70 ]
    then
        icon=""
    elif [ "$volume" -ge 30 ]
    then
        icon=""
    elif [ "$volume" -gt 1 ]
    then
        icon=""
    else
        icon=""
    fi

    notify-send -t 1000 -c "volume" -h int:value:"$volume" "$icon $volume%"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    local volume=$(get-volume)
    display-volume "$volume"
}

main "$@"
