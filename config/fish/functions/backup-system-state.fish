function backup-system-state -d "save explicitly installed pacman and aur packages, user groups, and services to separate files in dotfiles directory"
    function validate-environment
        if not set -q DOTFILES_PATH
            echo "error: \$DOTFILES_PATH is not set"
            return 1
        end

        if not test -d "$DOTFILES_PATH"
            echo "error: dotfiles directory '$DOTFILES_PATH' does not exist"
            return 1
        end

        if not command -q pacman
            echo "error: pacman is not installed or not in path"
            return 1
        end
    end

    function setup-directories
        set -l other_dir "$DOTFILES_PATH/other"

        if not test -d "$other_dir"
            echo "creating 'other' directory..."
            mkdir -p "$other_dir" || return 1
        end
    end

    function get-packages
        set -l output_file $argv[1]
        set -l package_type $argv[2]

        switch $package_type
            case all
                pacman -Qe | awk '{print $1}' > "$output_file"
            case aur
                pacman -Qem | awk '{print $1}' > "$output_file"
            case '*'
                return 1
        end
    end

    function get-user-groups
        set -l groups_file $argv[1]
        groups | tr ' ' '\n' | sort > "$groups_file"
    end

    function get-enabled-services
        set -l services_file $argv[1]

        begin
            echo "# system services"
            systemctl list-unit-files --state=enabled --no-pager --no-legend | awk '{print $1}' | grep -v "^\$"
            echo ""
            echo "# user services"
            systemctl --user list-unit-files --state=enabled --no-pager --no-legend 2>/dev/null | awk '{print $1}' | grep -v "^\$"
        end > "$services_file"
    end

    function compare-and-update
        set -l temp_file $argv[1]
        set -l target_file $argv[2]
        set -l description $argv[3]

        if test -f "$target_file"
            if cmp -s "$temp_file" "$target_file"
                return 1
            else
                echo "updating $description..."
                cp "$temp_file" "$target_file" || return 2
            end
        else
            echo "creating $description file '$target_file'..."
            cp "$temp_file" "$target_file" || return 2
        end
        return 0
    end

    function save-package-files
        set -l temp_all $argv[1]
        set -l temp_aur $argv[2]
        set -l pacman_file $argv[3]
        set -l aur_file $argv[4]

        set -l changed_files 0

        if compare-and-update "$temp_aur" "$aur_file" "aur packages"
            set -l status $status
            if test $status -eq 0
                set changed_files (math $changed_files + 1)
            else if test $status -eq 2
                return 1
            end
        end

        set -l temp_pacman (mktemp)
        if test -s "$temp_aur"
            grep -Fxv -f "$temp_aur" "$temp_all" > "$temp_pacman" || return 1
        else
            cp "$temp_all" "$temp_pacman" || return 1
        end

        if compare-and-update "$temp_pacman" "$pacman_file" "official pacman packages"
            set -l status $status
            if test $status -eq 0
                set changed_files (math $changed_files + 1)
            else if test $status -eq 2
                rm -f "$temp_pacman"
                return 1
            end
        end

        rm -f "$temp_pacman"
        echo $changed_files
        return 0
    end

    function show-summary
        set -l pacman_file $argv[1]
        set -l aur_file $argv[2]
        set -l groups_file $argv[3]
        set -l services_file $argv[4]
        set -l total_changes $argv[5]

        set -l pacman_count (wc -l < "$pacman_file" 2>/dev/null || echo "0")
        set -l aur_count (wc -l < "$aur_file" 2>/dev/null || echo "0")
        set -l groups_count (wc -l < "$groups_file" 2>/dev/null || echo "0")
        set -l services_count (grep -v "^#\|^\$" "$services_file" 2>/dev/null | wc -l || echo "0")

        echo "---"
        echo "workspace data summary:"
        echo "  - official packages: $pacman_count"
        echo "  - aur packages: $aur_count"
        echo "  - user groups: $groups_count"
        echo "  - enabled services: $services_count"
        echo ""

        if test $total_changes -eq 0
            echo "no changes detected in any workspace configuration files."
        else
            echo "changes detected and configuration files updated."
        end
    end

    if not validate-environment
        return 1
    end

    if not setup-directories
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

    set -l total_changes 0

    echo "collecting explicitly installed packages..."
    if not get-packages "$temp_all" all
        rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    echo "collecting explicitly installed aur packages..."
    if not get-packages "$temp_aur" aur
        rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    set -l package_changes (save-package-files "$temp_all" "$temp_aur" "$pacman_file" "$aur_file")
    if test $status -ne 0
        rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end
    set total_changes (math $total_changes + $package_changes)

    echo "collecting user groups..."
    if not get-user-groups "$temp_groups"
        rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if compare-and-update "$temp_groups" "$groups_file" "user groups"
        if test $status -eq 0
            set total_changes (math $total_changes + 1)
        else
            rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
            return 1
        end
    end

    echo "collecting enabled systemd services..."
    if not get-enabled-services "$temp_services"
        rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
        return 1
    end

    if compare-and-update "$temp_services" "$services_file" "enabled services"
        if test $status -eq 0
            set total_changes (math $total_changes + 1)
        else
            rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"
            return 1
        end
    end

    rm -f "$temp_all" "$temp_aur" "$temp_groups" "$temp_services"

    show-summary "$pacman_file" "$aur_file" "$groups_file" "$services_file" $total_changes
end
