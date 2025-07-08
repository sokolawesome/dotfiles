#!/bin/bash

get_location_data() {
    local ipinfo_response
    ipinfo_response=$(curl -s "https://ipinfo.io/json")

    local loc_str=$(echo "$ipinfo_response" | jq -r '.loc // "unknown"')

    if [[ "$loc_str" == "unknown" || "$loc_str" == "null" ]]; then
        echo "Error: Could not retrieve location data" >&2
        return 1
    fi

    local latitude=$(echo "$loc_str" | cut -d',' -f1)
    local longitude=$(echo "$loc_str" | cut -d',' -f2)

    echo "$latitude $longitude"
    return 0
}

start_wlsunset() {
    if pgrep -f "wlsunset -l" >/dev/null; then
        echo "wlsunset already running" >&2
        return 0
    fi

    local location_data
    location_data=$(get_location_data)

    if [[ -z "$location_data" ]]; then
        echo "Error: Failed to get location data for wlsunset" >&2
        return 1
    fi

    local latitude=$(echo "$location_data" | cut -d' ' -f1)
    local longitude=$(echo "$location_data" | cut -d' ' -f2)

    echo "Starting wlsunset with Lat: $latitude, Lon: $longitude" >&2
    wlsunset -l "$latitude" "$longitude" -t 6000 2500 -S -60 -s +60 &
    echo "wlsunset started" >&2
}

get_waybar_status() {
    local temp=$(hyprctl hyprsunset temperature 2>/dev/null || echo "6000")

    echo "{\"text\": \"󱍖 ${temp}K\"}"
}

case "$1" in
    "start"|"")
        start_wlsunset
        ;;
    "status")
        get_waybar_status
        ;;
    *)
        echo "Usage: $0 [start|status]"
        exit 1
        ;;
esac
