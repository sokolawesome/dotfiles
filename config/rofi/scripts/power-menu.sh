#!/bin/bash

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
        " Shutdown")
            if confirm_action "Shutdown"; then
                systemctl poweroff
            fi
            ;;
        " Reboot")
            if confirm_action "Reboot"; then
                systemctl reboot
            fi
            ;;
        "󰍃 Logout")
            if confirm_action "Logout"; then
                hyprctl dispatch exit
            fi
            ;;
        *)
            exit 0
            ;;
    esac
}

main() {
    check_dependencies

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
}

main "$@"
