#!/bin/bash

VPN_PROCESS_NAME="outline-cli"
VPN_LOG_FILE="${VPN_LOG_FILE:-/dev/null}"

get_vpn_status() {
    if pgrep -f "$VPN_PROCESS_NAME" > /dev/null; then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

start_vpn() {
    if [[ -z "$OUTLINE_VPN_URL" ]]; then
        if command -v zenity &> /dev/null; then
            OUTLINE_VPN_URL=$(zenity --entry --title="VPN Setup" --text="Enter Outline VPN URL:")
            if [[ -z "$OUTLINE_VPN_URL" ]]; then
                echo "Error: No URL provided" >&2
                return 1
            fi
        else
            echo "Error: OUTLINE_VPN_URL not set and zenity not available" >&2
            return 1
        fi
    fi

    if [[ "$(get_vpn_status)" == "running" ]]; then
        echo "VPN is already running" >&2
        return 0
    fi

    echo "Starting VPN..." >&2

    pkexec --disable-internal-agent env OUTLINE_VPN_URL="$OUTLINE_VPN_URL" VPN_LOG_FILE="$VPN_LOG_FILE" bash -c '
        go run github.com/Jigsaw-Code/outline-sdk/x/examples/outline-cli@latest -transport "$OUTLINE_VPN_URL" > "$VPN_LOG_FILE" 2>&1 &
    '

    local auth_result=$?
    if [[ $auth_result -eq 126 ]]; then
        echo "Authentication cancelled by user" >&2
        return 1
    elif [[ $auth_result -ne 0 ]]; then
        echo "Authentication failed" >&2
        return 1
    fi

    sleep 2

    if [[ "$(get_vpn_status)" == "running" ]]; then
        echo "VPN started successfully" >&2
        return 0
    else
        echo "Failed to start VPN" >&2
        return 1
    fi
}

stop_vpn() {
    if [[ "$(get_vpn_status)" == "stopped" ]]; then
        echo "VPN is not running" >&2
        return 0
    fi

    echo "Stopping VPN..." >&2

    pkexec --disable-internal-agent bash -c "
        pkill -f '$VPN_PROCESS_NAME'
        sleep 1
        pkill -9 -f '$VPN_PROCESS_NAME' 2>/dev/null
    "

    local auth_result=$?
    if [[ $auth_result -eq 126 ]]; then
        echo "Authentication cancelled by user" >&2
        return 1
    elif [[ $auth_result -ne 0 ]]; then
        echo "Authentication failed" >&2
        return 1
    fi

    echo "VPN stopped" >&2
    return 0
}

toggle_vpn() {
    if [[ "$(get_vpn_status)" == "running" ]]; then
        stop_vpn
    else
        start_vpn
    fi
}

get_waybar_status() {
    local status=$(get_vpn_status)
    local text=""

    if [[ "$status" == "running" ]]; then
        text="VPN: ON"
    else
        text="VPN: OFF"
    fi

    echo "{\"text\": \"$text\"}"
}

case "$1" in
    "start")
        start_vpn
        ;;
    "stop")
        stop_vpn
        ;;
    "toggle")
        toggle_vpn
        ;;
    "status"|"")
        get_waybar_status
        ;;
    *)
        echo "Usage: $0 [start|stop|toggle|status]"
        exit 1
        ;;
esac
