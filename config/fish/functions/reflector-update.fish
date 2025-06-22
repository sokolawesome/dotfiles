function reflector-update -d "Update Pacman mirror list using reflector"
    function validate_protocol
        set -l protocol $argv[1]

        if not contains $protocol http https ftp
            echo "Error: Invalid protocol '$protocol'. Use http, https, or ftp."
            return 1
        end
    end

    function validate_number
        set -l num_mirrors $argv[1]

        if not string match -qr '^\d+$' $num_mirrors; or test $num_mirrors -le 0
            echo "Error: Number of mirrors must be a positive integer."
            return 1
        end
    end

    function validate_countries
        set -l countries $argv

        if test (count $countries) -eq 0
            echo "Error: No countries specified."
            return 1
        end

        for country in $countries
            if not string match -qr '^[A-Z]{2}$' (string upper $country)
                echo "Warning: '$country' may not be a valid ISO country code."
            end
        end
    end

    function check_reflector_deps
        if not command -q reflector
            echo "Error: reflector is not installed. Install it with 'sudo pacman -S reflector'."
            return 1
        end

        if not command -q sudo
            echo "Error: sudo is required but not available."
            return 1
        end
    end

    function backup_mirrorlist
        set -l mirrorlist $argv[1]
        set -l backup_file $argv[2]

        if test -f $mirrorlist
            echo "Backing up $mirrorlist to $backup_file..."
            sudo cp $mirrorlist $backup_file
            or begin
                echo "Error: Failed to backup mirrorlist."
                return 1
            end
        end
    end

    function restore_mirrorlist
        set -l mirrorlist $argv[1]
        set -l backup_file $argv[2]

        if test -f $backup_file
            echo "Restoring backup mirrorlist..."
            sudo cp $backup_file $mirrorlist
            or begin
                echo "Error: Failed to restore mirrorlist backup."
                return 1
            end
        end
    end

    set -l default_countries "EE"
    set -l protocol "https"
    set -l num_mirrors 20
    set -l mirrorlist "/etc/pacman.d/mirrorlist"
    set -l backup_file "/etc/pacman.d/mirrorlist.bak"

    argparse 'c/country=' 'p/protocol=' 'n/number=' 'h/help' -- $argv
    or return 1

    if set -q _flag_help
        echo "Usage: reflector-update [-c|--country COUNTRIES] [-p|--protocol PROTOCOL] [-n|--number NUM]"
        echo "  -c, --country    Comma-separated country codes (default: EE)"
        echo "  -p, --protocol   Protocol to use: http, https, ftp (default: https)"
        echo "  -n, --number     Number of mirrors (default: 20)"
        echo "  -h, --help       Show this help message"
        return 0
    end

    if not check_reflector_deps
        return 1
    end

    set -l countries
    if set -q _flag_country
        set countries (string split "," $_flag_country | string trim)
    else
        set countries $default_countries
    end

    if set -q _flag_protocol
        set protocol $_flag_protocol
    end

    if set -q _flag_number
        set num_mirrors $_flag_number
    end

    if not validate_countries $countries
        return 1
    end

    if not validate_protocol $protocol
        return 1
    end

    if not validate_number $num_mirrors
        return 1
    end

    if not backup_mirrorlist $mirrorlist $backup_file
        return 1
    end

    set -l country_args
    for country in $countries
        set -a country_args --country (string trim $country)
    end

    echo "Updating mirrorlist with $num_mirrors $protocol mirrors from "(string join ", " $countries)"..."
    sudo reflector $country_args --protocol $protocol --latest $num_mirrors --sort rate --save $mirrorlist
    or begin
        echo "Error: Failed to update mirrorlist."
        restore_mirrorlist $mirrorlist $backup_file
        return 1
    end

    if not test -s $mirrorlist
        echo "Error: Mirrorlist is empty or not updated."
        restore_mirrorlist $mirrorlist $backup_file
        return 1
    end

    echo "Mirrorlist updated successfully!"

    echo "Syncing pacman databases..."
    sudo pacman -Syy
    or begin
        echo "Error: Failed to sync pacman databases."
        return 1
    end

    echo "Reflector update complete!"
end
