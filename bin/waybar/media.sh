#!/bin/bash

PREV_TRACK=""
PREV_STATUS=""
SCROLL_PID=""

function validate-environment
{
    if ! command -v playerctl >/dev/null 2>&1
    then
        echo "error: playerctl not found, install it with your package manager." >&2
        return 1
    fi
}

function json-escape
{
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

function format-display
{
    local status="$1"
    local artist="$2"
    local title="$3"

    case "$status" in
        Playing) echo "PLAYING: $artist - $title" ;;
        Paused) echo "PAUSED: $artist - $title" ;;
        *) echo "" ;;
    esac
}

function create-scrolling-display
{
    local status="$1"
    local media_text="$2"
    local scroll_pos="$3"
    local max_len=40
    local separator=" | "
    local prefix=""

    case "$status" in
        Playing) prefix="PLAYING: " ;;
        Paused) prefix="PAUSED: " ;;
    esac

    local available_space=$((max_len - ${#prefix}))

    if [[ ${#media_text} -le $available_space ]]
    then
        printf "%s%-${available_space}s" "$prefix" "$media_text"
        return
    fi

    local extended_media="${media_text}${separator}${media_text}"
    local start_pos=$((scroll_pos % (${#media_text} + ${#separator})))
    local scrolled_media="${extended_media:$start_pos:$available_space}"

    printf "%s%-${available_space}s" "$prefix" "$scrolled_media"
}

function output-json
{
    local text="$1"
    local tooltip="$2"

    local escaped_text=$(json-escape "$text")
    local escaped_tooltip=$(json-escape "$tooltip")

    echo "{\"text\": \"$escaped_text\", \"tooltip\": \"$escaped_tooltip\"}"
}

function scroll-handler
{
    local status="$1"
    local artist="$2"
    local title="$3"
    local tooltip="$4"
    local media_text="$artist - $title"
    local scroll_pos=0
    local scroll_speed=0.2

    while true
    do
        local display_text=$(create-scrolling-display "$status" "$media_text" "$scroll_pos")
        output-json "$display_text" "$tooltip"
        scroll_pos=$((scroll_pos + 1))
        sleep "$scroll_speed"
    done
}

function stop-scroll
{
    if [ -n "$SCROLL_PID" ]
    then
        kill "$SCROLL_PID" 2>/dev/null
        wait "$SCROLL_PID" 2>/dev/null
        SCROLL_PID=""
    fi
}

function handle-metadata-change
{
    local status="$1"
    local artist="$2"
    local title="$3"

    if [ -z "$status" ] || [ "$status" = "Stopped" ]
    then
        stop-scroll
        output-json "" ""
        PREV_TRACK=""
        PREV_STATUS=""
        return
    fi

    local current_track="$artist|$title"
    local full_display=$(format-display "$status" "$artist" "$title")
    local tooltip="$artist - $title"

    if [ "$current_track" != "$PREV_TRACK" ]
    then
        stop-scroll
        PREV_TRACK="$current_track"
        PREV_STATUS="$status"

        if [ ${#full_display} -gt 40 ]
        then
            scroll-handler "$status" "$artist" "$title" "$tooltip" &
            SCROLL_PID=$!
        else
            output-json "$full_display" "$tooltip"
        fi
    elif [ "$status" != "$PREV_STATUS" ]
    then
        PREV_STATUS="$status"
        local current_display=$(format-display "$status" "$artist" "$title")

        if [ ${#current_display} -le 40 ]
        then
            stop-scroll
            output-json "$current_display" "$tooltip"
        else
            stop-scroll
            scroll-handler "$status" "$artist" "$title" "$tooltip" &
            SCROLL_PID=$!
        fi
    fi
}

function cleanup
{
    stop-scroll
    exit 0
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi

    trap cleanup SIGTERM SIGINT EXIT
    output-json "" ""

    playerctl --follow metadata --format '{{status}}|{{artist}}|{{title}}' 2>/dev/null | while IFS='|' read -r status artist title
    do
        handle-metadata-change "$status" "$artist" "$title"
    done
}

main "$@"
