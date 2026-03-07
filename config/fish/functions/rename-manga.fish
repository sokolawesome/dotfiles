function rename-manga -d "bulk rename manga volumes and chapters to 01.cbz / c001.cbz format"

    function _rm_scan_files
        find . -maxdepth 1 -type f \( -name "*.cbz" -o -name "*.cbr" \) | sort
    end

    function _rm_extract_ext
        set -l parts (string split '.' $argv[1])
        set -l last $parts[(count $parts)]
        if contains -- $last cbz cbr
            echo ".$last"
            return 0
        end
        return 1
    end

    function _rm_pad
        set -l n (string replace -r '^0*' '' $argv[1])
        test -z "$n"; and set n 0
        if test "$argv[2]" -eq 3
            printf "%03d" "$n"
        else
            printf "%02d" "$n"
        end
    end

    function _rm_extract_type_num
        set -l name (string replace -r '\.[^.]+$' '' $argv[1])

        if string match -qr '(?i)\bv(?:ol(?:ume)?)?\.?\s*([0-9]+)' "$name"
            set -l m (string match -r '(?i)\bv(?:ol(?:ume)?)?\.?\s*([0-9]+)' "$name")
            printf "v:%s" (_rm_pad $m[2] 2)
            return 0
        end

        if string match -qr '(?i)\bc(?:h(?:apter)?)?\.?\s*([0-9]+)' "$name"
            set -l m (string match -r '(?i)\bc(?:h(?:apter)?)?\.?\s*([0-9]+)' "$name")
            printf "c:%s" (_rm_pad $m[2] 3)
            return 0
        end

        if string match -qr '\b([0-9]{2,3})\b' "$name"
            set -l m (string match -r '\b([0-9]{2,3})\b' "$name")
            printf "c:%s" (_rm_pad $m[2] 3)
            return 0
        end

        return 1
    end

    argparse 'h/help' -- $argv
    or return 1

    if set -q _flag_help
        echo "usage: rename-manga"
        echo ""
        echo "renames manga files in current directory to clean format:"
        echo "  volumes  →  01.cbz"
        echo "  chapters →  c001.cbz"
        echo ""
        echo "recognized patterns:"
        echo "  v09, vol.09, volume 9  →  volume"
        echo "  c03, ch.03, chapter 3  →  chapter"
        echo "  003                    →  chapter (bare number fallback)"
        return 0
    end

    set -l files (_rm_scan_files)
    if test (count $files) -eq 0
        echo "error: no manga files found in current directory"
        return 1
    end

    set -l entries
    set -l skipped

    for f in $files
        set -l base (basename "$f")
        set -l parsed (_rm_extract_type_num "$base")
        if test $status -eq 0
            set -l parts (string split ':' "$parsed")
            set -a entries "$parts[1]:$parts[2]:$f"
        else
            set -a skipped "$base"
        end
    end

    if test (count $entries) -eq 0
        echo "error: could not extract numbers from any files"
        return 1
    end

    echo ""
    echo "preview:"
    echo "────────────────────────────────────────────────────────────────"

    for entry in (printf '%s\n' $entries | sort -t: -k1,1 -k2,2n)
        set -l parts (string split ':' "$entry")
        set -l type $parts[1]
        set -l num $parts[2]
        set -l fpath (string join ':' $parts[3..-1])
        set -l base (basename "$fpath")
        set -l ext (_rm_extract_ext "$base")
        set -l preview (test "$type" = v; and echo "$num$ext"; or echo "$type$num$ext")
        printf "  %-55s → %s\n" "$base" "$preview"
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
    if not string match -qi 'y' "$confirm"
        echo "cancelled"
        return 1
    end

    set -l errors 0

    for entry in (printf '%s\n' $entries | sort -t: -k1,1 -k2,2n)
        set -l parts (string split ':' "$entry")
        set -l type $parts[1]
        set -l num $parts[2]
        set -l fpath (string join ':' $parts[3..-1])
        set -l base (basename "$fpath")
        set -l dir (dirname "$fpath")
        set -l ext (_rm_extract_ext "$base")
        set -l newname (test "$type" = v; and echo "$num$ext"; or echo "$type$num$ext")

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
