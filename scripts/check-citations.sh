#!/usr/bin/env bash
# Fails when a path this repo cites does not exist, whether it is backticked
# prose or a markdown link. A rule that points at a missing file is a rule that
# silently never runs. Imported material and per-instance files are counted and
# reported rather than failed; tools/citations.py says why.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.citations
