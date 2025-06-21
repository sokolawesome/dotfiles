#!/bin/bash

set -euo pipefail

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

wait_for_service() {
    local service="$1"
    local timeout="${2:-10}"
    local count=0

    while ! systemctl --user is-active "$service" >/dev/null 2>&1; do
        if [ $count -ge $timeout ]; then
            log "ERROR: Service $service failed to start within ${timeout}s"
            return 1
        fi
        sleep 0.5
        ((count++))
    done
    log "Service $service is active"
}

stop_services() {
    local services=("$@")
    for service in "${services[@]}"; do
        if systemctl --user is-active "$service" >/dev/null 2>&1; then
            log "Stopping $service"
            systemctl --user stop "$service" || true
        fi
    done
}

start_services() {
    local services=("$@")
    for service in "${services[@]}"; do
        log "Starting $service"
        systemctl --user start "$service"
        wait_for_service "$service"
    done
}

kill_processes() {
    local processes=("$@")
    for process in "${processes[@]}"; do
        if pgrep -x "$process" >/dev/null; then
            log "Killing $process"
            killall -e "$process" 2>/dev/null || true
        fi
    done
}

main() {
    log "Starting XDG portal setup"

    sleep 0.5

    # Kill existing portal processes
    kill_processes "xdg-desktop-portal-hyprland" "xdg-desktop-portal-gtk" "xdg-desktop-portal"

    # Update environment
    log "Updating environment"
    dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP=hyprland
    systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP

    # Start graphical session target
    systemctl --user start graphical-session.target

    # Stop all related services
    local services=(
        "pipewire"
        "wireplumber"
        "xdg-desktop-portal"
        "xdg-desktop-portal-gtk"
        "xdg-desktop-portal-hyprland"
    )

    stop_services "${services[@]}"
    sleep 0.2

    # Start portal processes manually first
    log "Starting portal processes"

    # Check if portal binaries exist
    local portals=(
        "/usr/lib/xdg-desktop-portal-hyprland"
        "/usr/lib/xdg-desktop-portal-gtk"
        "/usr/lib/xdg-desktop-portal"
    )

    for portal in "${portals[@]}"; do
        if [[ ! -x "$portal" ]]; then
            log "ERROR: Portal binary not found: $portal"
            exit 1
        fi
    done

    # Start portals in order
    "$portals[0]" &
    sleep 1

    "$portals[1]" &
    sleep 0.2

    "$portals[2]" &
    sleep 0.5

    # Start systemd services
    start_services "${services[@]}"

    log "XDG portal setup completed successfully"
}

main "$@"
