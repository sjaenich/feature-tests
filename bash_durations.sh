#!/usr/bin/env bash
# Usage: bash durations.sh [logs_directory]
# Requires GNU stat (Linux).

set -euo pipefail
shopt -s nullglob

root=${1:-logs}

if [[ ! -d "$root" ]]; then
    printf 'Directory not found: %s\n' "$root" >&2
    exit 1
fi

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT

touch "$tmp/all"

format_duration() {
    local seconds=$1
    printf '%dd %02dh %02dm %02ds' \
        "$((seconds / 86400))" \
        "$((seconds % 86400 / 3600))" \
        "$((seconds % 3600 / 60))" \
        "$((seconds % 60))"
}

summarize() {
    awk '
        function duration(s, d, h, m) {
            d = int(s / 86400)
            h = int(s % 86400 / 3600)
            m = int(s % 3600 / 60)
            return sprintf("%dd %02dh %02dm %05.2fs",
                           d, h, m, s % 60)
        }
        {
            sum += $1
            if (NR == 1 || $1 < minimum) minimum = $1
            if (NR == 1 || $1 > maximum) maximum = $1
        }
        END {
            if (!NR) {
                print "  No measurable durations (need at least two files)."
            } else {
                printf "  Count: %d\n", NR
                printf "  Mean:  %s\n", duration(sum / NR)
                printf "  Min:   %s\n", duration(minimum)
                printf "  Max:   %s\n", duration(maximum)
            }
        }
    ' "$1"
}

for library in "$root"/*/; do
    name=${library%/}
    name=${name##*/}

    : > "$tmp/timestamps"
    : > "$tmp/library"

    # Collect all regular files directly inside this library directory.
    for file in "$library"*; do
        [[ -f "$file" ]] || continue
        timestamp=$(stat -c %Y -- "$file")
        printf '%s\t%s\n' "$timestamp" "${file##*/}" \
            >> "$tmp/timestamps"
    done

    sort -n -k1,1 "$tmp/timestamps" > "$tmp/sorted"

    printf '\n%s\n' "$name"
    previous=""

    while IFS=$'\t' read -r timestamp filename; do
        if [[ -z "$previous" ]]; then
            printf '  %s: unknown (first completion)\n' "$filename"
        else
            elapsed=$((timestamp - previous))
            printf '  %s: %s\n' "$filename" \
                "$(format_duration "$elapsed")"
            printf '%s\n' "$elapsed" >> "$tmp/library"
        fi
        previous=$timestamp
    done < "$tmp/sorted"

    summarize "$tmp/library"
    cat "$tmp/library" >> "$tmp/all"
done

printf '\nALL LIBRARIES\n'
summarize "$tmp/all"
