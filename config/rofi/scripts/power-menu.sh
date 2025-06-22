#!/bin/bash

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_DIR="$HOME/.config/rofi"

check_dependencies() {
    local deps=("rofi" "systemctl" "hyprctl" "notify-send")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            notify-send "Error" "$dep not found"
            exit 1
        fi
    done
}

get_power_options() {
    echo " Shutdown"
    echo " Reboot"
    echo "󰍃 Logout"
    echo "󰅠 Cancel"
}

confirm_action() {
    local action="$1"
    local confirmation
    confirmation=$(echo -e "󰄬 Yes\n󰅖 No" | rofi -dmenu -p "Confirm $action?" -config "$CONFIG_DIR/power.rasi")
    [[ "$confirmation" == "󰄬 Yes" ]]
}

execute_action() {
    local chosen="$1"

    case "$chosen" in
        " Shutdown")
            if confirm_action "Shutdown"; then
                notify-send "System" "Shutting down..." -t 3000
                systemctl poweroff
            fi
            ;;
        " Reboot")
            if confirm_action "Reboot"; then
                notify-send "System" "Rebooting..." -t 3000
                systemctl reboot
            fi
            ;;
        "󰍃 Logout")
            if confirm_action "Logout"; then
                notify-send "System" "Logging out..." -t 3000
                hyprctl dispatch exit
            fi
            ;;
        "󰅠 Cancel")
            exit 0
            ;;
        *)
            exit 0
            ;;
    esac
}

show_system_info() {
    local uptime
    local load_avg
    local memory_usage

    uptime=$(uptime -p 2>/dev/null || echo "Unknown")
    load_avg=$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null || echo "Unknown")
    memory_usage=$(free -h | awk 'NR==2{printf "%.1f%%", $3/$2*100}' 2>/dev/null || echo "Unknown")

    echo "Uptime: $uptime"
    echo "Load: $load_avg"
    echo "Memory: $memory_usage"
}

main() {
    check_dependencies

    local info_mode=false
    if [[ "${1:-}" == "--info" ]]; then
        info_mode=true
    fi

    if $info_mode; then
        local chosen
        chosen=$(get_power_options | rofi -dmenu -p "󰐥 Power Menu" -config "$CONFIG_DIR/power.rasi" \
            -mesg "$(show_system_info)" \
            -kb-custom-1 "Alt+i")
        local rofi_exit_code=$?

        case $rofi_exit_code in
            10)
                main
                ;;
            *)
                execute_action "$chosen"
                ;;
        esac
    else
        local chosen
        chosen=$(get_power_options | rofi -dmenu -p "󰐥 Power Menu" -config "$CONFIG_DIR/power.rasi" \
            -kb-custom-1 "Alt+i" \
            -mesg "Alt+i: Show system info")
        local rofi_exit_code=$?

        case $rofi_exit_code in
            10)
                main --info
                ;;
            *)
                execute_action "$chosen"
                ;;
        esac
    fi
}

main "$@"
