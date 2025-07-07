complete -r -c manage-df

complete -c manage-df \
    -s h -l help \
    -d "show this help message"

complete -c manage-df \
    -s R -l restow \
    -d "restow packages"

complete -c manage-df \
    -s D -l delete \
    -d "remove stowed packages"

complete -c manage-df \
    -s n -l dry-run \
    -d "dry run"

complete -c manage-df -k -f
