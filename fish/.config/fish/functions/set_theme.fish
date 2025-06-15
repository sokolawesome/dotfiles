function set_theme -d "Apply a new theme based on a wallpaper"
    if not set -q argv[1]
        echo "Usage: set_theme /path/to/wallpaper.png"
        return 1
    end

    set wallpaper_path $argv[1]

    if not test -f "$wallpaper_path"
        echo "Error: Wallpaper file not found at '$wallpaper_path'"
        return 1
    end

    if not set -q DOTFILES_PATH
        echo "Error: \$DOTFILES_PATH is not set"
        return 1
    end

    echo "Generating color scheme from $wallpaper_path..."
    wal -i "$wallpaper_path" &> /dev/null

    echo "Applying Kvantum theme..."
    mkdir -p "$HOME/.config/Kvantum/pywal"
    cp "$HOME/.cache/wal/pywal.kvconfig" "$HOME/.config/Kvantum/pywal/pywal.kvconfig"
    cp "$HOME/.cache/wal/pywal.svg" "$HOME/.config/Kvantum/pywal/pywal.svg"


    echo "Updating Zed theme in dotfiles..."
    cp "$HOME/.cache/wal/colors-zed.json" "$DOTFILES_PATH/zed/.config/zed/themes/colors-zed.json"

    echo "Reloading services..."
    makoctl reload

    echo "Theme applied successfully!"
end
