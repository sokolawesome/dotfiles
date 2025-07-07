function code2clip -d "generate content from directory and copy to clipboard"
    function validate-environment
        if not command -q tree
            echo "error: 'tree' command not found. install it with your package manager."
            return 1
        end

        if not command -q find
            echo "error: 'find' command not found."
            return 1
        end

        if not command -q wl-copy
            echo "error: 'wl-copy' command not found. install wl-clipboard package."
            return 1
        end
    end

    function validate-directory
        set -l target_dir $argv[1]
        if not test -d "$target_dir"
            echo "error: directory '$target_dir' not found."
            return 1
        end
    end

    function build-exclude-pattern
        set -l custom_exclude $argv[1]
        set -l default_exclude '\.git/|node_modules/|dist/|\.cache/|\.next/|\.idea/|\.vscode/|\.DS_Store|__pycache__/|\.lock$|\.sum$|\.svg$|\.kvconfig$|pywal\.json$|\.code\.md$|\.gitignore$|\.golangci\.yml$|^\.git$'

        if test -n "$custom_exclude"
            echo "$custom_exclude"
        else
            echo "$default_exclude"
        end
    end

    function generate-tree-structure
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        echo "## directory structure"
        tree -a -I "$exclude_pattern" --noreport -L 3 "$target_dir" || return 1
    end

    function print-file-content
        set -l file $argv[1]
        set -l ext (string match -r '.*\.([^.]+)$' (basename "$file") | string replace -r '^.*\.' '' | string lower)

        echo ""
        echo "### '$file'"
        if test -n "$ext"
            echo "```$ext"
        else
            echo "```"
        end
        cat "$file"
        echo "```"
        echo ""
    end

    function generate-file-contents
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        echo ""
        echo "## file contents"

        find "$target_dir" -type f -print0 | \
            grep -vzE "$exclude_pattern" | \
            while read -z file
                if test -f "$file" -a -r "$file"
                    if test -f "$target_dir/.gitignore"
                        git -C "$target_dir" check-ignore "$file" > /dev/null 2>&1
                        and continue
                    end

                    grep -Iq . "$file" || continue
                    print-file-content "$file"
                end
            end
    end

    function generate-content
        set -l target_dir $argv[1]
        set -l exclude_pattern $argv[2]

        generate-tree-structure "$target_dir" "$exclude_pattern" || return 1
        generate-file-contents "$target_dir" "$exclude_pattern" || return 1
    end

    function output-content
        set -l content $argv[1]
        set -l output_mode $argv[2]

        if test "$output_mode" = "stdout"
            echo "$content"
        else
            echo "$content" | wl-copy || begin
                echo "error: failed to copy to clipboard. is 'wl-copy' working correctly?"
                return 1
            end
            echo "content successfully copied to clipboard!"
        end
    end

    if not validate-environment
        return 1
    end

    argparse 'e/exclude=' 'h/help' 'o/output=' -- $argv || return 1

    if set -q _flag_help
        echo "usage: code2clip [OPTIONS] <DIRECTORY>"
        echo "generate content from directory and copy to clipboard or stdout."
        echo ""
        echo "options:"
        echo "  -e, --exclude <PATTERN>   regex pattern to exclude files/directories"
        echo "                            (overrides default exclusions)"
        echo "  -o, --output <MODE>       output mode: clipboard (default) or stdout"
        echo "  -h, --help                show this help message"
        echo ""
        echo "arguments:"
        echo "  DIRECTORY                 directory to process (required)"
        return 0
    end

    if test (count $argv) -eq 0
        echo "error: directory argument is required."
        echo "use 'code2clip --help' for usage information."
        return 1
    end

    set -l target_dir (realpath "$argv[1]")
    set -l exclude_pattern (build-exclude-pattern "$_flag_exclude")
    set -l output_mode "clipboard"

    if test -n "$_flag_output"
        set output_mode "$_flag_output"
    end

    if not validate-directory "$target_dir"
        return 1
    end

    echo "generating content from "(basename "$target_dir")" directory..."

    set -l content (generate-content "$target_dir" "$exclude_pattern" | string collect)
    if test $status -ne 0
        echo "error: content generation failed."
        return 1
    end

    output-content "$content" "$output_mode"
end
