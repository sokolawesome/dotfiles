complete -r -c rename-episodes

function rename-episodes-seasons
    printf '%s\n' 0 1 2 3 4 5 6 7 8 9 10
end

function rename-episodes-offsets
    printf '%s\n' 0 12 24 36 48
end

complete -c rename-episodes \
    -s h -l help \
    -d "show this help message"

complete -c rename-episodes \
    -s s -l season \
    -x -d "season number" \
    -a "(rename-episodes-seasons)"

complete -c rename-episodes \
    -s o -l offset \
    -x -d "episode number offset" \
    -a "(rename-episodes-offsets)"

complete -c rename-episodes \
    -s n -l dry-run \
    -d "preview changes without executing"

complete -c rename-episodes -k -f
