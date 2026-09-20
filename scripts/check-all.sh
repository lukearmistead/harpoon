#!/usr/bin/env bash
# Every check this repo has, in one command, because five things nobody runs
# are worth less than one thing that runs itself. `.githooks/pre-commit` calls
# this, so a commit is the thing that runs it.
#
# Each check prints its own failures and this reports which ones failed, rather
# than stopping at the first. A run that says "citations failed" and hides that
# the tests also failed costs a second round trip.
set -uo pipefail
cd "$(dirname "$0")/.."

failed=()

run() {
  local name=$1; shift
  echo "== $name"
  if "$@"; then return 0; fi
  failed+=("$name")
}

run citations ./scripts/check-citations.sh
run "watch rows" ./scripts/check-watch-rows.sh
run "open questions" ./scripts/check-open-questions.sh
run "note indexes" ./scripts/check-notes-index.sh
run voice ./scripts/check-voice.sh
run "criteria length" ./scripts/check-criteria-length.sh

if command -v uv >/dev/null 2>&1; then
  run tests uv run --quiet pytest -q
else
  echo "== tests"
  echo "uv is not installed, so the tests did not run. See the setup skill." >&2
  failed+=("tests (uv missing)")
fi

if [ ${#failed[@]} -eq 0 ]; then
  echo
  echo "all checks passed"
  exit 0
fi

echo
echo "failed: ${failed[*]}"
exit 1
