#!/usr/bin/env bash
# `profile/meetings/` and `profile/interviews/` each carry an index.md so an agent can
# see what is in the directory without opening every file in it. This asserts
# the index is current and that every note in it has a summary written by a
# person, which is the one line no generator can supply.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.notes --check
