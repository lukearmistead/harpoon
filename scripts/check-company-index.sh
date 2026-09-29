#!/usr/bin/env bash
# `apply/index.md` carries one entry per company file, every line lifted
# verbatim from the file it names, so a ranking costs one read instead of
# forty-eight. This fails when it is stale, which is whenever a company file
# changes and nobody re-ran the generator.
#
# It also fails a repo where the index has never been written, because an index
# that is merely absent looks the same as one that is current.
set -uo pipefail
cd "$(dirname "$0")/.."

exec python3 -m tools.apply.companies --check
