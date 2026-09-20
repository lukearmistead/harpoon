#!/usr/bin/env bash
# Fails when profile/criteria.md reaches the ceiling it sets for itself, which
# it states in its own opening lines ("Under 100 lines"). A ceiling nobody
# measures ratchets: the file sat at 99 while five additions were queued for
# it. Change the number in the file, not here.
set -uo pipefail
cd "$(dirname "$0")/.."

file=profile/criteria.md
[ -f "$file" ] || exit 0

limit=$(head -10 "$file" | grep -oiE 'under [0-9]+ lines' | grep -oE '[0-9]+' | head -1)
if [ -z "$limit" ]; then
  echo "$file states no line ceiling in its opening lines, so nothing here" \
       "can enforce one. Say it in the file, as \"Under 100 lines\"." >&2
  exit 1
fi

lines=$(wc -l < "$file" | tr -d ' ')
if [ "$lines" -ge "$limit" ]; then
  echo "$file is $lines lines; it promises under $limit. Cut before adding." >&2
  exit 1
fi
