#!/bin/bash

function validate-environment
{
    for cmd in curl jq wlsunset
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function get-location-data
{
    local ipinfo_response=$(curl -s "https://ipinfo.io/json")
    local loc_str=$(echo "$ipinfo_response" | jq -r '.loc // "unknown"')

    if [ "$loc_str" = "unknown" ] || [ "$loc_str" = "null" ]
    then
        echo "error: could not retrieve location data"
        return 1
    fi

    local latitude=$(echo "$loc_str" | cut -d',' -f1)
    local longitude=$(echo "$loc_str" | cut -d',' -f2)

    echo "$latitude $longitude"
}

function start-wlsunset
{
    if pgrep -f "wlsunset -l" >/dev/null
    then
        echo "error: wlsunset is already running"
        return 1
    fi

    local location_data=$(get-location-data)
    if [ -z "$location_data" ]
    then
        echo "error: failed to get location data for wlsunset"
        return 1
    fi

    local latitude=$(echo "$location_data" | cut -d' ' -f1)
    local longitude=$(echo "$location_data" | cut -d' ' -f2)

    echo "starting wlsunset with latitude: $latitude, longitude: $longitude..."
    wlsunset -l "$latitude" "$longitude" -t 6000 2500 -S -60 -s +60 &
    echo "wlsunset started successfully"
}

function get-waybar-status
{
    local temp=$(hyprctl hyprsunset temperature 2>/dev/null || echo "6000")
    echo "{\"text\": \"󱍖 ${temp}K\"}"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    case "$1" in
        start|"")
            start-wlsunset
            ;;
        status)
            get-waybar-status
            ;;
        *)
            echo "usage: $0 [start|status]"
            echo "  start            start wlsunset with location-based settings"
            echo "  status           show temperature status for Waybar"
            exit 1
            ;;
    esac
}

main "$@"
