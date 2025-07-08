#!/bin/bash

function validate-environment
{
    for cmd in pgrep pkexec
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function get-vpn-status
{
    if pgrep -f "outline-cli" >/dev/null
    then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

function start-vpn
{
    local vpn_process_name="outline-cli"
    local vpn_log_file="${VPN_LOG_FILE:-/dev/null}"

    if [ -z "$OUTLINE_VPN_URL" ]
    then
        if command -v zenity >/dev/null 2>&1
        then
            OUTLINE_VPN_URL=$(zenity --entry --title="VPN Setup" --text="Enter Outline VPN URL:")
            if [ -z "$OUTLINE_VPN_URL" ]
            then
                echo "error: no VPN URL provided"
                return 1
            fi
        else
            echo "error: OUTLINE_VPN_URL not set and zenity not installed. install it with 'sudo pacman -S zenity'."
            return 1
        fi
    fi

    if [ "$(get-vpn-status)" = "running" ]
    then
        echo "error: VPN is already running"
        return 1
    fi

    echo "starting VPN..."
    pkexec --disable-internal-agent env OUTLINE_VPN_URL="$OUTLINE_VPN_URL" VPN_LOG_FILE="$vpn_log_file" bash -c \
        "go run github.com/Jigsaw-Code/outline-sdk/x/examples/outline-cli@latest -transport \"$OUTLINE_VPN_URL\" > \"$vpn_log_file\" 2>&1 &"

    local auth_result=$?
    if [ $auth_result -eq 126 ]
    then
        echo "error: authentication cancelled by user"
        return 1
    elif [ $auth_result -ne 0 ]
    then
        echo "error: authentication failed"
        return 1
    fi

    sleep 2

    if [ "$(get-vpn-status)" = "running" ]
    then
        echo "VPN started successfully"
        return 0
    else
        echo "error: failed to start VPN"
        return 1
    fi
}

function stop-vpn
{
    if [ "$(get-vpn-status)" = "stopped" ]
    then
        echo "error: VPN is not running"
        return 1
    fi

    echo "stopping VPN..."
    pkexec --disable-internal-agent bash -c \
        "pkill -f 'outline-cli'; sleep 1; pkill -9 -f 'outline-cli' 2>/dev/null"

    local auth_result=$?
    if [ $auth_result -eq 126 ]
    then
        echo "error: authentication cancelled by user"
        return 1
    elif [ $auth_result -ne 0 ]
    then
        echo "error: authentication failed"
        return 1
    fi

    echo "VPN stopped successfully"
    return 0
}

function toggle-vpn
{
    if [ "$(get-vpn-status)" = "running" ]
    then
        stop-vpn
    else
        start-vpn
    fi
}

function get-waybar-status
{
    local status=$(get-vpn-status)
    local text=""

    if [ "$status" = "running" ]
    then
        text="VPN: ON"
    else
        text="VPN: OFF"
    fi

    echo "{\"text\": \"$text\"}"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    case "$1" in
        start)
            start-vpn
            ;;
        stop)
            stop-vpn
            ;;
        toggle)
            toggle-vpn
            ;;
        status|"")
            get-waybar-status
            ;;
        *)
            echo "usage: $0 [start|stop|toggle|status]"
            echo "  start            start the VPN"
            echo "  stop             stop the VPN"
            echo "  toggle           toggle VPN state (start if stopped, stop if running)"
            echo "  status           show VPN status for Waybar"
            exit 1
            ;;
    esac
}

main "$@"
