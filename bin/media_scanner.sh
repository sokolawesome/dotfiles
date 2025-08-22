#!/bin/bash

function validate-environment
{
    for cmd in ffprobe find du numfmt
    do
        if ! command -v "$cmd" >/dev/null 2>&1
        then
            echo "error: $cmd not found, install it with your package manager."
            return 1
        fi
    done
}

function get-file-size
{
    local path="$1"
    local size_bytes=$(du -sb "$path" 2>/dev/null | cut -f1)
    if [ -n "$size_bytes" ] && [ "$size_bytes" -gt 0 ]
    then
        numfmt --to=iec --suffix=B "$size_bytes" | sed 's/B$/ B/'
    else
        echo "0 B"
    fi
}

function detect-category
{
    local title="$1"
    local base_path="$2"
    
    if [[ "$base_path" == *"/animation/"* ]]
    then
        echo "Animation"
    elif [[ "$base_path" == *"/anime/"* ]]
    then
        echo "Anime"
    else
        echo "Live Action"
    fi
}

function detect-type
{
    local base_path="$1"
    
    if [[ "$base_path" == *"/movies"* ]]
    then
        echo "Movie"
    else
        echo "Series"
    fi
}

function get-video-metadata
{
    local video_file="$1"
    
    if [ ! -f "$video_file" ]
    then
        echo "Unknown|Unknown|Unknown|Unknown|Unknown"
        return
    fi
    
    local width=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local height=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local codec=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local bitrate=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local color_primaries=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=color_primaries -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local color_transfer=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=color_transfer -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    local pix_fmt=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=pix_fmt -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1)
    
    width=$(echo "$width" | sed 's/,.*$//' | tr -d ' ')
    height=$(echo "$height" | sed 's/,.*$//' | tr -d ' ')
    codec=$(echo "$codec" | sed 's/,.*$//' | tr -d ' ')
    bitrate=$(echo "$bitrate" | sed 's/,.*$//' | tr -d ' ')
    
    local resolution="Unknown"
    if [[ -n "$width" && -n "$height" && "$width" != "N/A" && "$height" != "N/A" && "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ && "$width" -gt 0 && "$height" -gt 0 ]]
    then
        resolution="${width}x${height}"
    fi
    
    local video_codec="Unknown"
    case "$codec" in
        h264) video_codec="H.264" ;;
        hevc|h265) video_codec="H.265" ;;
        av1) video_codec="AV1" ;;
        vp9) video_codec="VP9" ;;
        mpeg2video) video_codec="MPEG-2" ;;
        mpeg4) video_codec="MPEG-4" ;;
        *) 
            if [ -n "$codec" ] && [ "$codec" != "N/A" ]
            then
                video_codec="${codec^^}"
            fi
            ;;
    esac
    
    local formatted_bitrate="Unknown"
    if [[ -n "$bitrate" && "$bitrate" != "N/A" && "$bitrate" =~ ^[0-9]+$ && "$bitrate" -gt 0 ]]
    then
        local bitrate_kbps=$((bitrate / 1000))
        formatted_bitrate="${bitrate_kbps} kbps"
    else
        local overall_bitrate=$(ffprobe -v quiet -show_entries format=bit_rate -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null | head -1 | sed 's/,.*$//' | tr -d ' ')
        if [[ -n "$overall_bitrate" && "$overall_bitrate" != "N/A" && "$overall_bitrate" =~ ^[0-9]+$ && "$overall_bitrate" -gt 0 ]]
        then
            local bitrate_kbps=$((overall_bitrate / 1000))
            formatted_bitrate="${bitrate_kbps} kbps"
        fi
    fi
    
    local hdr="No"
    if [[ "$color_primaries" == "bt2020" || "$color_transfer" == "smpte2084" || "$color_transfer" == "arib-std-b67" ]]
    then
        hdr="Yes"
    fi
    
    local color_depth="8-bit"
    if [[ "$pix_fmt" == *"10le"* || "$pix_fmt" == *"10be"* ]]
    then
        color_depth="10-bit"
    elif [[ "$pix_fmt" == *"12le"* || "$pix_fmt" == *"12be"* ]]
    then
        color_depth="12-bit"
    fi
    
    echo "${resolution}|${video_codec}|${formatted_bitrate}|${hdr}|${color_depth}"
}

function get-audio-tracks
{
    local video_file="$1"
    
    if [ ! -f "$video_file" ]
    then
        echo "0"
        return
    fi
    
    local audio_info=$(ffprobe -v quiet -select_streams a -show_entries stream=index:stream_tags=language -of csv=p=0 "$video_file" 2>/dev/null)
    local count=$(echo "$audio_info" | wc -l)
    
    if [ -z "$audio_info" ] || [ "$audio_info" = "" ]
    then
        echo "0"
        return
    fi
    
    local languages=$(echo "$audio_info" | cut -d',' -f2 | sort -u | grep -v "^$" | tr '\n' ',' | sed 's/,$//')
    
    if [ -n "$languages" ]
    then
        echo "$count ($languages)"
    else
        echo "$count"
    fi
}

function get-subtitle-tracks
{
    local video_file="$1"
    
    if [ ! -f "$video_file" ]
    then
        echo "0"
        return
    fi
    
    local sub_info=$(ffprobe -v quiet -select_streams s -show_entries stream=index:stream_tags=language -of csv=p=0 "$video_file" 2>/dev/null)
    local count=$(echo "$sub_info" | wc -l)
    
    if [ -z "$sub_info" ] || [ "$sub_info" = "" ]
    then
        echo "0"
        return
    fi
    
    local languages=$(echo "$sub_info" | cut -d',' -f2 | sort -u | grep -v "^$" | tr '\n' ',' | sed 's/,$//')
    
    if [ -n "$languages" ]
    then
        echo "$count ($languages)"
    else
        echo "$count"
    fi
}

function get-external-subtitles
{
    local season_path="$1"
    
    local sub_files=$(find "$season_path" -maxdepth 1 -type f \( -name "*.srt" -o -name "*.ass" -o -name "*.vtt" \) 2>/dev/null)
    local count=$(echo "$sub_files" | grep -v "^$" | wc -l)
    
    if [ "$count" -eq 0 ]
    then
        echo "0"
        return
    fi
    
    local languages=""
    while IFS= read -r file
    do
        if [ -n "$file" ]
        then
            local basename_file=$(basename "$file")
            local lang=$(echo "$basename_file" | sed -E 's/.*\.([a-z]{2,3})\.[^.]+\.[^.]+$/\1/')
            if [ "$lang" != "$basename_file" ]
            then
                languages="${languages}${lang}\n"
            fi
        fi
    done <<< "$sub_files"
    
    local unique_langs=$(echo -e "$languages" | sort -u | grep -v "^$" | tr '\n' ',' | sed 's/,$//')
    
    if [ -n "$unique_langs" ]
    then
        echo "$count ($unique_langs)"
    else
        echo "$count"
    fi
}

function get-external-audio
{
    local season_path="$1"
    
    local audio_files=$(find "$season_path" -maxdepth 1 -type f \( -name "*.aac" -o -name "*.ac3" -o -name "*.dts" -o -name "*.flac" -o -name "*.mp3" \) 2>/dev/null)
    local count=$(echo "$audio_files" | grep -v "^$" | wc -l)
    
    if [ "$count" -eq 0 ]
    then
        echo "0"
        return
    fi
    
    local languages=""
    while IFS= read -r file
    do
        if [ -n "$file" ]
        then
            local basename_file=$(basename "$file")
            local lang=$(echo "$basename_file" | sed -E 's/.*\.([a-z]{2,3})\.[^.]+\.[^.]+$/\1/')
            if [ "$lang" != "$basename_file" ]
            then
                languages="${languages}${lang}\n"
            fi
        fi
    done <<< "$audio_files"
    
    local unique_langs=$(echo -e "$languages" | sort -u | grep -v "^$" | tr '\n' ',' | sed 's/,$//')
    
    if [ -n "$unique_langs" ]
    then
        echo "$count ($unique_langs)"
    else
        echo "$count"
    fi
}

function get-file-format
{
    local video_file="$1"
    
    if [ ! -f "$video_file" ]
    then
        echo "Unknown"
        return
    fi
    
    local extension="${video_file##*.}"
    echo "${extension,,}"
}

function find-first-episode
{
    local season_path="$1"
    
    local first_ep=""
    
    first_ep=$(find "$season_path" -maxdepth 1 -type f -name "*E01.*" \( -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \) | head -1)
    
    if [ -z "$first_ep" ]
    then
        first_ep=$(find "$season_path" -maxdepth 1 -type f \( -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \) | sort | head -1)
    fi
    
    echo "$first_ep"
}

function count-episodes
{
    local season_path="$1"
    local count=$(find "$season_path" -maxdepth 1 -type f \( -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \) | wc -l)
    echo "$count"
}

function scan-media-directory
{
    local base_path="$1"
    local output_file="$2"
    
    echo "Scanning media directory: $base_path"
    echo "Output file: $output_file"
    echo
    
    cat > "$output_file" << 'EOF'
# Media Library Inventory

| Title | Type | Category | Episodes | Resolution | Video Codec | Audio Tracks | Built-in Subs | External Subs | External Audio | HDR | Bitrate | Color Depth | File Format | Size | Source |
|-------|------|----------|----------|------------|-------------|--------------|---------------|---------------|----------------|-----|---------|-------------|-------------|------|--------|
EOF
    
    local media_dirs=$(find "$base_path" -type d -name "*\[tvdbid-*\]" | grep -v "/Season " | sort)
    
    while IFS= read -r media_dir
    do
        if [ -z "$media_dir" ]
        then
            continue
        fi
        
        echo "Processing: $(basename "$media_dir")"
        
        local title=$(basename "$media_dir" | sed 's/ \[tvdbid-[0-9]*\]$//')
        local type=$(detect-type "$media_dir")
        local category=$(detect-category "$title" "$media_dir")
        
        if [ "$type" = "Movie" ]
        then
            local movie_file=$(find "$media_dir" -maxdepth 1 -type f \( -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \) | head -1)
            
            if [ -n "$movie_file" ]
            then
                local episodes="1"
                local video_meta=$(get-video-metadata "$movie_file")
                local resolution=$(echo "$video_meta" | cut -d'|' -f1)
                local video_codec=$(echo "$video_meta" | cut -d'|' -f2)
                local bitrate=$(echo "$video_meta" | cut -d'|' -f3)
                local hdr=$(echo "$video_meta" | cut -d'|' -f4)
                local color_depth=$(echo "$video_meta" | cut -d'|' -f5)
                local audio_tracks=$(get-audio-tracks "$movie_file")
                local builtin_subs=$(get-subtitle-tracks "$movie_file")
                local external_subs=$(get-external-subtitles "$media_dir")
                local external_audio=$(get-external-audio "$media_dir")
                local file_format=$(get-file-format "$movie_file")
                local size=$(get-file-size "$media_dir")
                
                echo "| $title | $type | $category | $episodes | $resolution | $video_codec | $audio_tracks | $builtin_subs | $external_subs | $external_audio | $hdr | $bitrate | $color_depth | $file_format | $size | |" >> "$output_file"
            fi
        else
            local season_dirs=$(find "$media_dir" -maxdepth 1 -type d -name "*Season*" | sort)
            
            while IFS= read -r season_dir
            do
                if [ -z "$season_dir" ]
                then
                    continue
                fi
                
                echo "  Processing: $(basename "$season_dir")"
                
                local season_name=$(basename "$season_dir" | sed 's/ \[tvdbid-[0-9]*\]$//')
                local full_title="${title} - ${season_name}"
                local first_episode=$(find-first-episode "$season_dir")
                
                if [ -n "$first_episode" ]
                then
                    local episodes=$(count-episodes "$season_dir")
                    local video_meta=$(get-video-metadata "$first_episode")
                    local resolution=$(echo "$video_meta" | cut -d'|' -f1)
                    local video_codec=$(echo "$video_meta" | cut -d'|' -f2)
                    local bitrate=$(echo "$video_meta" | cut -d'|' -f3)
                    local hdr=$(echo "$video_meta" | cut -d'|' -f4)
                    local color_depth=$(echo "$video_meta" | cut -d'|' -f5)
                    local audio_tracks=$(get-audio-tracks "$first_episode")
                    local builtin_subs=$(get-subtitle-tracks "$first_episode")
                    local external_subs=$(get-external-subtitles "$season_dir")
                    local external_audio=$(get-external-audio "$season_dir")
                    local file_format=$(get-file-format "$first_episode")
                    local size=$(get-file-size "$season_dir")
                    
                    echo "| $full_title | $type | $category | $episodes | $resolution | $video_codec | $audio_tracks | $builtin_subs | $external_subs | $external_audio | $hdr | $bitrate | $color_depth | $file_format | $size | |" >> "$output_file"
                fi
            done <<< "$season_dirs"
        fi
        
    done <<< "$media_dirs"
    
    echo
    echo "Scan completed successfully!"
    echo "Results saved to: $output_file"
}

function main
{
    if ! validate-environment
    then
        exit 1
    fi
    
    local media_path="${1:-/mnt/hdd}"
    local output_file="${2:-media_inventory.md}"
    
    if [ ! -d "$media_path" ]
    then
        echo "error: media directory '$media_path' does not exist"
        exit 1
    fi
    
    case "$1" in
        --help|-h)
            echo "usage: $0 [media_path] [output_file]"
            echo "  media_path       path to scan (default: /mnt/hdd)"
            echo "  output_file      output markdown file (default: media_inventory.md)"
            echo
            echo "example: $0 /mnt/hdd my_media.md"
            exit 0
            ;;
    esac
    
    scan-media-directory "$media_path" "$output_file"
}

main "$@"