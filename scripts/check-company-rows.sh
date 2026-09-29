#!/usr/bin/env bash
# Fails when a company the board has closed has no row in source/channels.md's
# `## Companies` table, when a name bolded in learn/rejections.md has none, when
# a row's condition says something the watch language cannot read, or when a
# board row's status is `watch`, which is a company with no seat and so belongs
# in that table rather than on the board. The first is a company shut for good by
# accident; the third would raise inside a sweep and end the run.
# tools/source/companyrows.py holds the matching rules.
#
# It lives here beside the other checks rather than only as a python command,
# because the thing that runs all of them runs this directory. It was two
# scripts, one per table, until the tables merged on 2026-09-28.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.source.companyrows
