#!/bin/bash

SCROLL_SPEED=0.2
MAX_LEN=40
SEPARATOR=" | "

PREV_TRACK=""
PREV_STATUS=""

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

xml_escape() {
    printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&apos;/g'
}

format_display() {
    local status="$1"
    local artist="$2"
    local title="$3"

    case "$status" in
        "Playing") echo "PLAYING: $artist - $title" ;;
        "Paused") echo "PAUSED: $artist - $title" ;;
        *) echo "" ;;
    esac
}

create_scrolling_display() {
    local status="$1"
    local media_text="$2"
    local scroll_pos="$3"

    local prefix=""
    case "$status" in
        "Playing") prefix="PLAYING: " ;;
        "Paused") prefix="PAUSED: " ;;
    esac

    local available_space=$((MAX_LEN - ${#prefix}))

    if [[ ${#media_text} -le $available_space ]]; then
        printf "%s%-${available_space}s" "$prefix" "$media_text"
        return
    fi

    local extended_media="${media_text}${SEPARATOR}${media_text}"
    local start_pos=$((scroll_pos % (${#media_text} + ${#SEPARATOR})))
    local scrolled_media="${extended_media:$start_pos:$available_space}"

    printf "%s%-${available_space}s" "$prefix" "$scrolled_media"
}

output_json() {
    local text="$1"
    local tooltip="$2"

    local escaped_text=$(json_escape "$text")
    local escaped_tooltip=$(xml_escape "$(json_escape "$tooltip")")

    echo "{\"text\": \"$escaped_text\", \"tooltip\": \"$escaped_tooltip\"}"
}

scroll_handler() {
    local status="$1"
    local artist="$2"
    local title="$3"
    local tooltip="$4"
    local media_text="$artist - $title"
    local scroll_pos=0

    while true; do
        local display_text=$(create_scrolling_display "$status" "$media_text" "$scroll_pos")
        output_json "$display_text" "$tooltip" "$status"

        scroll_pos=$((scroll_pos + 1))
        sleep "$SCROLL_SPEED"
    done
}

handle_metadata_change() {
    local status="$1"
    local artist="$2"
    local title="$3"

    if [[ -z "$status" || "$status" == "Stopped" ]]; then
        jobs -p | xargs -r kill 2>/dev/null
        output_json "" "" ""
        PREV_TRACK=""
        PREV_STATUS=""
        return
    fi

    local current_track="$artist|$title"
    local full_display=$(format_display "$status" "$artist" "$title")
    local tooltip="$artist - $title"
    local media_text="$artist - $title"

    if [[ "$current_track" != "$PREV_TRACK" ]]; then
        jobs -p | xargs -r kill 2>/dev/null
        wait 2>/dev/null

        PREV_TRACK="$current_track"
        PREV_STATUS="$status"

        if [[ ${#full_display} -gt $MAX_LEN ]]; then
            scroll_handler "$status" "$artist" "$title" "$tooltip" &
        else
            output_json "$full_display" "$tooltip" "$status"
        fi
    elif [[ "$status" != "$PREV_STATUS" ]]; then
        PREV_STATUS="$status"
        local current_display=$(format_display "$status" "$artist" "$title")

        if [[ ${#current_display} -le $MAX_LEN ]]; then
            jobs -p | xargs -r kill 2>/dev/null
            wait 2>/dev/null
            output_json "$current_display" "$tooltip" "$status"
        else
            jobs -p | xargs -r kill 2>/dev/null
            wait 2>/dev/null
            scroll_handler "$status" "$artist" "$title" "$tooltip" &
        fi
    fi
}

cleanup() {
    jobs -p | xargs -r kill 2>/dev/null
    wait 2>/dev/null
    exit 0
}

main() {
    trap cleanup SIGTERM SIGINT EXIT

    output_json "" "" ""

    playerctl --follow metadata --format '{{status}}|{{artist}}|{{title}}' 2>/dev/null | \
    while IFS='|' read -r status artist title; do
        handle_metadata_change "$status" "$artist" "$title"
    done
}

main "$@"
