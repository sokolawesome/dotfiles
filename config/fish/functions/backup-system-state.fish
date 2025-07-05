function backup-system-state -d "Save explicitly installed pacman and AUR packages, user groups, and services to separate files in dotfiles directory"
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
        set -l other_dir "$DOTFILES_PATH/other"

        if not test -d "$other_dir"
            echo "creating 'other' directory..."
            mkdir -p "$other_dir"
            or begin
                echo "error: failed to create 'other' directory"
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

        echo "collecting explicitly installed packages..."
        pacman -Qe | awk '{print $1}' > "$temp_file"
        or begin
            echo "error: failed to list explicitly installed packages"
            return 1
        end
    end

    function get_aur_packages
        set -l temp_file $argv[1]

        echo "collecting explicitly installed AUR packages..."
        pacman -Qem | awk '{print $1}' > "$temp_file"
        or begin
            echo "error: failed to list AUR packages"
            return 1
        end
    end

    function get_user_groups
        set -l groups_file $argv[1]

        echo "collecting user groups..."
        groups | tr ' ' '\n' | sort > "$groups_file"
        or begin
            echo "error: failed to save user groups"
            return 1
        end
    end

    function get_enabled_services
        set -l services_file $argv[1]

        echo "collecting enabled systemd services..."
        begin
            echo "# System services"
            systemctl list-unit-files --state=enabled --no-pager --no-legend | awk '{print $1}' | grep -v "^\$"
            echo ""
            echo "# User services"
            systemctl --user list-unit-files --state=enabled --no-pager --no-legend 2>/dev/null | awk '{print $1}' | grep -v "^\$"
        end > "$services_file"
        or begin
            echo "error: failed to save systemd services"
            return 1
        end
    end

    function compare_and_save_file
        set -l temp_file $argv[1]
        set -l target_file $argv[2]
        set -l description $argv[3]
        set -l changed_var_name $argv[4]

        if test -f "$target_file"
            if cmp -s "$temp_file" "$target_file"
                # No change, do nothing
                set -g $changed_var_name 0
            else
                echo "updating $description..."
                cp "$temp_file" "$target_file"
                or begin
                    echo "error: failed to write $target_file"
                    return 1
                end
                set -g $changed_var_name 1
            end
        else
            echo "creating $description file '$target_file'..."
            cp "$temp_file" "$target_file"
            or begin
                echo "error: failed to write $target_file"
                return 1
            end
            set -g $changed_var_name 1
        end
        return 0
    end

    function save_package_files
        set -l temp_all $argv[1]
        set -l temp_aur $argv[2]
        set -l pacman_file $argv[3]
        set -l aur_file $argv[4]
        set -l pacman_changed_var $argv[5]
        set -l aur_changed_var $argv[6]

        set -g $aur_changed_var 0
        set -g $pacman_changed_var 0

        # Save AUR packages
        if not compare_and_save_file "$temp_aur" "$aur_file" "AUR packages" $aur_changed_var
            return 1
        end

        # Determine official pacman packages
        set -l temp_pacman_filtered (mktemp)
        if test -s "$temp_aur"
            grep -Fxv -f "$temp_aur" "$temp_all" > "$temp_pacman_filtered"
            or begin
                echo "error: failed to filter official packages"
                cleanup_temp "$temp_pacman_filtered"
                return 1
            end
        else
            cp "$temp_all" "$temp_pacman_filtered"
            or begin
                echo "error: failed to copy all packages for official calculation"
                cleanup_temp "$temp_pacman_filtered"
                return 1
            end
        end

        # Save official pacman packages
        if not compare_and_save_file "$temp_pacman_filtered" "$pacman_file" "official pacman packages" $pacman_changed_var
            cleanup_temp "$temp_pacman_filtered"
            return 1
        end
        cleanup_temp "$temp_pacman_filtered"
        return 0
    end

    function validate_output
        set -l files $argv

        for file in $files
            if not test -f "$file"
                echo "Error: Failed to create $file"
                return 1
            end
        end
    end

    function show_summary
        set -l pacman_file $argv[1]
        set -l aur_file $argv[2]
        set -l groups_file $argv[3]
        set -l services_file $argv[4]
        set -l changed_status $argv[5]

        set -l pacman_count (wc -l < "$pacman_file" 2>/dev/null || echo "0")
        set -l aur_count (wc -l < "$aur_file" 2>/dev/null || echo "0")
        set -l groups_count (wc -l < "$groups_file" 2>/dev/null || echo "0")
        set -l services_count (grep -v "^#\|^\$" "$services_file" 2>/dev/null | wc -l || echo "0")

        echo "---" # Separator for clarity
        echo "Workspace data summary:"
        echo "  - Official packages: $pacman_count"
        echo "  - AUR packages: $aur_count"
        echo "  - User groups: $groups_count"
        echo "  - Enabled services: $services_count"
        echo ""

        if test "$changed_status" = "0"
            echo "no changes detected in any workspace configuration files."
        else
            echo "changes detected and configuration files updated."
        end
    end

    if not validate_environment
        return 1
    end

    if not setup_directories
        return 1
    end

    set -l pacman_file "$DOTFILES_PATH/other/pacman-packages.txt"
    set -l aur_file "$DOTFILES_PATH/other/yay-packages.txt"
    set -l groups_file "$DOTFILES_PATH/other/user-groups.txt"
    set -l services_file "$DOTFILES_PATH/other/enabled-services.txt"

    set -l temp_all (mktemp)
    set -l temp_aur (mktemp)
    set -l temp_groups (mktemp)
    set -l temp_services (mktemp)

    set -g changed_pacman 0
    set -g changed_aur 0
    set -g changed_groups 0
    set -g changed_services 0
    set -g any_file_changed 0

    if not get_all_packages "$temp_all"
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not get_aur_packages "$temp_aur"
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not save_package_files "$temp_all" "$temp_aur" "$pacman_file" "$aur_file" changed_pacman changed_aur
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not get_user_groups "$temp_groups"
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not compare_and_save_file "$temp_groups" "$groups_file" "user groups" changed_groups
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not get_enabled_services "$temp_services"
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if not compare_and_save_file "$temp_services" "$services_file" "enabled services" changed_services
        cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    cleanup_temp "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"

    if test "$changed_pacman" = "1" -o "$changed_aur" = "1" -o "$changed_groups" = "1" -o "$changed_services" = "1"
        set -g any_file_changed 1
    end

    if not validate_output "$pacman_file" "$aur_file" "$groups_file" "$services_file"
        return 1
    end

    show_summary "$pacman_file" "$aur_file" "$groups_file" "$services_file" "$any_file_changed"
end
