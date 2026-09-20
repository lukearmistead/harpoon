"""Markdown tables, read as rows of cells.

Three files here keep their data in tables a person edits by hand:
source/channels.md carries the catalog and the watchlist, board.md carries the
pipeline. Every reader of those files needs the same two rules, so they live
here once rather than being spelled differently in each caller.

Cells split on an unescaped pipe, because a title regex needs a literal one
for alternation and a markdown table spells that `\\|`. Backticks come off,
because whether a cell is set in code font is typography and not data.
"""

import re

SPLIT = re.compile(r"(?<!\\)\|")


def rows(text):
    """Every table row in the text, as a list of cells.

    A separator row and a header row come back like any other: telling them
    apart is the caller's job, because what makes a row interesting differs
    per table and no rule here would fit all three.
    """
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|"):
            yield [cell.strip().strip("`").replace("\\|", "|")
                   for cell in SPLIT.split(line.strip("|"))]
