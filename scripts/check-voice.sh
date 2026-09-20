#!/usr/bin/env bash
# The voice rules are the only rules in this repo with no instrument behind
# them, which means they hold exactly as long as whoever is writing remembers
# them. Two of them are machine-checkable, so they are checked.
#
# Em dashes are banned everywhere and there are none in tracked markdown today,
# so this starts clean rather than starting with a backlog to grandfather.
#
# The banned phrases are scoped to what gets sent to an employer, because a
# posting that says "passionate" is evidence and quoting it is right. A line
# holding a quotation mark is skipped for the same reason: a resume file here
# carries its own rationale log, and that log quotes the posting it answers,
# which is the only hit this check had on the day it was written. So is a
# blockquote, and so is this file, which has to spell the phrases out in order
# to ban them. me/voice.md spells them out too and is not in the scanned set.
set -uo pipefail
cd "$(dirname "$0")/.."

md() { git ls-files -z --cached --others --exclude-standard "$@"; }

fail=0

dashes=$(md '*.md' | xargs -0 grep -nH -- '—' 2>/dev/null |
         grep -v '^AGENTS\.md:\|^CLAUDE\.md:\|^scripts/' || true)
if [ -n "$dashes" ]; then
  echo "$dashes"
  echo "Em dashes. Use a comma, a colon, or a period."
  fail=1
fi

# What an employer actually reads: letters, resumes and the variants cut from
# them. company.md and form-fill.md are working notes and quote freely.
phrases='not just .*, but|passionate|leverage[sd]? the|leveraging|deep dive|deep-dive|I.m excited to|I was drawn to'
# read null-delimited into an array: a path with a space in it must reach grep
# as one argument, the same guard check-citations.sh spells out
deliverables=()
while IFS= read -r -d '' f; do
  case "$f" in
    applications/*/letter*.md|applications/*/resume*.md) deliverables+=("$f") ;;
  esac
done < <(md 'applications/*.md')

if [ ${#deliverables[@]} -gt 0 ]; then
  hits=$(grep -nHEi "$phrases" "${deliverables[@]}" 2>/dev/null |
         grep -v ':[0-9]*:>' | grep -v '"' || true)
  if [ -n "$hits" ]; then
    echo "$hits"
    echo "Banned phrasing in something an employer reads. Say it plainly."
    fail=1
  fi
fi

[ "$fail" -eq 0 ] && echo "voice rules hold"
exit "$fail"
