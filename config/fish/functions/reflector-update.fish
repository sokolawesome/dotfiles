function reflector-update -d "update pacman mirror list using reflector"
    function validate-args
        set -l protocol $argv[1]
        set -l num_mirrors $argv[2]

        if not contains $protocol http https ftp
            echo "error: invalid protocol '$protocol'. use http, https, or ftp."
            return 1
        end

        if not string match -qr '^\d+$' $num_mirrors; or test $num_mirrors -le 0
            echo "error: number of mirrors must be a positive integer."
            return 1
        end
    end

    function check-dependencies
        if not command -q reflector
            echo "error: reflector is not installed. install it with 'sudo pacman -S reflector'."
            return 1
        end

        if not command -q sudo
            echo "error: ensure sudo is installed and configured."
            return 1
        end
    end

    function backup-mirrorlist
        set -l mirrorlist $argv[1]
        set -l backup_file $argv[2]

        if test -f $mirrorlist
            echo "backing up $mirrorlist to $backup_file..."
            sudo cp $mirrorlist $backup_file || return 1
        end
    end

    function restore-mirrorlist
        set -l mirrorlist $argv[1]
        set -l backup_file $argv[2]

        if test -f $backup_file
            echo "restoring backup mirrorlist..."
            sudo cp $backup_file $mirrorlist || return 1
        end
    end

    function update-mirrors
        set -l countries $argv[1..-4]
        set -l protocol $argv[-3]
        set -l num_mirrors $argv[-2]
        set -l mirrorlist $argv[-1]

        set -l country_args
        for country in $countries
            set -a country_args --country (string trim $country)
        end

        echo "updating mirrorlist with $num_mirrors $protocol mirrors from "(string join ", " $countries)"..."
        sudo reflector $country_args --protocol $protocol --latest $num_mirrors --sort rate --save $mirrorlist || return 1

        if not test -s $mirrorlist
            echo "error: mirrorlist is empty or not updated."
            return 1
        end
    end

    if not check-dependencies
        return 1
    end

    set -l default_countries "EE"
    set -l protocol "https"
    set -l num_mirrors 20
    set -l mirrorlist "/etc/pacman.d/mirrorlist"
    set -l backup_file "/etc/pacman.d/mirrorlist.bak"

    argparse 'c/country=+' 'p/protocol=' 'n/number=' 'h/help' -- $argv || return 1

    if set -q _flag_help
        echo "usage: reflector-update [-c|--country COUNTRY...] [-p|--protocol PROTOCOL] [-n|--number NUM]"
        echo "  -c, --country    country names or codes (can be repeated, default: EE)"
        echo "  -p, --protocol   protocol to use: http, https, ftp (default: https)"
        echo "  -n, --number     number of mirrors (default: 20)"
        echo "  -h, --help       show this help message"
        return 0
    end

    set -l countries $default_countries
    if set -q _flag_country
        set countries $_flag_country
    end

    if set -q _flag_protocol
        set protocol $_flag_protocol
    end

    if set -q _flag_number
        set num_mirrors $_flag_number
    end

    if not validate-args $protocol $num_mirrors
        return 1
    end

    if not backup-mirrorlist $mirrorlist $backup_file
        return 1
    end

    if not update-mirrors $countries $protocol $num_mirrors $mirrorlist
        restore-mirrorlist $mirrorlist $backup_file
        return 1
    end

    echo "mirrorlist updated successfully!"

    echo "syncing pacman databases..."
    sudo pacman -Syy || begin
        echo "error: failed to sync pacman databases."
        return 1
    end

    echo "reflector update complete!"
end
