fish_config theme choose "Rosé Pine Moon"

export EDITOR="micro"
export STARSHIP_CONFIG=.config/starship/starship.toml

set -g fish_greeting

set -gx DOTFILES_PATH ~/dotfiles
set -gx PATH ~/bin $PATH

zoxide init fish | source
starship init fish | source
