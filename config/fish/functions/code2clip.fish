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
        set -l patterns \
            # Version control
            '\.git/' '\.gitignore$' '\.gitmodules$' '\.gitattributes$' \
            '\.hg/' '\.svn/' '\.bzr/' \
            # IDE and editor configurations
            '\.DS_Store' '\.idea/' '\.vscode/' '\.zed/' '\.vs/' \
            '\.code-workspace$' '\.project$' '\.settings/' '\.classpath$' \
            '\.sublime-project$' '\.sublime-workspace$' '\.history/' \
            # Temporary and backup files
            '\.bak$' '\.swp$' '\.swo$' '\.tmp$' '\.temp$' '~$' '\.#.*' \
            '\.lock$' '\.cache$' '\.tempdir/' '\.temporary/' \
            # Logs and caches
            '\.log$' '\.log\.[0-9]+$' '\.cache/' '\.pytest_cache/' '\.ruff_cache/' \
            '\.tox/' '\.venv/' 'venv/' '\.env/' '\.__pycache__/' \
            # Binary and archive files
            '\.zip$' '\.tar\.gz$' '\.rar$' '\.7z$' '\.tar$' '\.bz2$' '\.gz$' \
            '\.exe$' '\.dll$' '\.so$' '\.dylib$' '\.o$' '\.obj$' '\.a$' \
            '\.class$' '\.jar$' '\.war$' '\.ear$' \
            '\.deb$' '\.rpm$' '\.dmg$' '\.iso$' '\.img$' \
            # Media files
            '\.png$' '\.jpg$' '\.jpeg$' '\.gif$' '\.bmp$' '\.ico$' '\.webp$' \
            '\.svg$' '\.mp4$' '\.mp3$' '\.wav$' '\.avi$' '\.mkv$' '\.mov$' \
            '\.wmv$' '\.flv$' '\.webm$' '\.ogg$' \
            # Documentation and misc
            '\.pdf$' '\.doc$' '\.docx$' '\.xls$' '\.xlsx$' '\.ppt$' '\.pptx$' \
            'LICENSE' \
            # Web development
            'node_modules/' 'dist/' 'build/' 'out/' 'public/' \
            '\.next/' '\.nuxt/' '\.parcel-cache/' 'coverage/' '\.nyc_output/' \
            '\.angular/' '\.svelte-kit/' '\.vite/' '\.astro/' '\.gatsby-cache/' \
            '\.sass-cache/' 'coverage/' 'lerna-debug\.log$' '\.eslintcache$' \
            'package-lock\.json' 'environments/' \
            # Go
            'go\.mod$' 'go\.sum$' '\.test$' '\.out$' 'vendor/' 'pkg/' 'bin/' \
            # Rust
            'target/' 'Cargo\.lock$' '\.cargo/' '\.rustc/' \
            # C# and ASP.NET
            'obj/' 'bin/' 'publish/' '\.csproj\.user$' '\.suo$' '\.user$' \
            '\.sln\.docstates$' 'TestResults/' 'packages/' '\.nuget/' '\.pdb$' \
            # Miscellaneous build and test artifacts
            '\.min\.js$' '\.map$' '\.coverage$' '\.lcov$' '\.profraw$' \
            'test-reports/' 'build-artifacts/' 'tmp/' 'temp/' \
            # Database and configuration
            '\.db$' '\.sqlite3$' '\.sql$' '\.bak\.sql$' '\.env\.local$' \
            '\.env\.development$' '\.env\.production$' '\.env'

        string join '|' $patterns
    end

    function build-exclude-pattern
        set -l additional $argv[1]
        set -l basic_pattern (get-basic-exclude-pattern)

        if test -z "$additional"
            echo "$basic_pattern"
        else
            echo "$basic_pattern|$additional"
        end
    end

    function find-git-repos
        set -l dir $argv[1]
        find "$dir" -type d -name '.git' | while read git_dir
            dirname "$git_dir"
        end
    end

    function get-repo-for-file
        set -l file $argv[1]
        set -l repos $argv[2..]

        set -l longest_match ""
        for repo in $repos
            if string match -q "$repo/*" "$file"
                if test (string length "$repo") -gt (string length "$longest_match")
                    set longest_match "$repo"
                end
            end
        end

        echo "$longest_match"
    end

    function is-file-ignored
        set -l file $argv[1]
        set -l repo $argv[2]

        if test -z "$repo"
            return 1
        end

        git -C "$repo" check-ignore "$file" >/dev/null 2>&1
    end

    function generate-tree-structure
        set -l dir $argv[1]
        set -l exclude $argv[2]

        echo "## directory structure"
        tree -a -I "$exclude" --noreport -L 6 "$dir" || return 1
    end

    function print-file-content
        set -l file $argv[1]
        set -l ext (string match -r '.*\.([^.]+)$' (basename "$file") | string replace -r '^.*\.' '' | string lower)

        echo ""
        echo "### '$file'"
        echo "```$ext"
        cat "$file"
        echo ""
        echo "```"
    end

    function generate-file-contents
        set -l dir $argv[1]
        set -l exclude $argv[2]

        echo ""
        echo "## file contents"

        set -l git_repos (find-git-repos "$dir")

        find "$dir" -type f -print0 | grep -vzE "$exclude" | while read -z file
            if test -f "$file" -a -r "$file"
                grep -Iq . "$file" || continue

                set -l repo (get-repo-for-file "$file" $git_repos)
                if test -n "$repo"
                    if is-file-ignored "$file" "$repo"
                        continue
                    end
                end

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
        echo "  -e, --exclude <REGEX>        additional exclude pattern"
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
