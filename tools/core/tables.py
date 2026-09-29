"""Markdown tables, read as rows of cells.

Three files here keep their data in tables a person edits by hand:
source/channels.md carries the catalog, the watchlist and the closed
companies, board.md carries the pipeline. Every reader of those files needs the
same two rules, so they live here once rather than being spelled differently in
each caller.

Cells split on an unescaped pipe, because a title regex needs a literal one
for alternation and a markdown table spells that `\\|`. Backticks come off,
because whether a cell is set in code font is typography and not data.
"""

import re

SPLIT = re.compile(r"(?<!\\)\|")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def statuses(board):
    """Every company on board.md against its status: the first two cells of
    every row, the first stripped of its markdown link.

    It lives here rather than beside one of its readers because it has three,
    the rejudgment worklist, the company index and the row checks, and the one
    that held it could not be imported by the others without a cycle.
    """
    return {unlink(cells[0]): cells[1]
            for cells in rows(board) if len(cells) >= 2}


def unlink(cell):
    """A cell's text, with any markdown link reduced to the label it shows.

    A company's first cell becomes `[Acme](apply/acme/company.md)` the moment it
    has a file, and three readers were each handling that separately: two with
    their own pattern and one not at all, which fed
    `abbycareapplyabbycarecompanymd` to the already-decided gate.
    """
    return LINK.sub(r"\1", cell).strip()


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


def body(text, heading):
    """What is written under one `## heading`, and "" when there is none.

    An absent heading gives nothing back rather than the whole file, because a
    reader of `## Closed` that fell back that way would read the catalog as
    closed companies and gate every channel in it. The match is exact: these
    headings come from the schema, not from whoever edited the file that week.

    A `###` line stays inside the section it sits under, because the space
    after the two hashes is part of the match, and that is what lets a reader
    of a section with dated blocks under it see all of them.
    """
    blocks = re.split(r"^## (.+?)\s*$", text, flags=re.M)[1:]
    return dict(zip(blocks[::2], blocks[1::2])).get(heading, "")


def rows_under(text, *headings):
    """Every table row under the named headings, and nowhere else.

    Cell count used to tell source/channels.md's tables apart, and `## Closed`
    broke that: its second cell holds a comeback condition, which is the shape
    of a watchlist row's third. So a reader that wants one table says which
    heading it belongs to.
    """
    for heading in headings:
        yield from rows(body(text, heading))
