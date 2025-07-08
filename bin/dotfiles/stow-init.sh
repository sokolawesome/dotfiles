#!/bin/bash

function validate-environment
{
    if [ ! -d "$HOME/dotfiles" ]
    then
        echo "error: dotfiles directory '$HOME/dotfiles' does not exist"
        return 1
    fi

    if ! command -v stow >/dev/null 2>&1
    then
        echo "error: gnu stow not found, install it with your package manager."
        return 1
    fi
}

function get-target-directory
{
    local dir="$1"

    case "$dir" in
        home) echo "$HOME" ;;
        config) echo "$HOME/.config" ;;
        bin) echo "$HOME/bin" ;;
        *) return 1 ;;
    esac
}

function ensure-target-exists
{
    local target="$1"
    local dir_name="$2"

    if [ "$dir_name" = "config" ] || [ "$dir_name" = "bin" ]
    then
        if [ ! -d "$target" ]
        then
            echo "creating $target directory..."
            mkdir -p "$target" || return 1
        fi
    fi
}

function validate-source-directory
{
    local dir="$1"

    if [ ! -d "$dir" ]
    then
        echo "warning: '$dir/' directory not found in dotfiles"
        return 1
    fi
}

function execute-stow
{
    local target="$1"
    local dir="$2"

    echo "stowing '$dir' → $target ..."
    stow --no-folding -t "$target" "$dir" || return 1
}

function process-directories
{
    for dir in home config bin
    do
        if ! validate-source-directory "$dir"
        then
            continue
        fi

        local target=$(get-target-directory "$dir")
        if [ -z "$target" ]
        then
            echo "error: unknown directory type '$dir'"
            return 1
        fi

        if ! ensure-target-exists "$target" "$dir"
        then
            return 1
        fi

        if ! execute-stow "$target" "$dir"
        then
            echo "error: failed to stow $dir"
            return 1
        fi
    done
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    pushd "$HOME/dotfiles" >/dev/null || return 1
    if ! process-directories
    then
        popd >/dev/null
        exit 1
    fi
    popd >/dev/null

    echo "stowing dotfiles completed successfully!"
}

main "$@"
