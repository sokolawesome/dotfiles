complete -e -c mkv_extract_tracks

complete -c mkv_extract_tracks \
    -s h -l help \
    -d "show this help message"

complete -c mkv_extract_tracks -k -f -a "(__fish_complete_directories)"
