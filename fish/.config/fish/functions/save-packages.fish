function save-packages -d "Save explicitly installed pacman and AUR packages to separate files in dotfiles directory"
    # Ensure DOTFILES_PATH is set and valid
    if not set -q DOTFILES_PATH
        echo "Error: \$DOTFILES_PATH is not set"
        return 1
    end

    if not test -d "$DOTFILES_PATH"
        echo "Error: Dotfiles directory '$DOTFILES_PATH' does not exist"
        return 1
    end

    # Ensure pacman is available
    if not command -q pacman
        echo "Error: pacman is not installed or not in PATH"
        return 1
    end

    # Output paths
    set -l pacman_file "$DOTFILES_PATH/_meta/pacman-packages.txt"
    set -l yay_file "$DOTFILES_PATH/_meta/yay-packages.txt"

    # Temporary files
    set -l temp_all (mktemp)
    set -l temp_yay (mktemp)

    echo "Listing explicitly installed packages..."

    pacman -Qe | awk '{print $1}' > "$temp_all"
    or begin
        echo "Error: Failed to list explicitly installed packages"
        rm -f "$temp_all" "$temp_yay"
        return 1
    end

    echo "Listing explicitly installed AUR packages..."

    pacman -Qem | awk '{print $1}' > "$temp_yay"
    or begin
        echo "Error: Failed to list AUR packages"
        rm -f "$temp_all" "$temp_yay"
        return 1
    end

    echo "Saving AUR packages..."
    cp "$temp_yay" "$yay_file"
    or begin
        echo "Error: Failed to write $yay_file"
        rm -f "$temp_all" "$temp_yay"
        return 1
    end

    echo "Saving official pacman packages..."
    if test -s "$temp_yay"
        # Exclude AUR packages from all packages
        grep -Fxv -f "$temp_yay" "$temp_all" > "$pacman_file"
    else
        cp "$temp_all" "$pacman_file"
    end

    or begin
        echo "Error: Failed to write $pacman_file"
        rm -f "$temp_all" "$temp_yay"
        return 1
    end

    rm -f "$temp_all" "$temp_yay"

    echo "Packages saved:"
    echo "  - $pacman_file"
    echo "  - $yay_file"
end
