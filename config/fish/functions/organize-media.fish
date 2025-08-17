function organize-media -d "create organized directory structure for movies and tv shows"
    function validate-arguments
        set -l type $argv[1]
        set -l name $argv[2]
        set -l year $argv[3]
        set -l tvdb_id $argv[4]

        if not contains $type movie show
            echo "error: type must be 'movie' or 'show'"
            return 1
        end

        if test -z "$name"
            echo "error: name is required"
            return 1
        end

        if test -z "$year"
            echo "error: year is required"
            return 1
        end

        if test -z "$tvdb_id"
            echo "error: tvdb id is required"
            return 1
        end
    end

    function parse-tvdb-ids
        set -l tvdb_id_string $argv[1]
        set -l content_type $argv[2]
        set -l seasons $argv[3..]

        set -l ids (string split ',' "$tvdb_id_string")

        if test "$content_type" = movie
            if test (count $ids) -ne 1
                echo "error: movies should have only one tvdb id"
                return 1
            end
            echo "$ids[1]"
            return 0
        else
            set -l show_id "$ids[1]"
            set -l season_ids $ids[2..]

            if test (count $season_ids) -gt 0
                if test (count $season_ids) -ne (count $seasons)
                    echo "error: number of season ids ("(count $season_ids)") must match number of seasons ("(count $seasons)")"
                    return 1
                end
            end

            echo "$show_id"
            for season_id in $season_ids
                echo "$season_id"
            end
            return 0
        end
    end

    function parse-season-range
        set -l season_spec $argv[1]

        if test -z "$season_spec"
            return 1
        end

        if string match -qr '^[0-9]+$' "$season_spec"
            echo "$season_spec"
            return 0
        end

        if string match -qr '^[0-9]+-[0-9]+$' "$season_spec"
            set -l parts (string split '-' "$season_spec")
            set -l start $parts[1]
            set -l end $parts[2]

            if test "$start" -gt "$end"
                echo "error: invalid season range '$season_spec' - start must be <= end"
                return 1
            end

            seq -f "%02g" "$start" "$end"
            return 0
        end

        echo "error: invalid season format '$season_spec'. use single number or range (e.g., '1' or '0-3')"
        return 1
    end

    function create-main-directory
        set -l name $argv[1]
        set -l year $argv[2]
        set -l tvdb_id $argv[3]
        set -l dry_run $argv[4]

        set -l main_dir "$name ($year) [tvdbid-$tvdb_id]"

        if test "$dry_run" = true
            echo "would create: $main_dir/" >&2
        else
            if test -d "$main_dir"
                echo "directory already exists: $main_dir/" >&2
            else
                echo "creating: $main_dir/" >&2
                mkdir -p "$main_dir" || return 1
            end
        end

        echo "$main_dir"
    end

    function create-season-directories
        set -l main_dir $argv[1]
        set -l seasons $argv[2..-3]
        set -l season_ids $argv[-2]
        set -l dry_run $argv[-1]

        set -l season_id_list (string split ' ' "$season_ids")

        for i in (seq (count $seasons))
            set -l season $seasons[$i]
            set -l season_id

            if test (count $season_id_list) -ge $i
                set season_id $season_id_list[$i]
            else
                set season_id $season_id_list[1]
            end

            set -l season_dir "$main_dir/Season $season [tvdbid-$season_id]"

            if test "$dry_run" = true
                echo "would create: $season_dir/" >&2
            else
                if test -d "$season_dir"
                    echo "directory already exists: $season_dir/" >&2
                else
                    echo "creating: $season_dir/" >&2
                    mkdir -p "$season_dir" || return 1
                end
            end
        end
    end

    argparse 't/type=' 'n/name=' 'y/year=' 'i/id=' 's/seasons=' d/dry-run h/help -- $argv || return 1

    if set -q _flag_help
        echo "usage: organize-media -t TYPE -n NAME -y YEAR -i TVDB_ID [-s SEASONS] [-d]"
        echo ""
        echo "create organized directory structure for movies and tv shows"
        echo ""
        echo "options:"
        echo "  -t, --type TYPE      content type: 'movie' or 'show'"
        echo "  -n, --name NAME      name of the movie/show"
        echo "  -y, --year YEAR      release year"
        echo "  -i, --id TVDB_ID     tvdb id (for shows: comma-separated show,season1,season2...)"
        echo "  -s, --seasons RANGE  season range for shows (e.g., '1' or '0-3')"
        echo "  -d, --dry-run        show what would be created without creating"
        echo "  -h, --help           show this help message"
        echo ""
        echo "examples:"
        echo "  organize-media -t movie -n 'Shrek' -y 2001 -i 12345"
        echo "  organize-media -t show -n 'Jujutsu Kaisen' -y 2020 -i 67890 -s '1'"
        echo "  organize-media -t show -n 'Blue Box' -y 2024 -i 429934,430001,430002 -s '1-2'"
        return 0
    end

    if not validate-arguments "$_flag_type" "$_flag_name" "$_flag_year" "$_flag_id"
        return 1
    end

    set -l dry_run false
    if set -q _flag_dry_run
        set dry_run true
    end

    if test "$dry_run" = true
        echo "dry run - showing what would be created:"
    end

    if test "$_flag_type" = show -a -n "$_flag_seasons"
        set -l seasons (parse-season-range "$_flag_seasons")
        if test $status -ne 0
            return 1
        end

        set -l parsed_ids (parse-tvdb-ids "$_flag_id" "$_flag_type" $seasons)
        if test $status -ne 0
            return 1
        end

        set -l show_id $parsed_ids[1]
        set -l season_ids $parsed_ids[2..]

        set -l main_dir (create-main-directory "$_flag_name" "$_flag_year" "$show_id" "$dry_run")
        if test $status -ne 0
            return 1
        end

        if test (count $season_ids) -gt 0
            set -l season_ids_string (string join ' ' $season_ids)
            create-season-directories "$main_dir" $seasons "$season_ids_string" "$dry_run"
        else
            set -l season_ids_string "$show_id"
            create-season-directories "$main_dir" $seasons "$season_ids_string" "$dry_run"
        end
        if test $status -ne 0
            return 1
        end
    else
        set -l parsed_ids (parse-tvdb-ids "$_flag_id" "$_flag_type")
        if test $status -ne 0
            return 1
        end

        set -l main_id $parsed_ids[1]
        set -l main_dir (create-main-directory "$_flag_name" "$_flag_year" "$main_id" "$dry_run")
        if test $status -ne 0
            return 1
        end

        if test "$_flag_type" = show
            if test -z "$_flag_seasons"
                echo "error: seasons are required for tv shows"
                return 1
            end
        end
    end

    if test "$dry_run" = true
        echo ""
        echo "run without -d/--dry-run to create directories"
    else
        echo "directory structure created successfully!"
    end
end
