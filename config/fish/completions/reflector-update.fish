complete -r -c reflector-update

function reflector-countries
    if command -q reflector
        reflector --list-countries 2>/dev/null | \
            string match -r '^([A-Za-z\s\(\)\/]+?)\s{2,}' | \
            string replace -r '\s{2,}.*$' '' | \
            string trim
    end
end

function reflector-protocols
    printf '%s\n' http https ftp
end

function reflector-numbers
    printf '%s\n' 5 10 15 20 25 30
end

complete -c reflector-update \
    -s h -l help \
    -d "show this help message"

complete -c reflector-update \
    -s c -l country \
    -x -d "country name/code" \
    -a "(reflector-countries)"

complete -c reflector-update \
    -s p -l protocol \
    -x -d "protocol to use" \
    -a "(reflector-protocols)"

complete -c reflector-update \
    -s n -l number \
    -x -d "number of mirrors" \
    -a "(reflector-numbers)"

complete -c reflector-update -k -f
