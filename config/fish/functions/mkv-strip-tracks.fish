function mkv-strip-tracks -d "interactively strip audio/subtitle tracks from MKV files"

    function _mst_scan_tracks
        set -l file $argv[1]
        mkvmerge -J "$file" 2>/dev/null | jq -r '
            .tracks[] |
            [
                (.id | tostring),
                .type,
                (.properties.language_ietf // .properties.language // "und"),
                (.properties.track_name // "")
            ] | join("|")
        '
    end

    function _mst_find_track_id
        set -l file $argv[1]
        set -l type $argv[2]
        set -l lang $argv[3]
        set -l name $argv[4]

        set -l match (mkvmerge -J "$file" 2>/dev/null | jq -r --arg type "$type" --arg lang "$lang" --arg name "$name" '
            .tracks[] |
            select(.type == $type) |
            select((.properties.language_ietf // .properties.language // "und") == $lang) |
            select($name == "" or (.properties.track_name // "") == $name) |
            .id | tostring
        ' | head -1)

        if test -z "$match"
            set match (mkvmerge -J "$file" 2>/dev/null | jq -r --arg type "$type" --arg lang "$lang" '
                .tracks[] |
                select(.type == $type) |
                select((.properties.language_ietf // .properties.language // "und") == $lang) |
                .id | tostring
            ' | head -1)
        end

        echo "$match"
    end

    function _mst_scan_files
        find . -maxdepth 1 -name "*.mkv" | sort
    end

    if not command -q mkvmerge
        echo "error: mkvmerge not found — install mkvtoolnix"
        return 1
    end

    if not command -q jq
        echo "error: jq not found"
        return 1
    end

    set -l files (_mst_scan_files)
    if test (count $files) -eq 0
        echo "error: no .mkv files found in current directory"
        return 1
    end

    set -l probe $files[1]
    echo "scanning tracks from: "(basename "$probe")
    echo ""

    set -l tracks (_mst_scan_tracks "$probe")
    if test (count $tracks) -eq 0
        echo "error: could not read tracks from $probe"
        return 1
    end

    set -l audio_tracks
    set -l sub_tracks
    set -l idx 1

    echo "audio tracks:"
    for t in $tracks
        set -l parts (string split '|' "$t")
        if test "$parts[2]" = audio
            printf "  [%d] id=%-2s  lang=%-6s  %s\n" $idx $parts[1] $parts[3] $parts[4]
            set -a audio_tracks "$t"
            set idx (math $idx + 1)
        end
    end

    echo ""
    echo "subtitle tracks:"
    set -l sub_idx $idx
    for t in $tracks
        set -l parts (string split '|' "$t")
        if test "$parts[2]" = subtitles
            printf "  [%d] id=%-2s  lang=%-6s  %s\n" $idx $parts[1] $parts[3] $parts[4]
            set -a sub_tracks "$t"
            set idx (math $idx + 1)
        end
    end

    echo ""
    read -l -P "audio tracks to keep (space-separated numbers, or 'all'): " audio_input
    read -l -P "subtitle tracks to keep (space-separated numbers, or 'all', or 'none'): " sub_input

    set -l keep_audio
    if test "$audio_input" = all
        set keep_audio $audio_tracks
    else
        for n in (string split ' ' "$audio_input")
            set -l i (math "$n - 1")
            if test $i -ge 0 -a $i -lt (count $audio_tracks)
                set -a keep_audio $audio_tracks[(math $i + 1)]
            end
        end
    end

    set -l keep_subs
    if test "$sub_input" = all
        set keep_subs $sub_tracks
    else if test "$sub_input" != none -a -n "$sub_input"
        for n in (string split ' ' "$sub_input")
            set -l i (math "$n - $sub_idx")
            if test $i -ge 0 -a $i -lt (count $sub_tracks)
                set -a keep_subs $sub_tracks[(math $i + 1)]
            end
        end
    end

    if test (count $keep_audio) -eq 0
        echo "error: at least one audio track must be kept"
        return 1
    end

    echo ""
    echo "will keep:"
    echo "  video: all"
    for t in $keep_audio
        set -l parts (string split '|' "$t")
        printf "  audio:    lang=%-6s  %s\n" $parts[3] $parts[4]
    end
    for t in $keep_subs
        set -l parts (string split '|' "$t")
        printf "  subtitle: lang=%-6s  %s\n" $parts[3] $parts[4]
    end

    echo ""
    echo "checking all files..."

    set -l files_ok
    set -l files_missing
    set -l missing_report

    for f in $files
        set -l base (basename "$f")
        set -l missing

        for t in $keep_audio
            set -l parts (string split '|' "$t")
            set -l id (_mst_find_track_id "$f" audio $parts[3] $parts[4])
            if test -z "$id"
                set -a missing "audio lang=$parts[3] $parts[4]"
            end
        end

        for t in $keep_subs
            set -l parts (string split '|' "$t")
            set -l id (_mst_find_track_id "$f" subtitles $parts[3] $parts[4])
            if test -z "$id"
                set -a missing "subtitle lang=$parts[3] $parts[4]"
            end
        end

        if test (count $missing) -gt 0
            set -a files_missing "$f"
            set -a missing_report "$base: missing "(string join ', ' $missing)
        else
            set -a files_ok "$f"
        end
    end

    if test (count $files_missing) -gt 0
        echo ""
        echo "warning: some files are missing selected tracks:"
        for r in $missing_report
            echo "  $r"
        end

        echo ""
        echo "  [1] skip those files, process the rest"
        echo "  [2] process anyway (missing tracks simply won't be included)"
        echo "  [3] abort"
        echo ""
        read -l -P "choose [1/2/3]: " choice

        switch "$choice"
            case 1
                set files $files_ok
                if test (count $files) -eq 0
                    echo "nothing to process"
                    return 1
                end
                echo "skipping "(count $files_missing)" file(s), processing "(count $files)
            case 2
                echo "processing all "(count $files)" files"
            case '*'
                echo "aborted"
                return 1
        end
    end

    echo ""
    printf "  %d files will be processed\n" (count $files)
    echo ""

    read -l -P "proceed? [y/N] " confirm
    if not string match -qi 'y' "$confirm"
        echo "cancelled"
        return 1
    end

    set -l errors 0

    for f in $files
        set -l base (basename "$f")
        set -l temp (string replace -r '\.mkv$' '_strip_temp.mkv' "$f")

        set -l audio_ids
        for t in $keep_audio
            set -l parts (string split '|' "$t")
            set -l id (_mst_find_track_id "$f" audio $parts[3] $parts[4])
            if test -n "$id"
                set -a audio_ids $id
            end
        end

        set -l sub_ids
        for t in $keep_subs
            set -l parts (string split '|' "$t")
            set -l id (_mst_find_track_id "$f" subtitles $parts[3] $parts[4])
            if test -n "$id"
                set -a sub_ids $id
            end
        end

        set -l cmd mkvmerge -o "$temp"

        if test (count $audio_ids) -gt 0
            set -a cmd --audio-tracks (string join ',' $audio_ids)
        else
            set -a cmd --no-audio
        end

        if test (count $sub_ids) -gt 0
            set -a cmd --subtitle-tracks (string join ',' $sub_ids)
        else
            set -a cmd --no-subtitles
        end

        set -a cmd "$f"

        printf "  processing: %s ... " "$base"
        if $cmd > /dev/null 2>&1
            mv "$temp" "$f"
            echo "done"
        else
            rm -f "$temp"
            echo "error"
            set errors (math $errors + 1)
        end
    end

    echo ""
    if test $errors -eq 0
        echo "done — "(count $files)" files processed"
    else
        echo "done with $errors error(s)"
    end
end
