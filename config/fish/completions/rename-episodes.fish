complete -e -c rename-episodes

complete -c rename-episodes \
    -s h -l help \
    -d "show this help message"

complete -c rename-episodes \
    -s s -l season \
    -x -d "season number" \
    -a "(seq 0 10)"

complete -c rename-episodes \
    -s o -l offset \
    -x -d "episode number offset" \
    -a "0 12 24 36 48"

complete -c rename-episodes -k -f
