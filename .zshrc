# Paths & Environment
export ZSH="$HOME/.oh-my-zsh"
ZSH_COMPDUMP="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump"
mkdir -p "$(dirname "$ZSH_COMPDUMP")"

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

# Zsh Options
setopt HIST_IGNORE_ALL_DUPS
setopt INC_APPEND_HISTORY
setopt SHARE_HISTORY
ENABLE_CORRECTION=true

# Completion Config3
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' rehash true

autoload -Uz compinit
compinit -d "$ZSH_COMPDUMP"

# Theme & Plugins
ZSH_THEME="gallois"

zstyle ':omz:update' mode auto
zstyle ':omz:update' frequency 7

plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  zsh-completions
)

source "$ZSH/oh-my-zsh.sh"

# Plugin Config
export ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=8'

# Extra Tools
eval "$(zoxide init zsh)"

# Aliases
alias ls="eza --icons"
alias cat="bat"
alias cd="z"
