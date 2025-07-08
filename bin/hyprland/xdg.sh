#!/bin/bash

function validate-environment
{
    for cmd in systemctl dbus-update-activation-environment
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function stop-portals
{
    systemctl --user stop xdg-desktop-portal
    systemctl --user stop xdg-desktop-portal-gtk
    systemctl --user stop xdg-desktop-portal-hyprland
}

function kill-portals
{
    killall -e xdg-desktop-portal-hyprland 2>/dev/null
    killall -e xdg-desktop-portal-gtk 2>/dev/null
    killall -e xdg-desktop-portal 2>/dev/null
}

function update-environment
{
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP=hyprland
    systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP
}

function start-portals
{
    systemctl --user start xdg-desktop-portal
    systemctl --user start xdg-desktop-portal-gtk
    systemctl --user start xdg-desktop-portal-hyprland
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    kill-portals
    sleep 0.5
    update-environment
    stop-portals
    sleep 0.1
    start-portals
    sleep 1

    echo "xdg desktop portal restarted successfully"
}

main "$@"
