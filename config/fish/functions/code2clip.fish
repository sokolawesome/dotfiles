function code2clip -d "Generate content from directory and copy to clipboard"
    function _code2clip_validate_directory
        set -l target_dir $argv[1]
        if not test -d "$target_dir"
            echo "Error: Directory '$target_dir' not found." >&2
            return 1
        end
    end

    function _code2clip_check_dependencies
        if not command -s tree > /dev/null
            echo "Error: 'tree' command not found. Install it with your package manager (e.g., 'sudo apt install tree')." >&2
            return 1
        end
        if not command -s find > /dev/null
            echo "Error: 'find' command not found." >&2
            return 1
        end
        if not command -s wl-copy > /dev/null
            echo "Error: 'wl-copy' command not found. Install wl-clipboard package (e.g., 'sudo apt install wl-clipboard')." >&2
            return 1
        end
    end

    function _code2clip_build_exclude_pattern
        set -l custom_exclude $argv[1]
        set -l default_exclude '\.git/|node_modules/|dist/|\.cache/|\.next/|\.idea/|\.vscode/|\.DS_Store|__pycache__/|\.lock$|\.sum$|\.svg$|\.kvconfig$|pywal\.json$|\.code\.md$|\.gitignore$|\.golangci\.yml$|^\.git$'

        if test -n "$custom_exclude"
            echo "$custom_exclude"
        else
            echo "$default_exclude"
        end
    end

    function _code2clip_generate_tree_structure
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        echo "## Directory Structure"
        tree -a -I "$exclude_pattern" --noreport -L 3 "$target_dir"
        or begin
            echo "Error: Failed to generate directory tree for '$target_dir'." >&2
            return 1
        end
    end

    function _code2clip_print_file
        set -l file $argv[1]
        set -l ext (string match -r '.*\.([^.]+)$' (basename "$file") | string replace -r '^.*\.' '' | string lower)
        echo ""
        echo "### File: '$file'"
        if test -n "$ext"
            echo "```$ext"
        else
            echo "```"
        end
        cat "$file"
        echo "```"
        echo ""
    end

    function _code2clip_generate_file_contents
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        echo "## File Contents"

        find "$target_dir" -type f -print0 | \
            grep -zvE "$exclude_pattern" | \
            while read -z file
                if test -f "$file" -a -r "$file"
                    if test -f "$target_dir/.gitignore"
                        git -C "$target_dir" check-ignore "$file" > /dev/null 2>&1
                        and continue
                    end

                    grep -Iq . "$file"
                    or continue

                    _code2clip_print_file "$file"
                end
            end
    end

    function _code2clip_generate_content
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        set -l tree_output (begin; _code2clip_generate_tree_structure "$target_dir" "$exclude_pattern"; end | string collect)
        if test $status -ne 0
            return 1
        end
        echo "$tree_output"

        set -l file_contents_output (begin; _code2clip_generate_file_contents "$target_dir" "$exclude_pattern"; end | string collect)
        if test $status -ne 0
            return 1
        end
        echo "$file_contents_output"
    end

    set -l target_dir ""
    set -l exclude_pattern ""
    set -l output_mode "clipboard"

    argparse 'e/exclude=' 'h/help' 'o/output=' -- $argv
    or return 1

    if set -q _flag_help
        echo "Usage: code2clip [OPTIONS] <DIRECTORY>"
        echo "Generate content from directory and copy to clipboard or stdout."
        echo ""
        echo "Options:"
        echo "  -e, --exclude <PATTERN>   Regex pattern to exclude files/directories"
        echo "                            (overrides default exclusions)"
        echo "  -o, --output <MODE>       Output mode: clipboard (default) or stdout"
        echo "  -h, --help                Show this help message"
        echo ""
        echo "Arguments:"
        echo "  DIRECTORY                 Directory to process (REQUIRED)"
        return 0
    end

    if test (count $argv) -eq 0
        echo "Error: Directory argument is required." >&2
        echo "Use 'code2clip --help' for usage information." >&2
        return 1
    end

    if test -n "$_flag_output"
        set output_mode "$_flag_output"
    end

    if not _code2clip_check_dependencies
        return 1
    end

    set target_dir (realpath "$argv[1]")
    if not _code2clip_validate_directory "$target_dir"
        return 1
    end

    set exclude_pattern (_code2clip_build_exclude_pattern "$_flag_exclude")

    echo "Generating content from "(basename "$target_dir")" directory..."

    set -l content (begin; _code2clip_generate_content "$target_dir" "$exclude_pattern"; end | string collect)
    if test $status -ne 0
        echo "Error: Content generation failed." >&2
        return 1
    end

    if test "$output_mode" = "stdout"
        echo "$content"
    else
        echo "$content" | wl-copy
        or begin
            echo "Error: Failed to copy to clipboard. Is 'wl-copy' working correctly?" >&2
            return 1
        end
        echo "Content successfully copied to clipboard!"
    end
end
