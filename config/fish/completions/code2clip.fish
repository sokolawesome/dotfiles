complete -c code2clip -e

function __fish_code2clip_directories
    find . -maxdepth 2 -type d -not -path '*/.*' 2>/dev/null | \
        string replace -r '^\./' '' | \
        string match -v '.'
end

function __fish_code2clip_exclude_patterns
    printf '%s\n' \
        '\.git/' \
        'node_modules/' \
        'dist/' \
        '\.cache/' \
        '\.next/' \
        '__pycache__/' \
        '\.idea/' \
        '\.vscode/' \
        '\.DS_Store' \
        '\.log$' \
        '\.tmp$' \
        '\.lock$' \
        '\.sum$' \
        '\.svg$' \
        '\.kvconfig$' \
        'pywal\.json$' \
        '\.code\.md$' \
        '\.gitignore$' \
        '\.golangci\.yml$'
end

complete -c code2clip \
    -s h -l help \
    -d "Show this help message"

complete -c code2clip \
    -s e -l exclude \
    -x \
    -d "Regex pattern to exclude files/directories" \
    -a "(__fish_code2clip_exclude_patterns)"

complete -c code2clip \
    -s o -l output \
    -x \
    -d "Output mode" \
    -a "clipboard stdout"

complete -c code2clip \
    -f \
    -d "Directory to process" \
    -a "(__fish_code2clip_directories)"

complete -c code2clip -k -f
