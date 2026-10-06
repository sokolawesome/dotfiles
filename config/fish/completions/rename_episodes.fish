complete -e -c rename_episodes

complete -c rename_episodes \
    -s h -l help \
    -d "show this help message"

complete -c rename_episodes \
    -s s -l season \
    -x -d "season number, detected from the directory name if absent" \
    -a "(seq 0 20)"

complete -c rename_episodes \
    -s o -l offset \
    -x -d "add this to every episode number" \
    -a "-100 -12 0 12 24"

complete -c rename_episodes \
    -l absolute \
    -d "treat episode numbers as absolute, subtract --offset from them"

complete -c rename_episodes \
    -s d -l directory \
    -r -F -a "(__fish_complete_directories)" \
    -d "directory to scan"

complete -c rename_episodes -k -f