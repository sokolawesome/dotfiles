#!/bin/bash

function validate-environment
{
    for cmd in hyprctl notify-send
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function adjust-brightness
{
    local change="$1"
    hyprctl hyprsunset gamma "$change"
}

function get-brightness
{
    local value=$(hyprctl hyprsunset gamma)
    printf "%.0f" "$value"
}

function display-brightness
{
    local value="$1"
    notify-send -t 1000 -c "brightness" -h int:value:"$value" "󰳲 $value"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    if [ -n "$1" ]
    then
        adjust-brightness "$1"
    fi

    local value=$(get-brightness)
    display-brightness "$value"
}

main "$@"
