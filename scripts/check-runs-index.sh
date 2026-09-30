#!/usr/bin/env bash
# `learn/runs/index.md` carries one line per run directory, so asking where the
# grading is costs one read instead of one per run. This fails when it is
# stale, which is whenever a run is written or a row is graded and nobody
# re-ran the generator.
#
# It also fails a repo where the index has never been written, because an index
# that is merely absent looks the same as one that is current. An instance with
# no runs yet is skipped instead: the template ships the directory empty.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.learn.runs --check
