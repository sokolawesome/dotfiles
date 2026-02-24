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
    if tailscale status | grep "offers exit node"
    then
        echo "stopped"
        return 0
    else
        echo "running"
        return 1
    fi
}

function start-vpn
{
    if [ "$(get-vpn-status)" = "running" ]
    then
        echo "error: VPN is already running"
        return 1
    fi

    echo "starting VPN..."
    pkexec --disable-internal-agent bash -c \
        "tailscale set --exit-node=100.87.8.77"

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
        "tailscale set --exit-node="

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
