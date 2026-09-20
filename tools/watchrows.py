"""A `watch` row on the board has to name something that is actually watching.

    python3 -m tools.watchrows

The row delegates the company to the sweep, and the thing doing the watching
is that company's row in source/channels.md. A `watch` with no channel row is a
company nobody is watching and nobody is working, which is the one status that
can rot without anyone noticing. Six rows sat that way on 2026-09-16, which is
why this runs instead of being remembered.

Names are matched the way the sweep matches them, through contract.norm, so a
company spelled two ways across the two files is still one company here.
"""

import re
import sys

from tools import repo, tables
from tools.contract import norm

ROOT = repo.ROOT
LINK = re.compile(r"^\[|\]\([^)]*\)")
INPUTS = ("board.md", "source/channels.md")


def absent_inputs(root):
    """Both files are written per instance, so a fresh clone of the template
    has neither. A check that fails there teaches everyone who clones it to
    ignore the checks."""
    return [path for path in INPUTS if not (root / path).exists()]


def watched(board):
    """Every company the board hands to the sweep.

    Column one is the company, stripped of any markdown link, and column two
    is its status.
    """
    return [LINK.sub("", cells[0]).strip() for cells in tables.rows(board)
            if len(cells) >= 2 and cells[1] == "watch"]


def cataloged(channels):
    """Every company named in the first column of a channel row, whether the
    watching is a fetcher or a person opening the page by hand."""
    return {norm(cells[0]) for cells in tables.rows(channels)}


def check(root=ROOT):
    """Every `watch` row with nothing behind it.

    A merged row names two companies as "A / B": a channel on either half is a
    real watcher on that half, and the row's own cell says which is blind.
    """
    if absent_inputs(root):
        return []
    channels = cataloged((root / "source/channels.md").read_text())
    return [f"board.md: {name} is `watch` with no row in source/channels.md"
            for name in watched((root / "board.md").read_text())
            if not any(norm(half) in channels for half in name.split("/"))]


def main():
    skipped = absent_inputs(ROOT)
    if skipped:
        print(f"skipped: no {' or '.join(skipped)} in this instance yet")
        return
    problems = check(ROOT)
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(f"\n{len(problems)} unwatched `watch` row(s). Catalog the "
                 "board, add it to Watched by hand, or make the row a `lead`.")


if __name__ == "__main__":
    main()
