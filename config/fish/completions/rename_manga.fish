complete -e -c rename_manga

complete -c rename_manga \
    -s h -l help \
    -d "show this help message"

complete -c rename_manga \
    -s d -l directory \
    -r -F -a "(__fish_complete_directories)" \
    -d "directory to scan"

complete -c rename_manga -k -f