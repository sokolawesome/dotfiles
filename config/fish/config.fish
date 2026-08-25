set -gx EDITOR micro
set -gx STARSHIP_CONFIG ~/.config/starship/starship.toml
set -gx MANPAGER "bat -plman"
set -gx DOTFILES_PATH ~/dotfiles

fish_add_path -g ~/bin ~/go/bin /usr/local/go/bin
set -g fish_greeting

status is-interactive || return

abbr -a --position anywhere -- --help '--help | bat -plhelp'
abbr -a --position anywhere -- -h '-h | bat -plhelp'

zoxide init fish | source
fzf --fish | source
starship init fish | source
