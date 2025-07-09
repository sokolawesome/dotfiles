complete -r -c code2clip

complete -c code2clip \
    -s h -l help \
    -d "show this help message"

complete -c code2clip \
    -s e -l exclude \
    -x -d "additional exclude pattern (regex)"

complete -c code2clip \
    -s o -l output \
    -x -d "output mode" \
    -a "clipboard stdout"

complete -c code2clip \
    -s t -l no-tree \
    -d "disable tree"

complete -c code2clip \
    -d "target directory" \
    -a "(__fish_complete_directories)"

complete -c code2clip -k -f
