function save-packages -d "Save explicitly installed pacman and AUR packages to separate files in dotfiles directory"
    function validate_environment
        if not set -q DOTFILES_PATH
            echo "Error: \$DOTFILES_PATH is not set"
            return 1
        end

        if not test -d "$DOTFILES_PATH"
            echo "Error: Dotfiles directory '$DOTFILES_PATH' does not exist"
            return 1
        end

        if not command -q pacman
            echo "Error: pacman is not installed or not in PATH"
            return 1
        end
    end

    function setup_directories
        set -l meta_dir "$DOTFILES_PATH/_meta"

        if not test -d "$meta_dir"
            echo "Creating _meta directory..."
            mkdir -p "$meta_dir"
            or begin
                echo "Error: Failed to create _meta directory"
                return 1
            end
        end
    end

    function cleanup_temp
        set -l temp_files $argv
        rm -f $temp_files
    end

    function get_all_packages
        set -l temp_file $argv[1]

        echo "Listing explicitly installed packages..."
        pacman -Qe | awk '{print $1}' > "$temp_file"
        or begin
            echo "Error: Failed to list explicitly installed packages"
            return 1
        end
    end

    function get_aur_packages
        set -l temp_file $argv[1]

        echo "Listing explicitly installed AUR packages..."
        pacman -Qem | awk '{print $1}' > "$temp_file"
        or begin
            echo "Error: Failed to list AUR packages"
            return 1
        end
    end

    function save_package_files
        set -l temp_all $argv[1]
        set -l temp_aur $argv[2]
        set -l pacman_file $argv[3]
        set -l aur_file $argv[4]

        echo "Saving AUR packages..."
        cp "$temp_aur" "$aur_file"
        or begin
            echo "Error: Failed to write $aur_file"
            return 1
        end

        echo "Saving official pacman packages..."
        if test -s "$temp_aur"
            grep -Fxv -f "$temp_aur" "$temp_all" > "$pacman_file"
            or begin
                echo "Error: Failed to filter official packages"
                return 1
            end
        else
            cp "$temp_all" "$pacman_file"
            or begin
                echo "Error: Failed to write $pacman_file"
                return 1
            end
        end
    end

    function validate_output
        set -l pacman_file $argv[1]
        set -l aur_file $argv[2]

        if not test -f "$pacman_file" -a -f "$aur_file"
            echo "Error: Failed to create package files"
            return 1
        end
    end

    function show_summary
        set -l pacman_file $argv[1]
        set -l aur_file $argv[2]

        set -l pacman_count (wc -l < "$pacman_file" 2>/dev/null || echo "0")
        set -l aur_count (wc -l < "$aur_file" 2>/dev/null || echo "0")

        echo "Packages saved:"
        echo "  - Official packages: $pacman_count ($pacman_file)"
        echo "  - AUR packages: $aur_count ($aur_file)"
    end

    if not validate_environment
        return 1
    end

    if not setup_directories
        return 1
    end

    set -l pacman_file "$DOTFILES_PATH/_meta/pacman-packages.txt"
    set -l aur_file "$DOTFILES_PATH/_meta/yay-packages.txt"
    set -l temp_all (mktemp)
    set -l temp_aur (mktemp)

    if not get_all_packages "$temp_all"
        cleanup_temp "$temp_all" "$temp_aur"
        return 1
    end

    if not get_aur_packages "$temp_aur"
        cleanup_temp "$temp_all" "$temp_aur"
        return 1
    end

    if not save_package_files "$temp_all" "$temp_aur" "$pacman_file" "$aur_file"
        cleanup_temp "$temp_all" "$temp_aur"
        return 1
    end

    cleanup_temp "$temp_all" "$temp_aur"

    if not validate_output "$pacman_file" "$aur_file"
        return 1
    end

    show_summary "$pacman_file" "$aur_file"
end
