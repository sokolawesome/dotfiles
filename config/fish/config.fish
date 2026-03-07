fish_config theme choose "Rosé Pine Moon"

set -Ux EDITOR "micro"
set -Ux STARSHIP_CONFIG ~/.config/starship/starship.toml
set -Ux MANPAGER "bat -plman"
set -Ux DOTFILES_PATH ~/dotfiles
set -Ux PATH ~/bin ~/go/bin /usr/local/go/bin $PATH

set -U fish_greeting

abbr -a --position anywhere -- --help '--help | bat -plhelp'
abbr -a --position anywhere -- -h '-h | bat -plhelp'

zoxide init fish | source
fzf --fish | source
starship init fish | source
