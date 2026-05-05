function rename-episodes -d "bulk rename tv show episodes with proper S01E01 format"

    function _re_detect_season
        set -l dir (basename "$PWD")
        if string match -qr '(?i)season[\s._-]*([0-9]+)' "$dir"
            printf "%02d" (string replace -r '^0*' '' (string match -r '(?i)season[\s._-]*([0-9]+)' "$dir")[2])
            return 0
        end
        return 1
    end

    function _re_pad
        set -l n (string replace -r '^0*' '' "$argv[1]")
        test -z "$n" && set n 0
        printf "%02d" $n
    end

    function _re_normalize_dots
        set -l name $argv[1]
        if not string match -q '* *' "$name"
            echo (string replace -ar '\.' ' ' "$name")
        else
            echo "$name"
        end
    end

    function _re_normalize_underscores
        set -l name $argv[1]
        echo (string replace -ar '_' ' ' "$name")
    end

    function _re_strip_tags
        set -l name $argv[1]
        set name (string replace -ar '(?i)\[[^\]]*(?:bdrip|webrip|web.dl|bluray|x26[45]|hevc|avc|flac|aac|ac3|eac3|dts|opus|10bit|8bit|[0-9]{3,4}p|[0-9]{4}x[0-9]{3,4})[^\]]*\]' '' "$name")
        set name (string replace -ar '(?i)\([^)]*(?:bdrip|webrip|web.dl|bluray|x26[45]|hevc|avc|flac|aac|ac3|eac3|dts|opus|10bit|8bit|[0-9]{3,4}p|[0-9]{4}x[0-9]{3,4})[^)]*\)' '' "$name")
        set name (string replace -ar '(?i)\b(?:bdrip|webrip|web-dl|bluray|x26[45]|hevc|avc|flac|aac|ac3|eac3|dts|opus|10bit|8bit|[0-9]{3,4}p|[0-9]{4}x[0-9]{3,4})\b' '' "$name")
        echo (string trim "$name")
    end

    function _re_extract_episode
        set -l raw $argv[1]
        set -l name (string replace -r '\.[^.]+$' '' "$raw")

        if string match -qr '(?i)S([0-9]{1,2})\.E([0-9]{1,3})' "$name"
            set -l m (string match -r '(?i)S([0-9]{1,2})\.E([0-9]{1,3})' "$name")
            printf "%s:%s" (_re_pad $m[2]) (_re_pad $m[3])
            return 0
        end

        set -l normalized (_re_normalize_dots "$name")
        set normalized (_re_normalize_underscores "$normalized")
        set normalized (_re_strip_tags "$normalized")

        if string match -qr '(?i)S([0-9]{1,2})E([0-9]{1,3})' "$normalized"
            set -l m (string match -r '(?i)S([0-9]{1,2})E([0-9]{1,3})' "$normalized")
            printf "%s:%s" (_re_pad $m[2]) (_re_pad $m[3])
            return 0
        end

        if string match -qr '([0-9]{1,2})x([0-9]{1,3})' "$normalized"
            set -l m (string match -r '([0-9]{1,2})x([0-9]{1,3})' "$normalized")
            printf "%s:%s" (_re_pad $m[2]) (_re_pad $m[3])
            return 0
        end

        if string match -qr '\[([0-9]{1,3})\]' "$normalized"
            set -l m (string match -r '\[([0-9]{1,3})\]' "$normalized")
            printf "00:%s" (_re_pad $m[2])
            return 0
        end

        if string match -qr ' - ([0-9]{1,3})[ .]' "$normalized"
            set -l m (string match -r ' - ([0-9]{1,3})[ .]' "$normalized")
            printf "00:%s" (_re_pad $m[2])
            return 0
        end

        if string match -qr '[ -]([0-9]{1,3})$' "$normalized"
            set -l m (string match -r '[ -]([0-9]{1,3})$' "$normalized")
            printf "00:%s" (_re_pad $m[2])
            return 0
        end

        if string match -qr '^([0-9]{1,3})[\. ]' "$normalized"
            set -l m (string match -r '^([0-9]{1,3})[\. ]' "$normalized")
            printf "00:%s" (_re_pad $m[2])
            return 0
        end

        if string match -qr ' ([0-9]{1,3}) ' "$normalized"
            set -l m (string match -r ' ([0-9]{1,3}) ' "$normalized")
            printf "00:%s" (_re_pad $m[2])
            return 0
        end

        return 1
    end

    function _re_extract_ext
        set -l name $argv[1]
        set -l known_langs eng rus jpn chi kor fre ger spa ita por ara pol ukr tur vie en ru jp fr de
        set -l video_exts mkv mp4 avi
        set -l audio_exts mka ac3 eac3 flac aac
        set -l sub_exts ass srt vtt sub
        set -l parts (string split '.' "$name")
        set -l n (count $parts)

        if test $n -lt 2
            return 1
        end

        set -l last $parts[$n]

        if contains -- $last $video_exts
            echo ".$last"
            return 0
        end

        if contains -- $last $audio_exts
            set -l ext_parts $last
            set -l i (math "$n - 1")
            if test $i -ge 2
                set -l candidate $parts[$i]
                if not contains -- $candidate $known_langs
                    and not string match -qr '^[0-9]+$' "$candidate"
                    and not string match -q '* *' "$candidate"
                    and test (string length "$candidate") -le 20
                    set -p ext_parts $candidate
                    set i (math "$i - 1")
                end
            end
            if test $i -ge 2
                if contains -- $parts[$i] $known_langs
                    set -p ext_parts $parts[$i]
                end
            end
            echo "."(string join '.' $ext_parts)
            return 0
        end

        if contains -- $last $sub_exts
            set -l ext_parts $last
            set -l i (math "$n - 1")
            if test $i -ge 2
                set -l candidate $parts[$i]
                if not contains -- $candidate $known_langs
                    and not string match -qr '^[0-9]+$' "$candidate"
                    and not string match -q '* *' "$candidate"
                    and test (string length "$candidate") -le 20
                    set -p ext_parts $candidate
                    set i (math "$i - 1")
                end
            end
            if test $i -ge 2
                if contains -- $parts[$i] $known_langs
                    set -p ext_parts $parts[$i]
                end
            end
            echo "."(string join '.' $ext_parts)
            return 0
        end

        return 1
    end

    function _re_new_name
        set -l season $argv[1]
        set -l episode $argv[2]
        set -l orig_base $argv[3]
        set -l ext (_re_extract_ext "$orig_base")
        echo "S"$season"E"$episode$ext
    end

    function _re_scan_files
        find . -maxdepth 1 -type f \( \
            -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \
            -o -name "*.mka" -o -name "*.ac3" -o -name "*.eac3" \
            -o -name "*.flac" -o -name "*.aac" \
            -o -name "*.ass" -o -name "*.srt" -o -name "*.vtt" -o -name "*.sub" \
            \) | sort
    end

    argparse 's/season=' 'o/offset=' h/help -- $argv
    or return 1

    if set -q _flag_help
        echo "usage: rename-episodes [-s SEASON] [-o OFFSET]"
        echo ""
        echo "options:"
        echo "  -s, --season N    season number (auto-detected from directory name)"
        echo "  -o, --offset N    add N to every episode number (default: 0)"
        echo ""
        echo "examples:"
        echo "  rename-episodes"
        echo "  rename-episodes -s 2"
        echo "  rename-episodes -s 1 -o 12"
        return 0
    end

    set -l season
    if set -q _flag_season
        set season (printf "%02d" "$_flag_season")
    else
        set season (_re_detect_season)
        if test $status -ne 0
            echo "error: could not detect season from directory name '(basename $PWD)'"
            echo "       use -s/--season to specify"
            return 1
        end
        echo "detected season $season from directory name"
    end

    set -l offset 0
    if set -q _flag_offset
        set offset (math (printf "%d" "$_flag_offset"))
    end

    set -l files (_re_scan_files)
    if test (count $files) -eq 0
        echo "error: no media files found in current directory"
        return 1
    end

    set -l entries
    set -l skipped

    for f in $files
        set -l base (basename "$f")
        set -l parsed (_re_extract_episode "$base")
        if test $status -eq 0
            set -l parts (string split ':' "$parsed")
            set -l ep_season $parts[1]
            set -l ep_num $parts[2]

            if test $offset -ne 0
                set -l ep_num_decimal (string replace -r '^0*' '' "$ep_num")
                test -z "$ep_num_decimal" && set ep_num_decimal 0
                set ep_num (printf "%02d" (math "$ep_num_decimal + $offset"))
            end

            if test "$ep_season" = 00
                set ep_season "$season"
            end

            set -a entries "$ep_season:$ep_num:$f"
        else
            set -a skipped "$base"
        end
    end

    if test (count $entries) -eq 0
        echo "error: could not extract episode numbers from any files"
        return 1
    end

    echo ""
    echo "preview:"
    echo "────────────────────────────────────────────────────────────────"

    for entry in (printf '%s\n' $entries | sort -t: -k1,1 -k2,2)
        set -l parts (string split ':' "$entry")
        set -l ep_season $parts[1]
        set -l ep_num $parts[2]
        set -l fpath $parts[3]
        set -l base (basename "$fpath")
        set -l newname (_re_new_name "$ep_season" "$ep_num" "$base")
        printf "  %-55s → %s\n" "$base" "$newname"
    end

    if test (count $skipped) -gt 0
        echo ""
        echo "skipped:"
        for s in $skipped
            echo "  $s"
        end
    end

    echo "────────────────────────────────────────────────────────────────"
    printf "  %d files" (count $entries)
    if test (count $skipped) -gt 0
        printf ", %d skipped" (count $skipped)
    end
    echo ""
    echo ""

    read -l -P "proceed? [y/N] " confirm
    if not string match -qi y "$confirm"
        echo cancelled
        return 1
    end

    set -l errors 0

    for entry in (printf '%s\n' $entries | sort -t: -k1,1 -k2,2)
        set -l parts (string split ':' "$entry")
        set -l ep_season $parts[1]
        set -l ep_num $parts[2]
        set -l fpath $parts[3]
        set -l base (basename "$fpath")
        set -l dir (dirname "$fpath")
        set -l newname (_re_new_name "$ep_season" "$ep_num" "$base")

        if mv "$fpath" "$dir/$newname"
            echo "  $base → $newname"
        else
            echo "  error: failed to rename $base"
            set errors (math $errors + 1)
        end
    end

    echo ""
    if test $errors -eq 0
        echo "done - "(count $entries)" files renamed"
    else
        echo "done with $errors error(s)"
    end
end
