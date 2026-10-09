complete -e -c manage_df

complete -c manage_df \
    -s h -l help \
    -d "show this help message"

complete -c manage_df \
    -s R -l restow \
    -d "remove then stow"

complete -c manage_df \
    -s D -l delete \
    -d "remove the symlinks"

complete -c manage_df \
    -s d -l dry-run \
    -d "show what would happen"

complete -c manage_df \
    -s i -l pick \
    -d "pick the packages from a list"

complete -c manage_df \
    -s v -l verbose \
    -d "show stow's own output"

complete -c manage_df \
    -l dotfiles \
    -r -F -a "(__fish_complete_directories)" \
    -d "dotfiles repo root"

complete -c manage_df -k -f