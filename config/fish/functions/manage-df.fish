function manage-df --description "Manage dotfiles using GNU Stow"

    # Ensure DOTFILES_PATH is set and valid
    if not set -q DOTFILES_PATH
        echo "Error: \$DOTFILES_PATH is not set"
        return 1
    end

    if not test -d "$DOTFILES_PATH"
        echo "Error: Dotfiles directory '$DOTFILES_PATH' does not exist"
        return 1
    end

    # Ensure stow is installed
    if not command -q stow
        echo "Error: GNU Stow is not installed. Install it with 'sudo pacman -S stow'."
        return 1
    end

    # Parse flags
    argparse R/restow D/delete n/dry-run -- $argv
    or return 1

    # Determine base stow command
    set -l stow_cmd stow --no-folding
    set -l action Stowing

    if set -q _flag_restow
        set stow_cmd "$stow_cmd -R --no-folding"
        set action Restowing
    else if set -q _flag_delete
        set stow_cmd "$stow_cmd -D"
        set action Unstowing
    else if set -q _flag_dry_run
        set stow_cmd "$stow_cmd -n --no-folding"
        set action Dry-run
    end

    # Go to dotfiles root
    pushd $DOTFILES_PATH
    or begin
        echo "Error: Failed to enter '$DOTFILES_PATH'"
        return 1
    end

    # Handle home and config
    for dir in home config
        if not test -d "$dir"
            echo "Warning: '$dir/' directory not found in dotfiles"
            continue
        end

        if test "$dir" = home
            set target $HOME
        else if test "$dir" = config
            set target "$HOME/.config"
            mkdir -p "$target"
            or begin
                echo "Error: Failed to create ~/.config"
                popd
                return 1
            end
        end

        echo "$action '$dir' → $target ..."
        eval $stow_cmd -t "$target" "$dir"
        or begin
            echo "Error: Failed to $action $dir"
            popd
            return 1
        end
    end

    popd
    echo "$action dotfiles completed successfully!"
end
