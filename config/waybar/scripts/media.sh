#!/bin/bash

UPDATE_INTERVAL=0.5
MAX_LEN=30
SEPARATOR=" | "

json_escape() {
    echo -n "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\//\\\//g; s/\n/\\n/g; s/\r/\\r/g; s/\t/\\t/g'
}

xml_escape() {
    printf '%s' "$1" | sed \
        -e 's/&/\&amp;/g' \
        -e 's/</\&lt;/g' \
        -e 's/>/\&gt;/g' \
        -e 's/"/\&quot;/g' \
        -e "s/'/\&apos;/g"
}

get_player_info() {
    local metadata_json
    metadata_json=$(playerctl metadata --format '{{status}}|{{artist}}|{{title}}' 2>/dev/null)
    echo "$metadata_json"
}

format_media_text() {
    local status="$1"
    local artist="$2"
    local title="$3"

    case "$status" in
        "Playing")
            echo "PLAYING: $artist - $title"
            ;;
        "Paused")
            echo "PAUSED: $artist - $title"
            ;;
        *)
            echo ""
            ;;
    esac
}

create_scrolling_text() {
    local full_text="$1"
    local prefix="$2"
    local media_part="$3"
    local scroll_index="$4"

    if [ "${#media_part}" -le "$MAX_LEN" ]; then
        echo "$full_text"
    else
        local padded_media="${media_part}${SEPARATOR}${media_part}"
        local display_media=$(echo "$padded_media" | cut -c$((scroll_index + 1))-$((scroll_index + MAX_LEN)))
        echo "${prefix}${display_media}"
    fi
}

output_json() {
    local text="$1"
    local tooltip="$2"

    local escaped_text=$(json_escape "$text")
    local escaped_tooltip=$(xml_escape "$(json_escape "$tooltip")")

    echo "{\"text\": \"$escaped_text\", \"tooltip\": \"$escaped_tooltip\"}"
}

handle_exit() {
    exit 0
}

main() {
    trap handle_exit SIGTERM SIGINT

    local previous_full_text=""
    local scroll_index=0

    while true; do
        IFS='|' read -r status artist title <<< "$(get_player_info)"

        if [[ -z "$status" || "$status" == "Stopped" ]]; then
            output_json "" ""
            previous_full_text=""
            scroll_index=0
        else
            local media_info="$artist - $title"
            local current_full_text=$(format_media_text "$status" "$artist" "$title")

            if [[ "$current_full_text" != "$previous_full_text" ]]; then
                previous_full_text="$current_full_text"
                scroll_index=0
            fi

            local prefix=""
            case "$status" in
                "Playing") prefix="PLAYING: " ;;
                "Paused") prefix="PAUSED: " ;;
            esac

            local display_text=$(create_scrolling_text "$current_full_text" "$prefix" "$media_info" "$scroll_index")
            output_json "$display_text" "$current_full_text"

            if [ "${#media_info}" -gt "$MAX_LEN" ]; then
                scroll_index=$(( (scroll_index + 1) % (${#media_info} + ${#SEPARATOR}) ))
            fi
        fi

        sleep "$UPDATE_INTERVAL"
    done
}

main "$@"
