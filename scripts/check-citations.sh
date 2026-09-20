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
cd "$(dirname "$0")/.."

# Seven paths are created per instance and deliberately never exported: they carry
# the candidate's own content, so the public template ships the rules that name
# them without the files themselves. The setup skill creates all seven in a fresh
# instance. They are reported like local-only material rather than failing,
# because a template whose own checks fail teaches everyone who clones it to
# ignore them. Adding a template citation to one of these means adding it here
# and to the setup skill in the same turn: that has now been the bug twice.
PER_INSTANCE="evals/LEARNINGS.md me/voice.md me/positioning.md
me/meetings/index.md me/interviews/index.md me/experience/index.md
me/network/index.md"

# -z + xargs -0: a tracked file whose own path contains spaces must reach
# grep as one argument, not two bogus ones.
# A file deleted but not yet staged is still in the index, and grepping it
# prints an error for every citation check that follows. Only what exists.
files() {
  git ls-files -z --cached --others --exclude-standard '*.md' |
    while IFS= read -r -d '' f; do [ -f "$f" ] && printf '%s\0' "$f"; done
}

cited=$(
  {
    # `me/experience.md`, `applications/`, `pipeline.md`
    files | xargs -0 grep -noE '`([A-Za-z0-9_.-]+(/[A-Za-z0-9_. -]+)+/?|[A-Za-z0-9_.-]+\.(md|sh))`' | tr -d '`'
    # [file](applications/acme-health/company.md), skipping URLs and anchors
    files | xargs -0 grep -noE '\]\([A-Za-z0-9_.][A-Za-z0-9_./ -]*\)' | tr -d ')' | sed 's/](//'
  } | sort -u
)

# A naming convention is not a citation. `YYYY-MM-DD-topic.md` names the shape a
# file should take, and no file of that literal name should ever exist. Skip
# anything carrying a placeholder rather than a path.
cited=$(grep -vE 'YYYY|MM-DD|<[^>]+>|\{[^}]+\}' <<< "$cited")

# A markdown link resolves against the file that carries it, not against the
# repo root, so both are tried. me/meetings/index.md links a sibling note by
# bare filename, which is right for whoever opens it and invisible from here.
absent=$(
  while IFS=: read -r file line path; do
    [ -n "${path:-}" ] || continue
    [ -e "$path" ] || [ -e "$(dirname "$file")/$path" ] ||
      printf '%s:%s:%s\n' "$file" "$line" "$path"
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
  elif grep -qw -- "$path" <<< "$PER_INSTANCE"; then
    local_only=$((local_only + 1))
  else
    echo "$file:$line: missing $path"
    missing=$((missing + 1))
  fi
done <<< "$absent"

if [ "$local_only" -gt 0 ]; then
  echo "$local_only citation(s) point at imported material or at a file created per instance. Absent from a fresh clone by design."
fi

# The resume's `## What backs each bullet` map names sections of the fact base
# rather than paths, so the loop above cannot see it. Every drafting skill now
# reaches me/experience.md through that map, which makes a stale entry a bullet
# with nothing behind it. Absent in a fresh clone, so this no-ops there.
if [ -f me/resume.md ] && [ -f me/experience.md ] &&
   grep -q '^## What backs each bullet' me/resume.md; then
  while IFS= read -r section; do
    grep -qxF "$section" me/experience.md && continue
    echo "me/resume.md: the bullet map names $section, which me/experience.md does not have"
    missing=$((missing + 1))
  done < <(sed -n '/^## What backs each bullet/,$p' me/resume.md |
           grep -oE '`## [^`]+`' | tr -d '`' | sort -u)
fi

[ "$missing" -eq 0 ] && exit 0
echo
echo "$missing dead citation(s). Fix the path or drop the claim."
exit 1
