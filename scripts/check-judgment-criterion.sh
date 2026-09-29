#!/usr/bin/env bash
# Fails when a row in the newest learn/runs/*/judgment.csv decided something and
# names no criterion, which is a verdict nobody can revisit when the bullet it
# rested on moves. tools/learn/judgmentcriterion.py holds the rules, including why
# older runs are left alone.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.learn.judgmentcriterion
