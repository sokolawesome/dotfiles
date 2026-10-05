complete -e -c organize_media

function organize_media_types
    printf '%s\n' movie show
end

complete -c organize_media \
    -s h -l help \
    -d "show this help message"

complete -c organize_media \
    -s t -l type \
    -x -d "movie or show, skips the questions" \
    -a "(organize_media_types)"

complete -c organize_media \
    -s n -l name \
    -x -d "title of the movie or show"

complete -c organize_media \
    -s y -l year \
    -x -d "release year"

complete -c organize_media \
    -s i -l id \
    -x -d "tvdb id, comma separated for season ids"

complete -c organize_media \
    -s s -l seasons \
    -x -d "season number or range, shows only" \
    -a "1 0-3"

complete -c organize_media \
    -l add-season \
    -x -d "add a season to an existing show" \
    -a "(__fish_complete_directories)"

complete -c organize_media \
    -l season-id \
    -x -d "tvdb id for the season added with --add-season"

complete -c organize_media \
    -s d -l dry-run \
    -d "show what would be created"

complete -c organize_media \
    -l root \
    -r -F -a "(__fish_complete_directories)" \
    -d "directory to create folders in"

complete -c organize_media -k -f