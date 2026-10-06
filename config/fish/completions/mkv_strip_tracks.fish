complete -e -c mkv_strip_tracks

complete -c mkv_strip_tracks \
    -s h -l help \
    -d "show this help message"

complete -c mkv_strip_tracks \
    -l keep-audio \
    -x -d "comma separated audio languages" \
    -a "eng jpn kor chi spa ger fre ita rus por ara pol tur und"

complete -c mkv_strip_tracks \
    -l keep-subs \
    -x -d "comma separated subtitle languages" \
    -a "eng jpn kor chi spa ger fre ita rus por ara pol tur und"

complete -c mkv_strip_tracks \
    -l skip-missing \
    -d "leave files that lack a requested track alone"

complete -c mkv_strip_tracks \
    -l directory \
    -x -d "directory to scan"

complete -c mkv_strip_tracks \
    -d "mkv files to process" \
    -a "*.mkv"

complete -c mkv_strip_tracks -k -f