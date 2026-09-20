#!/usr/bin/env bash
# Fails when something tagged `[ask: Key]` reaches no line in board.md, which
# is the only page the candidate reads. The fact base cannot be allowed a
# private backlog he never sees; tools/questions.py holds the marker's rules.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.questions
