complete -r -c reflector-update

function __fish_reflector_countries_for_completion
    if not command -q reflector
        return 1
    end

    reflector --list-countries 2>/dev/null | \
        string match -r '^([A-Za-z\s\(\)\/]+?)\s{2,}' | \
        string replace -r '\s{2,}.*$' '' | \
        string trim
end

function __fish_reflector_protocols
    printf '%s\n' http https ftp
end

function __fish_reflector_numbers
    printf '%s\n' 5 10 15 20 25 30
end

complete -c reflector-update \
    -s h -l help -d "Show this help message"

complete -c reflector-update \
    -s c -l country \
    -x \
    -d "Country name or code" \
    -a "(__fish_reflector_countries_for_completion)"

complete -c reflector-update \
    -s p -l protocol \
    -x \
    -d "Protocol to use" \
    -a "(__fish_reflector_protocols)"

complete -c reflector-update \
    -s n -l number \
    -x \
    -a "(__fish_reflector_numbers)" \
    -d "Number of mirrors"

complete -c reflector-update -k -f
