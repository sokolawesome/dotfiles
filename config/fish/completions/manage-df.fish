complete -r -c manage-df

complete -c manage-df \
    -s R -l restow -d "Restow packages (remove then stow)"
complete -c manage-df \
    -s D -l delete -d "Remove stowed packages"
complete -c manage-df \
    -s n -l dry-run -d "Show what would be done without doing it"
complete -c manage-df \
    -s h -l help -d "Show this help message"

complete -c manage-df -k -f
