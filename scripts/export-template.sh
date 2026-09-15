#!/bin/bash
# The one deliberate door from a private search repo to the public template.
#
#   ./export-template.sh "commit message for the template"
#
# Copies the engine files (allowlist below, personal paths never named) into
# a fresh clone of the template repo, shows what changed, commits, pushes.
# The template's push URL stays DISABLED in this repo's `engine` remote so
# nothing can leave by accident; this script reads the fetch URL instead.
set -euo pipefail
cd "$(dirname "$0")/.."

ENGINE_PATHS=(CLAUDE.md README.md scripts pyproject.toml uv.lock .gitignore
              .claude/skills harpoon tests evals/.gitkeep)

msg=${1:?usage: ./export-template.sh "commit message"}
url=$(git remote get-url engine)

if [ -n "$(git status --porcelain -- "${ENGINE_PATHS[@]}")" ]; then
  echo "engine files have uncommitted changes; commit privately first" >&2
  exit 1
fi

tmp=$(mktemp -d)
git clone --quiet --depth 1 "$url" "$tmp"
for p in "${ENGINE_PATHS[@]}"; do
  rsync -aR --delete --exclude __pycache__ --exclude .pytest_cache "$p" "$tmp/"
done

git -C "$tmp" add -A
if git -C "$tmp" diff --cached --name-only | grep -qE '^(me/|applications/|pipeline\.md|evals\.md)'; then
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
