complete -e -c backup_system_state

complete -c backup_system_state \
    -s h -l help \
    -d "show this help message"

complete -c backup_system_state \
    -l dotfiles \
    -r -F -a "(__fish_complete_directories)" \
    -d "dotfiles repo root"

complete -c backup_system_state -k -f