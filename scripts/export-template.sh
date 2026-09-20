#!/bin/bash
# The one deliberate door from a private search repo to the public template.
#
#   ./export-template.sh "commit message for the template"
#
# Copies the template files (allowlist below, personal paths never named) into
# a fresh clone of the template repo, shows what changed, commits, pushes.
# The template's push URL stays DISABLED in this repo's `engine` remote so
# nothing can leave by accident; this script reads the fetch URL instead.
set -euo pipefail
cd "$(dirname "$0")/.."

# AGENTS.md is the rulebook and CLAUDE.md is a symlink to it; skills/ holds the
# procedures and both .agents/skills and .claude/skills are symlinks to it, one
# per tool that looks for them. All three symlinks are on the list and all are
# relative, so they resolve inside the template exactly as they do here. rsync
# copies a symlink as a symlink: no -L anywhere.
#
# .claude/settings.json is named on its own rather than the whole .claude
# directory, because .claude/settings.local.json is the per-machine override
# and exporting one person's would hand everybody their local answers.
TEMPLATE_PATHS=(AGENTS.md CLAUDE.md README.md scripts .githooks pyproject.toml
              uv.lock .gitignore skills .agents/skills .claude/skills
              .claude/settings.json tools tests
              learn/runs/.gitkeep)

msg=${1:?usage: ./export-template.sh "commit message"}
url=$(git remote get-url engine)

if [ -n "$(git status --porcelain -- "${TEMPLATE_PATHS[@]}")" ]; then
  echo "template files have uncommitted changes; commit privately first" >&2
  exit 1
fi

tmp=$(mktemp -d)
git clone --quiet --depth 1 "$url" "$tmp"
# learn/runs/.gitkeep is the only learn path on the allowlist, so --delete prunes
# every sibling from the template: that is the point. A run directory names
# real companies and must never leave, and grades.csv was retired on
# 2026-09-16, so the template's seeded copy gets pruned on the next export.
#
# One rsync call, never one per path. A path copied on its own makes its parent
# the whole transfer, and --delete then prunes every sibling, including the ones
# further down this same allowlist: copying .claude/settings.json by itself
# deleted the .claude/skills symlink beside it, which is the symlink that makes
# the skills visible to the tool most people clone this with. Listing every
# source in one call puts them in one file list, so siblings survive each other.
rsync -aR --delete --exclude __pycache__ --exclude .pytest_cache \
      "${TEMPLATE_PATHS[@]}" "$tmp/"

git -C "$tmp" add -A
if git -C "$tmp" diff --cached --name-only |
   grep -qE '^(profile/|source/|apply/|board\.md|learn/lessons\.md|learn/runs/[0-9])'; then
  echo "refusing: a personal path reached the staging area" >&2
  exit 1
fi
if git -C "$tmp" diff --cached --quiet; then
  echo "template already matches; nothing to export"
  exit 0
fi

git -C "$tmp" status --short
git -C "$tmp" commit --quiet -m "$msg"
git -C "$tmp" push --quiet origin HEAD
echo "exported to $url"
