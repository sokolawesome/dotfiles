# Options
options="⏻ Shutdown\n⏼ Reboot\n Logout"

# Get choice
chosen=$(echo -e "$options" | rofi -dmenu -p "Power Menu" -i)

# Execute chosen command
case "$chosen" in
    "⏻ Shutdown")
        systemctl poweroff
        ;;
    "⏼ Reboot")
        systemctl reboot
        ;;
    " Logout")
        hyprctl dispatch exit
        ;;
esac
