function code2clip -d "generate content from directory and copy to clipboard"
    function validate-environment
        for cmd in tree find wl-copy
            if not command -q $cmd
                echo "error: '$cmd' not found, install it with your package manager."
                return 1
            end
        end
    end

    function validate-directory
        set -l dir $argv[1]
        if not test -d "$dir"
            echo "error: directory '$dir' not found."
            return 1
        end
    end

    function get-basic-exclude-pattern
        echo '\.git/|\.DS_Store|\.idea/|\.vscode/|\.zed/|\.lock$|\.svg$|\.gitignore$'
    end

    function get-preset-exclude-pattern
        set -l preset $argv[1]

        switch $preset
            case web
                echo 'node_modules/|dist/|build/|\.cache/|\.next/|\.nuxt/|coverage/|\.nyc_output/|\.parcel-cache/'
            case go
                echo 'bin/|pkg/|vendor/|go\.mod$|go\.sum$|\.test$'
            case rust
                echo 'target/|Cargo\.lock$|\.cargo/'
            case dotnet
                echo 'bin/|obj/|\.vs/|packages/|\.nuget/|TestResults/|\.user$|\.suo$'
            case '*'
                echo ""
        end
    end

    function build-exclude-pattern
        set -l preset_or_custom $argv[1]
        set -l basic_pattern (get-basic-exclude-pattern)

        if test -z "$preset_or_custom"
            echo "$basic_pattern"
        else
            set -l preset_pattern (get-preset-exclude-pattern "$preset_or_custom")

            if test -z "$preset_pattern"
                echo "$basic_pattern|$preset_or_custom"
            else
                echo "$basic_pattern|$preset_pattern"
            end
        end
    end

    function generate-tree-structure
        set -l dir $argv[1]
        set -l exclude $argv[2]
        echo "## directory structure"

        if test -f "$dir/.gitignore"
            set -l gitignore_patterns (cat "$dir/.gitignore" | grep -v '^#' | grep -v '^$' | tr '\n' '|' | sed 's/|$//')
            if test -n "$gitignore_patterns"
                set exclude "$exclude|$gitignore_patterns"
            end
        end

        tree -a -I "$exclude" --noreport -L 3 "$dir" || return 1
    end

    function print-file-content
        set -l file $argv[1]
        set -l ext (string match -r '.*\.([^.]+)$' (basename "$file") | string replace -r '^.*\.' '' | string lower)

        echo ""
        echo "### '$file'"
        echo "```$ext"
        cat "$file"
        echo "```"
        echo ""
    end

    function generate-file-contents
        set -l dir $argv[1]
        set -l exclude $argv[2]

        echo ""
        echo "## file contents"

        find "$dir" -type f -print0 | grep -vzE "$exclude" | while read -z file
            if test -f "$file" -a -r "$file"
                if test -f "$dir/.gitignore"
                    if git -C "$dir" check-ignore "$file" > /dev/null 2>&1
                        continue
                    end
                end

                grep -Iq . "$file" || continue
                print-file-content "$file"
            end
        end
    end

    function generate-content
        set -l dir $argv[1]
        set -l exclude $argv[2]
        set -l show_tree $argv[3]

        if test "$show_tree" = true
            generate-tree-structure "$dir" "$exclude" || return 1
        end

        generate-file-contents "$dir" "$exclude" || return 1
    end

    function output-content
        set -l content $argv[1]
        set -l mode $argv[2]

        if test "$mode" = "stdout"
            echo "$content"
        else
            echo "$content" | wl-copy
            or begin
                echo "error: failed to copy to clipboard"
                return 1
            end
            echo "content successfully copied to clipboard!"
        end
    end

    if not validate-environment
        return 1
    end

    argparse 'e/exclude=' 'o/output=' 'h/help' 't/no-tree' -- $argv || return 1

    if set -q _flag_help
        echo "usage: code2clip [OPTIONS] <DIRECTORY>"
        echo "generate content from directory and copy to clipboard or stdout."
        echo ""
        echo "options:"
        echo "  -e, --exclude <NAME|REGEX>   exclude pattern or preset"
        echo "                               presets: web, go, rust, dotnet"
        echo "  -o, --output <MODE>          output mode: clipboard (default) or stdout"
        echo "  -t, --no-tree                do not include dir tree structure"
        echo "  -h, --help                   show this help message"
        echo ""
        echo "arguments:"
        echo "  DIRECTORY                    directory to process (required)"
        return 0
    end

    if test (count $argv) -eq 0
        echo "error: missing directory argument"
        return 1
    end

    set -l dir (realpath "$argv[1]")
    if not validate-directory "$dir"
        return 1
    end

    set -l exclude (build-exclude-pattern "$_flag_exclude")
    set -l output_mode "clipboard"
    if set -q _flag_output
        set output_mode $_flag_output
    end

    set -l show_tree true
    if set -q _flag_no_tree
        set show_tree false
    end

    echo "generating content from "(basename "$dir")"..."
    set -l content (generate-content "$dir" "$exclude" "$show_tree" | string collect)
    or return 1

    output-content "$content" "$output_mode"
end
