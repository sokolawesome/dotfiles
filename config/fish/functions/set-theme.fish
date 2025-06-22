function set-theme -d "Apply a new theme based on a wallpaper"
    function generate_gtk_css -d "Generate CSS for GTK themes from pywal JSON"
        set -l json_file "$HOME/.cache/wal/pywal.json"

        if not test -f "$json_file"
            echo "Error: pywal.json not found"
            return 1
        end

        set -l theme_data (cat "$json_file" | jq -r '.' 2>/dev/null)
        if test $status -ne 0
            echo "Error: Failed to parse pywal.json"
            return 1
        end

        set -l css_vars ""
        set -l variables (echo "$theme_data" | jq -r '.variables // {} | to_entries[] | "\(.key):\(.value)"' 2>/dev/null)
        if test $status -ne 0
            echo "Error: Failed to extract variables from theme data"
            return 1
        end

        for var in $variables
            set -l key (echo "$var" | cut -d: -f1)
            set -l value (echo "$var" | cut -d: -f2-)
            set css_vars "$css_vars@define-color $key $value;\n"
        end

        set -l sidebar_bg (echo "$theme_data" | jq -r '.variables.sidebar_bg_color // empty' 2>/dev/null)
        if test -z "$sidebar_bg"
            set -l window_bg (echo "$theme_data" | jq -r '.variables.window_bg_color // "#ffffff"' 2>/dev/null)
            set -l window_fg (echo "$theme_data" | jq -r '.variables.window_fg_color // "#000000"' 2>/dev/null)
            set -l view_bg (echo "$theme_data" | jq -r '.variables.view_bg_color // "#ffffff"' 2>/dev/null)
            set -l headerbar_shade (echo "$theme_data" | jq -r '.variables.headerbar_shade_color // "#000000"' 2>/dev/null)

            set css_vars "$css_vars@define-color sidebar_bg_color $window_bg;\n"
            set css_vars "$css_vars@define-color sidebar_fg_color $window_fg;\n"
            set css_vars "$css_vars@define-color sidebar_backdrop_color $view_bg;\n"
            set css_vars "$css_vars@define-color sidebar_shade_color $headerbar_shade;\n"
        end

        set -l css_palette ""
        set -l palette_exists (echo "$theme_data" | jq -r '.palette // empty | length' 2>/dev/null)
        if test -n "$palette_exists"
            set -l tints (echo "$theme_data" | jq -r '.palette | keys[]' 2>/dev/null)
            for tint in $tints
                set -l colors (echo "$theme_data" | jq -r ".palette.$tint | to_entries[] | \"\(.key):\(.value)\"" 2>/dev/null)
                for color in $colors
                    set -l index (echo "$color" | cut -d: -f1)
                    set -l value (echo "$color" | cut -d: -f2-)
                    set css_palette "$css_palette@define-color $tint$index $value;\n"
                end
            end
        end

        set -l base_css "$css_vars$css_palette"
        set -l gtk3_css "$base_css"
        set -l gtk4_css "$base_css"

        set -l custom_gtk3 (echo "$theme_data" | jq -r '.custom_css.gtk3 // empty' 2>/dev/null)
        set -l custom_gtk4 (echo "$theme_data" | jq -r '.custom_css.gtk4 // empty' 2>/dev/null)

        if test -n "$custom_gtk3"
            set gtk3_css "$gtk3_css\n$custom_gtk3"
        end
        if test -n "$custom_gtk4"
            set gtk4_css "$gtk4_css\n$custom_gtk4"
        end

        set -l config_dir (string replace -r '^$' "$HOME/.config" -- "$XDG_CONFIG_HOME")
        set -l gtk3_dir "$config_dir/gtk-3.0"
        set -l gtk4_dir "$config_dir/gtk-4.0"

        mkdir -p "$gtk3_dir" "$gtk4_dir"
        printf "$gtk3_css" > "$gtk3_dir/gtk.css"
        printf "$gtk4_css" > "$gtk4_dir/gtk.css"
    end

    function check_dependencies -d "Check if required tools are available"
        set -l missing_tools

        for tool in wal jq
            if not type -q $tool
                set -a missing_tools $tool
            end
        end

        if test (count $missing_tools) -gt 0
            echo "Error: Missing required tools: "(string join ", " $missing_tools)
            return 1
        end
    end

    set -l backend "wal"
    set -l wallpaper_path ""

    argparse 'b/backend=' 'h/help' -- $argv
    or return 1

    if set -q _flag_help
        echo "Usage: set-theme [WALLPAPER] [-b|--backend wal|haishoku]"
        return 0
    end

    if not check_dependencies
        return 1
    end

    if set -q _flag_backend
        set backend $_flag_backend
        if not contains $backend wal haishoku
            echo "Error: Unsupported backend '$backend'. Use 'wal' or 'haishoku'."
            return 1
        end
    end

    if set -q argv[1]
        set wallpaper_path $argv[1]
    else
        echo "No wallpaper provided. Launching selector..."

        if not test -d ~/wallpapers
            echo "Error: ~/wallpapers directory not found"
            return 1
        end

        if not type -q fzf
            echo "Error: fzf is required for interactive wallpaper selection but was not found."
            return 1
        end

        set wallpaper_path (find ~/wallpapers -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | fzf)
        if test -z "$wallpaper_path"
            echo "No wallpaper selected."
            return 1
        end
    end

    if not test -f "$wallpaper_path"
        echo "Error: Wallpaper file not found at '$wallpaper_path'"
        return 1
    end

    echo "Generating color scheme from $wallpaper_path using backend '$backend'..."
    command wal -i "$wallpaper_path" --backend "$backend" --contrast 5 &> /dev/null
    or begin
        echo "Error: Failed to generate color scheme with wal"
        return 1
    end

    echo "Applying GTK theme..."
    if not generate_gtk_css
        echo "Error: Failed to generate GTK CSS"
        return 1
    end

    echo "Applying Kvantum theme..."
    mkdir -p "$HOME/.config/Kvantum/pywal"
    command cp "$HOME/.cache/wal/pywal.kvconfig" "$HOME/.config/Kvantum/pywal/pywal.kvconfig"
    and command cp "$HOME/.cache/wal/pywal.svg" "$HOME/.config/Kvantum/pywal/pywal.svg"
    or begin
        echo "Error: Failed to apply Kvantum theme"
        return 1
    end

    echo "Updating Zed theme..."
    command cp "$HOME/.cache/wal/colors-zed.json" "$HOME/.config/zed/themes/colors-zed.json"
    or begin
        echo "Error: Failed to update Zed theme"
        return 1
    end

    echo "Applying Zen theme..."
    command pywalfox update
    or begin
        echo "Error: Failed to apply Zen theme"
        return 1
    end

    echo "Updating Telegram theme..."
    command walogram &> /dev/null
    and command killall Telegram &> /dev/null
    hyprctl dispatch exec "Telegram" &> /dev/null
    if test $status -ne 0
        echo "Error: Failed to update Telegram theme"
        return 1
    end

    echo "Reloading services..."
    command makoctl reload
    or begin
        echo "Error: Failed to reload mako"
        return 1
    end

    echo "Theme applied successfully!"
end
