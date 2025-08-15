complete -r -c organize-media

function organize-media-types
    printf '%s\n' movie show
end

complete -c organize-media \
    -s h -l help \
    -d "show this help message"

complete -c organize-media \
    -s t -l type \
    -x -d "content type" \
    -a "(organize-media-types)"

complete -c organize-media \
    -s n -l name \
    -x -d "name of the movie/show"

complete -c organize-media \
    -s y -l year \
    -x -d "release year"

complete -c organize-media \
    -s i -l id \
    -x -d "tvdb id"

complete -c organize-media \
    -s s -l seasons \
    -x -d "season range (e.g., '1' or '0-3')"

complete -c organize-media \
    -s d -l dry-run \
    -d "show what would be created without creating"

complete -c organize-media -k -f
