function manage-df -d "manage dotfiles using gnu stow"
    function validate-environment
        if not set -q DOTFILES_PATH
            echo "error: \$DOTFILES_PATH is not set"
            return 1
        end

        if not test -d "$DOTFILES_PATH"
            echo "error: dotfiles directory '$DOTFILES_PATH' does not exist"
            return 1
        end

        if not command -q stow
            echo "error: gnu stow is not installed. install it with 'sudo pacman -S stow'."
            return 1
        end
    end

    function build-stow-command
        set -l restow $argv[1]
        set -l delete $argv[2]
        set -l dry_run $argv[3]

        set -l stow_cmd "stow --no-folding"

        if test "$restow" = true
            set stow_cmd "$stow_cmd -R"
        else if test "$delete" = true
            set stow_cmd "$stow_cmd -D"
        else if test "$dry_run" = true
            set stow_cmd "$stow_cmd -n"
        end

        echo "$stow_cmd"
    end

    function get-action-description
        set -l restow $argv[1]
        set -l delete $argv[2]
        set -l dry_run $argv[3]

        if test "$restow" = true
            echo "restowing"
        else if test "$delete" = true
            echo "unstowing"
        else if test "$dry_run" = true
            echo "dry-run"
        else
            echo "stowing"
        end
    end

    function get-target-directory
        set -l dir $argv[1]

        switch $dir
            case home
                echo "$HOME"
            case config
                echo "$HOME/.config"
            case bin
                echo "$HOME/bin"
            case '*'
                return 1
        end
    end

    function ensure-target-exists
        set -l target $argv[1]
        set -l dir_name $argv[2]

        if test "$dir_name" = config
            if not test -d "$target"
                echo "creating ~/.config directory..."
                mkdir -p "$target" || return 1
            end
        else if test "$dir_name" = bin
            if not test -d "$target"
                echo "creating ~/bin directory..."
                mkdir -p "$target/bin" || return 1
            end
        end
    end

    function validate-source-directory
        set -l dir $argv[1]

        if not test -d "$dir"
            echo "warning: '$dir/' directory not found in dotfiles"
            return 1
        end
    end

    function execute-stow
        set -l stow_cmd $argv[1]
        set -l target $argv[2]
        set -l dir $argv[3]
        set -l action $argv[4]

        echo "$action '$dir' → $target ..."
        eval $stow_cmd -t "$target" "$dir" || begin
            echo "error: failed to $action $dir"
            return 1
        end
    end

    function process-directories
        set -l stow_cmd $argv[1]
        set -l action $argv[2]

        for dir in home config bin
            if not validate-source-directory "$dir"
                continue
            end

            set -l target (get-target-directory "$dir")
            if test -z "$target"
                echo "error: unknown directory type '$dir'"
                return 1
            end

            if not ensure-target-exists "$target" "$dir"
                return 1
            end

            if not execute-stow "$stow_cmd" "$target" "$dir" "$action"
                return 1
            end
        end
    end

    if not validate-environment
        return 1
    end

    argparse R/restow D/delete n/dry-run h/help -- $argv || return 1

    if set -q _flag_help
        echo "usage: manage-df [OPTIONS]"
        echo "  -R, --restow     restow packages (remove then stow)"
        echo "  -D, --delete     remove stowed packages"
        echo "  -n, --dry-run    show what would be done without doing it"
        echo "  -h, --help       show this help message"
        return 0
    end

    set -l restow false
    set -l delete false
    set -l dry_run false

    if set -q _flag_restow
        set restow true
    end
    if set -q _flag_delete
        set delete true
    end
    if set -q _flag_dry_run
        set dry_run true
    end

    set -l stow_cmd (build-stow-command "$restow" "$delete" "$dry_run")
    set -l action (get-action-description "$restow" "$delete" "$dry_run")

    pushd "$DOTFILES_PATH" || return 1

    if not process-directories "$stow_cmd" "$action"
        popd
        return 1
    end

    popd
    echo "$action dotfiles completed successfully!"
end
