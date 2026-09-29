#!/usr/bin/env bash
# Fails when board.md carries a heading below its table. The board is the seats
# the candidate is chasing; anything under the table is bookkeeping written for
# an agent on the one page a person reads. Four such sections grew there before
# 2026-09-28 and held 26,795 characters, 29 companies' only record among them.
# When something has no home, name the file it belongs in and write it there:
# a company file in apply/, a row in source/channels.md, a lesson in learn/.
set -uo pipefail
cd "$(dirname "$0")/.."

[ -f board.md ] || { echo "skipped: no board.md in this instance yet"; exit 0; }

after=$(awk '/^\| /{seen=1; next} seen && /^#+ /{print FNR": "$0}' board.md)
[ -z "$after" ] && exit 0

echo "board.md carries a heading below its table:"
echo "$after"
exit 1
