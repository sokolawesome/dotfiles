function set-theme -d "Apply a new theme based on a wallpaper"
    # Check if wallpaper path is provided
    if not set -q argv[1]
        echo "Usage: set_theme /path/to/wallpaper.png"
        return 1
    end

    set wallpaper_path $argv[1]

    # Validate wallpaper file
    if not test -f "$wallpaper_path"
        echo "Error: Wallpaper file not found at '$wallpaper_path'"
        return 1
    end

    # Generate color scheme with pywal16
    echo "Generating color scheme from $wallpaper_path..."
    wal -i "$wallpaper_path" &> /dev/null
    or begin
        echo "Error: Failed to generate color scheme with wal"
        return 1
    end

    # Apply Kvantum theme
    echo "Applying Kvantum theme..."
    mkdir -p "$HOME/.config/Kvantum/pywal"
    cp "$HOME/.cache/wal/pywal.kvconfig" "$HOME/.config/Kvantum/pywal/pywal.kvconfig"
    cp "$HOME/.cache/wal/pywal.svg" "$HOME/.config/Kvantum/pywal/pywal.svg"
    or begin
        echo "Error: Failed to apply Kvantum theme"
        return 1
    end

    # Update Zed theme in dotfiles
    echo "Updating Zed theme in dotfiles..."
    cp "$HOME/.cache/wal/colors-zed.json" "$HOME/.config/zed/themes/colors-zed.json"
    or begin
        echo "Error: Failed to update Zed theme"
        return 1
    end

    # Reload services
    echo "Reloading services..."
    makoctl reload
    or begin
        echo "Error: Failed to reload mako"
        return 1
    end

    echo "Theme applied successfully!"
end
