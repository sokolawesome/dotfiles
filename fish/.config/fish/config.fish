set -g fish_greeting

zoxide init fish | source

if test -f ~/.cache/wal/colors.fish
    source ~/.cache/wal/colors.fish
end
