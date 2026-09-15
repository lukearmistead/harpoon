#!/usr/bin/env bash
# Every path this repo cites must exist, whether it is backticked prose or a
# markdown link. A rule that points at a missing file is a rule that silently
# never runs.
#
# Imported source material is deliberately gitignored, so it is absent from a
# fresh clone by design. Derived work product inside an ignored directory is
# re-included in .gitignore precisely so this check still covers it. Those citations get counted and reported, and they do
# not fail the check. A missing path that git does not ignore is a real dead
# citation, and it does.
set -uo pipefail
cd "$(dirname "$0")"

files() { git ls-files --cached --others --exclude-standard '*.md'; }

cited=$(
  {
    # `me/experience.md`, `applications/`, `pipeline.md`
    files | xargs grep -noE '`([A-Za-z0-9_.-]+(/[A-Za-z0-9_. -]+)+/?|[A-Za-z0-9_.-]+\.(md|sh))`' | tr -d '`'
    # [file](applications/acme-health/company.md), skipping URLs and anchors
    files | xargs grep -noE '\]\([A-Za-z0-9_.][A-Za-z0-9_./ -]*\)' | tr -d ')' | sed 's/](//'
  } | sort -u
)

# A naming convention is not a citation. `YYYY-MM-DD-topic.md` names the shape a
# file should take, and no file of that literal name should ever exist. Skip
# anything carrying a placeholder rather than a path.
cited=$(grep -vE 'YYYY|MM-DD|<[^>]+>|\{[^}]+\}' <<< "$cited")

absent=$(
  while IFS=: read -r file line path; do
    [ -n "${path:-}" ] || continue
    [ -e "$path" ] || printf '%s:%s:%s\n' "$file" "$line" "$path"
  done <<< "$cited"
)

[ -z "$absent" ] && exit 0

# Ask git which of the absent paths are ignored on purpose.
ignored=$(cut -d: -f3- <<< "$absent" | sort -u | git check-ignore --stdin || true)

missing=0
local_only=0
while IFS=: read -r file line path; do
  [ -n "${path:-}" ] || continue
  if [ -n "$ignored" ] && grep -qxF "$path" <<< "$ignored"; then
    local_only=$((local_only + 1))
  else
    echo "$file:$line: missing $path"
    missing=$((missing + 1))
  fi
done <<< "$absent"

if [ "$local_only" -gt 0 ]; then
  echo "$local_only citation(s) point at local-only imported material. Absent from a fresh clone by design."
fi

[ "$missing" -eq 0 ] && exit 0
echo
echo "$missing dead citation(s). Fix the path or drop the claim."
exit 1
