function mkv-strip-tracks -d "interactively strip audio/subtitle tracks from MKV files"

    function validate-environment
        if not command -q mkvmerge
            echo "error: mkvmerge not found - install with 'sudo pacman -S mkvtoolnix-cli'"
            return 1
        end

        if not command -q jq
            echo "error: jq not found - install with 'sudo pacman -S jq'"
            return 1
        end
        if not command -q stdbuf
            echo "error: stdbuf not found - install with 'sudo pacman -S coreutils'"
            return 1
        end
    end

    function scan-tracks
        set -l file $argv[1]
        mkvmerge -J "$file" 2>/dev/null | jq -r '
            .tracks[] |
            [
                (.id | tostring),
                .type,
                (.properties.language_ietf // .properties.language // "und"),
                ((.properties.track_name // "") | gsub("[|]"; "/"))
            ] | join("|")
        '
    end

    function find-track-ids-by-spec
        set -l file $argv[1]
        set -l type $argv[2]
        set -l lang $argv[3]
        set -l name $argv[4]
        set -l target_pos $argv[5]

        set -l all_matches (mkvmerge -J "$file" 2>/dev/null | jq -r --arg type "$type" --arg lang "$lang" --arg name "$name" '
            .tracks[] |
            select(.type == $type) |
            select((.properties.language_ietf // .properties.language // "und") == $lang) |
            select($name == "" or ((.properties.track_name // "") | gsub("[|]"; "/")) == $name) |
            .id | tostring
        ')

        set -l matches (string split '\n' $all_matches)
        set -l idx (math "$target_pos + 1")
        echo $matches[$idx]
    end

    function scan-files
        if test (count $argv) -gt 0
            for f in $argv
                if test -f "$f" -a (string match -q '*.mkv' "$f"; echo $status) -eq 0
                    echo "$f"
                else
                    echo "error: $f is not a valid .mkv file" >&2
                end
            end
        else
            find . -maxdepth 1 -name "*.mkv" | sort
        end
    end

    function sum-size
        set -l total 0
        for f in $argv
            set -l s (stat -c %s "$f" 2>/dev/null)
            if test -n "$s"
                set total (math "$total + $s")
            end
        end
        echo $total
    end

    function format-size
        set -l bytes $argv[1]
        if test $bytes -ge 1073741824
            printf "%.2f GiB" (math "$bytes / 1073741824")
        else if test $bytes -ge 1048576
            printf "%.2f MiB" (math "$bytes / 1048576")
        else
            printf "%d B" $bytes
        end
    end

    if not validate-environment
        return 1
    end

    set -l files (scan-files $argv)
    if test (count $files) -eq 0
        echo "error: no .mkv files found in current directory"
        return 1
    end

    set -l probe $files[1]
    echo "scanning tracks from: "(basename "$probe")
    echo ""

    set -l tracks (scan-tracks "$probe")
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

    set -l audio_specs
    for t in $keep_audio
        set -l parts (string split '|' "$t")
        set -l type $parts[2]
        set -l lang $parts[3]
        set -l name $parts[4]
        set -l probe_id $parts[1]
        set -l pos 0
        for candidate in $tracks
            set -l cp (string split '|' "$candidate")
            if test "$cp[2]" = "$type" -a "$cp[3]" = "$lang" -a "$cp[4]" = "$name"
                if test "$cp[1]" = "$probe_id"
                    break
                end
                set pos (math $pos + 1)
            end
        end
        set -a audio_specs "$type|$lang|$name|$pos"
    end

    set -l sub_specs
    for t in $keep_subs
        set -l parts (string split '|' "$t")
        set -l type $parts[2]
        set -l lang $parts[3]
        set -l name $parts[4]
        set -l probe_id $parts[1]
        set -l pos 0
        for candidate in $tracks
            set -l cp (string split '|' "$candidate")
            if test "$cp[2]" = "$type" -a "$cp[3]" = "$lang" -a "$cp[4]" = "$name"
                if test "$cp[1]" = "$probe_id"
                    break
                end
                set pos (math $pos + 1)
            end
        end
        set -a sub_specs "$type|$lang|$name|$pos"
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

        for spec in $audio_specs
            set -l sp (string split '|' "$spec")
            set -l ids (find-track-ids-by-spec "$f" $sp[1] $sp[2] $sp[3] $sp[4])
            if test -z "$ids"
                set -a missing "audio lang=$sp[2] $sp[3]"
            end
        end

        for spec in $sub_specs
            set -l sp (string split '|' "$spec")
            set -l ids (find-track-ids-by-spec "$f" $sp[1] $sp[2] $sp[3] $sp[4])
            if test -z "$ids"
                set -a missing "subtitle lang=$sp[2] $sp[3]"
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

    set -l size_before (sum-size $files)

    echo ""
    printf "  %d files will be processed\n" (count $files)
    echo ""

    read -l -P "proceed? [y/N] " confirm
    if not string match -qi 'y' "$confirm"
        echo "cancelled"
        return 1
    end

    set -l errors 0
    set -l time_start (date +%s | string replace -r '\..+' '')

    for f in $files
        set -l base (basename "$f")
        set -l temp (string replace -r '\.mkv$' '_strip_temp.mkv' "$f")

        set -l audio_ids
        for spec in $audio_specs
            set -l sp (string split '|' "$spec")
            set -l ids (find-track-ids-by-spec "$f" $sp[1] $sp[2] $sp[3] $sp[4])
            for id in $ids
                set -a audio_ids $id
            end
        end

        set -l sub_ids
        for spec in $sub_specs
            set -l sp (string split '|' "$spec")
            set -l ids (find-track-ids-by-spec "$f" $sp[1] $sp[2] $sp[3] $sp[4])
            for id in $ids
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

        printf "  %-60s" "$base"
        set -l ok true
        stdbuf -oL $cmd 2>/dev/null | stdbuf -oL tr '\r' '\n' | while read -l line
            if string match -qr 'Progress: ([0-9]+)%' "$line"
                set -l pct (string match -r 'Progress: ([0-9]+)%' "$line")[2]
                printf "\r  %-60s %3s%%" "$base" "$pct"
            end
        end
        if test $pipestatus[1] -eq 0 -a "$ok" = true
            mv "$temp" "$f"
            printf "\r  %-60s done\n" "$base"
        else
            rm -f "$temp"
            printf "\r  %-60s error\n" "$base"
            set errors (math $errors + 1)
        end
    end

    set -l size_after (sum-size $files)
    set -l saved (math "$size_before - $size_after")

    echo ""
    if test $errors -eq 0
        echo "done - "(count $files)" files processed"
    else
        echo "done with $errors error(s)"
    end

    printf "  before: %s\n" (format-size $size_before)
    printf "  after:  %s\n" (format-size $size_after)
    printf "  saved:  %s\n" (format-size $saved)
    set -l time_end (date +%s | string replace -r '\..+' '')
    set -l elapsed (math -s 0 "$time_end - $time_start")
    printf "  time:   %dm %ds\n" (math -s 0 "$elapsed / 60") (math -s 0 "$elapsed % 60")
end
