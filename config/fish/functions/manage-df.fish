function manage-df --description "Manage dotfiles using GNU Stow"
    function validate_environment
        if not set -q DOTFILES_PATH
            echo "Error: \$DOTFILES_PATH is not set"
            return 1
        end

        if not test -d "$DOTFILES_PATH"
            echo "Error: Dotfiles directory '$DOTFILES_PATH' does not exist"
            return 1
        end

        if not command -q stow
            echo "Error: GNU Stow is not installed. Install it with 'sudo pacman -S stow'."
            return 1
        end
    end

    function show_help
        echo "Usage: manage-df [OPTIONS]"
        echo "  -R, --restow     Restow packages (remove then stow)"
        echo "  -D, --delete     Remove stowed packages"
        echo "  -n, --dry-run    Show what would be done without doing it"
        echo "  -h, --help       Show this help message"
    end

    function build_stow_command
        set -l restow $argv[1]
        set -l delete $argv[2]
        set -l dry_run $argv[3]

        set -l stow_cmd "stow --no-folding"
        set -l action "Stowing"

        if test "$restow" = true
            set stow_cmd "$stow_cmd -R"
            set action "Restowing"
        else if test "$delete" = true
            set stow_cmd "$stow_cmd -D"
            set action "Unstowing"
        else if test "$dry_run" = true
            set stow_cmd "$stow_cmd -n"
            set action "Dry-run"
        end

        echo "$stow_cmd"
        echo "$action"
    end

    function get_target_directory
        set -l dir $argv[1]

        switch $dir
            case home
                echo "$HOME"
            case config
                echo "$HOME/.config"
            case '*'
                echo ""
                return 1
        end
    end

    function ensure_target_exists
        set -l target $argv[1]
        set -l dir_name $argv[2]

        if test "$dir_name" = config
            if not test -d "$target"
                echo "Creating ~/.config directory..."
                mkdir -p "$target"
                or begin
                    echo "Error: Failed to create ~/.config"
                    return 1
                end
            end
        end
    end

    function validate_source_directory
        set -l dir $argv[1]

        if not test -d "$dir"
            echo "Warning: '$dir/' directory not found in dotfiles"
            return 1
        end
    end

    function execute_stow
        set -l stow_cmd $argv[1]
        set -l target $argv[2]
        set -l dir $argv[3]
        set -l action $argv[4]

        echo "$action '$dir' → $target ..."
        eval $stow_cmd -t "$target" "$dir"
        or begin
            echo "Error: Failed to $action $dir"
            return 1
        end
    end

    function process_directories
        set -l stow_cmd $argv[1]
        set -l action $argv[2]

        for dir in home config
            if not validate_source_directory "$dir"
                continue
            end

            set -l target (get_target_directory "$dir")
            if test -z "$target"
                echo "Error: Unknown directory type '$dir'"
                return 1
            end

            if not ensure_target_exists "$target" "$dir"
                return 1
            end

            if not execute_stow "$stow_cmd" "$target" "$dir" "$action"
                return 1
            end
        end
    end

    function safe_directory_change
        set -l target_dir $argv[1]

        pushd "$target_dir"
        or begin
            echo "Error: Failed to enter '$target_dir'"
            return 1
        end
    end

    argparse R/restow D/delete n/dry-run h/help -- $argv
    or return 1

    if set -q _flag_help
        show_help
        return 0
    end

    if not validate_environment
        return 1
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

    set -l stow_result (build_stow_command "$restow" "$delete" "$dry_run")
    set -l stow_cmd (echo "$stow_result" | head -n1)
    set -l action (echo "$stow_result" | tail -n1)

    if not safe_directory_change "$DOTFILES_PATH"
        return 1
    end

    if not process_directories "$stow_cmd" "$action"
        popd
        return 1
    end

    popd
    echo "$action dotfiles completed successfully!"
end
