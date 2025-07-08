#!/bin/bash

validate_environment() {
    if [[ ! -d "$HOME/dotfiles" ]]; then
        echo "Error: Dotfiles directory '$HOME/dotfiles' does not exist"
        return 1
    fi

    if ! command -v stow &> /dev/null; then
        echo "Error: GNU Stow is not installed. Install it with 'sudo pacman -S stow'."
        return 1
    fi
}

get_target_directory() {
    local dir="$1"

    case "$dir" in
        home)
            echo "$HOME"
            ;;
        config)
            echo "$HOME/.config"
            ;;
        bin)
            echo "$HOME/bin"
            ;;
        *)
            return 1
            ;;
    esac
}

ensure_target_exists() {
    local target="$1"
    local dir_name="$2"

    if [[ "$dir_name" == "config" ]]; then
        if [[ ! -d "$target" ]]; then
            echo "Creating ~/.config directory..."
            mkdir -p "$target" || {
                echo "Error: Failed to create ~/.config"
                return 1
            }
        fi
    elif [[ "$dir_name" == "bin" ]]; then
        if [[ ! -d "$target" ]]; then
            echo "Creating ~/bin directory..."
            mkdir -p "$target" || {
                echo "Error: Failed to create ~/bin"
                return 1
            }
        fi
    fi
}

validate_source_directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        echo "Warning: '$dir/' directory not found in dotfiles"
        return 1
    fi
}

execute_stow() {
    local target="$1"
    local dir="$2"

    echo "Stowing '$dir' → $target ..."
    stow --no-folding -t "$target" "$dir" || {
        echo "Error: Failed to stow $dir"
        return 1
    }
}

process_directories() {
    for dir in home config bin; do
        if ! validate_source_directory "$dir"; then
            continue
        fi

        local target
        target=$(get_target_directory "$dir")
        if [[ -z "$target" ]]; then
            echo "Error: Unknown directory type '$dir'"
            return 1
        fi

        if ! ensure_target_exists "$target" "$dir"; then
            return 1
        fi

        if ! execute_stow "$target" "$dir"; then
            return 1
        fi
    done
}

main() {
    if ! validate_environment; then
        return 1
    fi

    pushd "$HOME/dotfiles" > /dev/null || {
        echo "Error: Failed to enter '$HOME/dotfiles'"
        return 1
    }

    if ! process_directories; then
        popd > /dev/null
        return 1
    fi

    popd > /dev/null
    echo "Stowing dotfiles completed successfully!"
}

main "$@"
