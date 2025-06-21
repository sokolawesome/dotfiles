if status is-login
    if test (tty) = "/dev/tty1"
        exec dbus-run-session Hyprland
    end
end

if test -f ~/.cache/wal/colors.fish
    source ~/.cache/wal/colors.fish
end

set -g fish_greeting

set -gx DOTFILES_PATH ~/dotfiles

zoxide init fish | source

export EDITOR="micro"
