function reflector-update -d "Update Pacman mirror list using reflector"
    # Check if reflector is installed
    if not command -q reflector
        echo "Error: reflector is not installed. Install it with 'sudo pacman -S reflector'."
        return 1
    end

    # Default options
    set -l default_countries "EE"
    set -l protocol "https"
    set -l num_mirrors 20
    set -l mirrorlist "/etc/pacman.d/mirrorlist"
    set -l backup_file "/etc/pacman.d/mirrorlist.bak"

    # Parse arguments
    argparse 'c/country=' 'p/protocol=' 'n/number=' -- $argv
    or return 1

    # Override defaults if arguments are provided
    set -l countries
    if set -q _flag_country
        # Split comma-separated countries into a list
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

    # Validate countries
    if test -z "$countries"
        echo "Error: No countries specified."
        return 1
    end

    # Backup existing mirrorlist
    if test -f $mirrorlist
        echo "Backing up $mirrorlist to $backup_file..."
        sudo cp $mirrorlist $backup_file
        or begin
            echo "Error: Failed to backup mirrorlist."
            return 1
        end
    end

    # Build reflector country arguments
    set -l country_args
    for country in $countries
        set -a country_args --country (string trim $country)
    end

    # Run reflector to update mirrorlist
    echo "Updating mirrorlist with $num_mirrors $protocol mirrors from "(string join ", " $countries)"..."
    sudo reflector $country_args --protocol $protocol --latest $num_mirrors --sort rate --save $mirrorlist
    or begin
        echo "Error: Failed to update mirrorlist."
        return 1
    end

    # Verify the mirrorlist was updated
    if test -s $mirrorlist
        echo "Mirrorlist updated successfully!"
    else
        echo "Error: Mirrorlist is empty or not updated."
        return 1
    end

    # Optionally sync pacman
    echo "Syncing pacman databases..."
    sudo pacman -Syy
    or begin
        echo "Error: Failed to sync pacman databases."
        return 1
    end

    echo "Reflector update complete!"
end
