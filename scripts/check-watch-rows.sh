#!/usr/bin/env bash
# A `watch` row on pipeline.md delegates the company to the sweep, and the
# thing doing the watching is that company's row in me/channels.md. A `watch`
# with no channel row is a company nobody is watching and nobody is working,
# which is the one status that can rot without anyone noticing. Six rows sat
# that way on 2026-09-16, which is why this runs instead of being remembered.
set -uo pipefail
cd "$(dirname "$0")/.."

# Column 1 is the company, stripped of any markdown link; column 2 the status.
watched=$(
  awk -F'|' '$3 ~ /^ *watch *$/ {
    name = $2
    gsub(/^ *\[|\]\([^)]*\)|^ *| *$/, "", name)
    print name
  }' pipeline.md
)

missing=0
while IFS= read -r name; do
  [ -n "${name:-}" ] || continue
  # A merged row names two companies as "A / B": a channel on either half is
  # a real watcher on that half, and the row's own cell says which is blind.
  found=0
  while IFS= read -r half; do
    half=$(printf '%s' "$half" | sed 's/^ *//;s/ *$//')
    grep -qF "| $half |" me/channels.md && found=1
  done <<< "$(tr '/' '\n' <<< "$name")"
  [ "$found" -eq 1 ] && continue
  echo "pipeline.md: $name is \`watch\` with no row in me/channels.md"
  missing=$((missing + 1))
done <<< "$watched"

[ "$missing" -eq 0 ] && exit 0
echo
echo "$missing unwatched \`watch\` row(s). Catalog the board, add it to Watched by hand, or make the row a \`lead\`."
exit 1
