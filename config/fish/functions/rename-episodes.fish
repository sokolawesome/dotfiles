function rename-episodes -d "bulk rename tv show episodes with proper season/episode format"
    function detect-season-from-directory
        set -l current_dir (basename "$PWD")

        if string match -qr 'Season ([0-9]+)' "$current_dir"
            set -l season_match (string match -r 'Season ([0-9]+)' "$current_dir")
            printf "%02d" $season_match[2]
            return 0
        end

        return 1
    end

    function get-video-files
        find . -maxdepth 1 -type f \( -name "*.mkv" -o -name "*.mka" -o -name "*.mp4" -o -name "*.avi" \) | sort
    end

    function get-subtitle-files
        find . -maxdepth 1 -type f \( -name "*.ass" -o -name "*.srt" -o -name "*.vtt" \) | sort
    end

    function extract-episode-number
        set -l filename $argv[1]

        set -l patterns \
            'S[0-9]+E([0-9]+)' \
            '\[([0-9]+)\]' \
            ' ([0-9]+) ' \
            '-([0-9]+)-' \
            '_([0-9]+)_' \
            '\.([0-9]+)\.' \
            ' ([0-9]+)\.' \
            '^([0-9]+)' \
            '([0-9]+)$'

        for pattern in $patterns
            if string match -qr "$pattern" "$filename"
                set -l match (string match -r "$pattern" "$filename")
                if test -n "$match[2]"
                    echo "$match[2]"
                    return 0
                end
            end
        end

        return 1
    end

    function group-files-by-episode
        set -l files $argv[1..]
        set -l grouped_files

        for file in $files
            set -l basename_file (basename "$file")
            set -l episode_num (extract-episode-number "$basename_file")

            if test -n "$episode_num"
                # Convert to decimal to avoid octal issues, then pad
                set -l decimal_episode (printf "%d" "$episode_num" 2>/dev/null || echo "$episode_num")
                set -l padded_episode (printf "%02d" "$decimal_episode")
                set -a grouped_files "$decimal_episode:$file"
            else
                echo "warning: could not extract episode number from '$basename_file'"
            end
        end

        printf '%s\n' $grouped_files | sort -n -t: -k1,1
    end

    function calculate-new-episode-number
        set -l current_episode $argv[1]
        set -l episode_offset $argv[2]

        # Convert to decimal to avoid octal interpretation issues
        set -l current_decimal (printf "%d" "$current_episode" 2>/dev/null || echo "$current_episode")
        set -l offset_decimal (printf "%d" "$episode_offset" 2>/dev/null || echo "$episode_offset")

        math "$current_decimal + $offset_decimal"
    end

    function generate-new-filename
        set -l old_file $argv[1]
        set -l season $argv[2]
        set -l new_episode $argv[3]

        set -l extension (string match -r '\\.[^.]+\\.[^.]+\\.[^.]+|\\.[^.]+\\.[^.]+|\\.[^.]+$' (string sub -s 3 "$old_file"))
        set -l new_episode_padded (printf "%02d" "$new_episode")

        echo "S"$season"E$new_episode_padded$extension"
    end

    function preview-renames
        set -l season $argv[1]
        set -l episode_offset $argv[2]
        set -l grouped_files $argv[3..]

        echo "preview of changes:"
        echo -------------------

        for entry in $grouped_files
            set -l parts (string split ':' "$entry")
            set -l episode_num $parts[1]
            set -l file_path $parts[2]
            set -l old_filename (basename "$file_path")

            set -l new_episode (calculate-new-episode-number "$episode_num" "$episode_offset")
            set -l new_filename (generate-new-filename "$file_path" "$season" "$new_episode")

            echo "$old_filename -> $new_filename"
        end

        echo -------------------
        echo "total files: "(count $grouped_files)
    end

    function execute-renames
        set -l season $argv[1]
        set -l episode_offset $argv[2]
        set -l grouped_files $argv[3..]

        for entry in $grouped_files
            set -l parts (string split ':' "$entry")
            set -l episode_num $parts[1]
            set -l file_path $parts[2]
            set -l old_filename (basename "$file_path")

            set -l new_episode (calculate-new-episode-number "$episode_num" "$episode_offset")
            set -l new_filename (generate-new-filename "$file_path" "$season" "$new_episode")

            echo "renaming: $old_filename -> $new_filename"
            mv "$file_path" "$new_filename" || begin
                echo "error: failed to rename $old_filename"
                return 1
            end
        end
    end

    function prompt-confirmation
        echo ""
        echo "proceed with renaming? [y/N]: "
        read -l response

        if test "$response" = y -o "$response" = Y
            return 0
        else
            echo "operation cancelled"
            return 1
        end
    end

    argparse 's/season=' 'o/offset=' n/dry-run h/help -- $argv || return 1

    if set -q _flag_help
        echo "usage: rename-episodes [-s SEASON] [-o OFFSET] [-n]"
        echo ""
        echo "bulk rename tv show episodes with proper season/episode format"
        echo ""
        echo "options:"
        echo "  -s, --season SEASON  season number (auto-detect from directory if not provided)"
        echo "  -o, --offset OFFSET  episode number offset (default: 0)"
        echo "  -n, --dry-run        preview changes without executing"
        echo "  -h, --help           show this help message"
        echo ""
        echo "examples:"
        echo "  rename-episodes                    # auto-detect season, no offset"
        echo "  rename-episodes -s 2               # force season 2"
        echo "  rename-episodes -s 2 -o 12         # season 2, episodes start from 13"
        echo "  rename-episodes -n                 # preview only"
        return 0
    end

    set -l season
    if set -q _flag_season
        set season (printf "%02d" "$_flag_season")
    else
        set season (detect-season-from-directory)
        if test $status -ne 0
            echo "error: could not detect season from directory name"
            echo "use -s/--season to specify season number"
            return 1
        end
        echo "detected season: $season"
    end

    set -l episode_offset 0
    if set -q _flag_offset
        set episode_offset "$_flag_offset"
    end

    set -l video_files (get-video-files)
    set -l subtitle_files (get-subtitle-files)
    set -l all_files $video_files $subtitle_files

    if test (count $all_files) -eq 0
        echo "error: no video or subtitle files found in current directory"
        return 1
    end

    set -l grouped_files (group-files-by-episode $all_files)
    if test (count $grouped_files) -eq 0
        echo "error: could not extract episode numbers from any files"
        return 1
    end

    set -l dry_run false
    if set -q _flag_dry_run
        set dry_run true
    end

    preview-renames "$season" "$episode_offset" $grouped_files

    if test "$dry_run" = true
        echo ""
        echo "dry run complete - no files were renamed"
        return 0
    end

    if not prompt-confirmation
        return 1
    end

    execute-renames "$season" "$episode_offset" $grouped_files
    if test $status -eq 0
        echo ""
        echo "episode renaming completed successfully!"
    end
end
