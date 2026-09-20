#!/usr/bin/env bash
# Fails when a `watch` row on board.md has no row in source/channels.md, which
# is a company nobody is watching and nobody is working: the one status that
# can rot without anyone noticing. tools/watchrows.py holds the matching rules.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.watchrows
