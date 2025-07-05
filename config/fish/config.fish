if status is-login
    if test (tty) = "/dev/tty1"
        exec dbus-run-session Hyprland
    end
end

fish_config theme choose "Rosé Pine Moon"

set -g fish_greeting

set -gx DOTFILES_PATH ~/dotfiles

zoxide init fish | source

export EDITOR="micro"
