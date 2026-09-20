#!/usr/bin/env bash
# Anything only the candidate can answer has to reach the page he actually
# reads. `[ask]` marks such a question wherever it lives; this asserts each one
# is also a line in pipeline.md's Todo, so the fact base cannot accumulate a
# private backlog he never sees. It went 20 to 3 that way once.
#
# The key is the word after the marker, `[ask: Tenure]`. Square brackets and no
# parentheses, so check-citations.sh does not read it as a markdown link, and
# because the prose around it is too long and too fluid to match on. Untagged
# open questions are not failures: tagging is a per-entry decision, and a check
# that fires on everything gets ignored.
set -uo pipefail
cd "$(dirname "$0")/.."

# a file deleted but not yet staged is still in the index, and grep would
# rather say so on stderr every run: the same filter check-citations.sh makes
files() {
  git ls-files -z --cached --others --exclude-standard '*.md' |
    while IFS= read -r -d '' f; do [ -f "$f" ] && printf '%s\0' "$f"; done
}

asked=$(files | xargs -0 grep -noE '\[ask: *[^]]+\]' | sed 's/\[ask: *//; s/\]$//')

# A placeholder names the shape the marker takes and is not a real question,
# the same exemption check-citations.sh makes for `YYYY-MM-DD-topic.md`.
asked=$(grep -v '<[^>]*>' <<< "$asked")

missing=0
while IFS=: read -r file line key; do
  [ -n "${key:-}" ] || continue
  [ "$file" = "pipeline.md" ] && continue
  grep -qiF "$key" pipeline.md && continue
  echo "$file:$line: [ask: $key] reaches no line in pipeline.md"
  missing=$((missing + 1))
done <<< "$asked"

[ "$missing" -eq 0 ] && exit 0
echo
echo "$missing question(s) for the candidate that he cannot see. Put each on pipeline.md's Todo."
exit 1
