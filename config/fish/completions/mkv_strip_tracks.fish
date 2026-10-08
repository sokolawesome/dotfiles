complete -e -c mkv_strip_tracks

complete -c mkv_strip_tracks \
    -s h -l help \
    -d "show this help message"

complete -c mkv_strip_tracks -k -f -a "(__fish_complete_directories)"
