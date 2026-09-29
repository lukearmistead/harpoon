"""Every company the repo has decided has to say what would bring it back.

    python3 -m tools.source.companyrows

The already-decided gate reads the `## Companies` table in source/channels.md and
asks each row's condition whether this posting is the one. A company the board has
closed with no row there has no condition to ask, so it is shut for good by
accident rather than on purpose, and the only record of why is prose the sweep
cannot read. On 2026-09-27 that was 84 companies, gated by a bolded name in the
rejection log and nothing else.

Three rules, from three different days:

- A closed company, `passed` or `rejected` on board.md, needs a row.
- A name bolded in learn/rejections.md needs one too, until the board or the
  table accounts for it, because that log was the store before the table was.
- A condition has to parse. tools/source/watch.py::meets raises on a term it
  cannot read and the sweep is where that lands, so one cell of prose would end a
  run before it printed anything. A failed commit is the cheaper place.

And one rule about the board rather than the table: no row on it says `watch`. A
row is one company and one seat, so a company worth an eye on with no seat has
nothing to put in its role cell and belongs in the table instead. Twenty-one
moved that way on 2026-09-27.

This file was two, watchrows.py and closedrows.py, one per table, which is what a
Watchlist and a Closed list with the same three fields cost. They merged with the
tables on 2026-09-28.

Names are matched the way the sweep matches them, through contract.norm, so a
company spelled two ways across the two files is still one company here.
"""

import re
import sys

from tools.core import repo, tables
from tools.core.contract import Lead, norm
from tools.source import sweep
from tools.source.sweep import fetched_companies as fetched
from tools.source.watch import meets

ROOT = repo.ROOT
LOG = "learn/rejections.md"
CLOSING = ("rejected", "passed")
INPUTS = ("board.md", "source/channels.md")
BOLD_OPENER = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*", re.M)
SENTENCE_BREAK = re.compile(r"[.,:;]\s")
PROBE = Lead(company="probe", title="Staff ML Engineer", location="Remote",
             band=None, url=None, source="check-company-rows")


def absent_inputs(root):
    """Both files are written per instance, so a fresh clone of the template
    has neither. A check that fails there teaches everyone who clones it to
    ignore the checks."""
    return [path for path in INPUTS if not (root / path).exists()]


def watching_rows(board):
    """Every row still claiming to watch a company itself."""
    return [name for name, status in tables.statuses(board).items()
            if status == "watch"]


def cataloged_names(channels):
    """Every company named in a Catalog or Companies row, as the file spells it.

    A caller that needs to match on something other than contract.norm needs the
    original: slugging a normalized name gives `anglehealth`, which matches no
    directory, and that quietly reported four watched companies as gaps.
    """
    return [cells[0] for cells in
            tables.rows_under(channels, "Catalog", "Companies") if cells[0]]


def cataloged(channels):
    """The same companies, normalized."""
    return {norm(name) for name in cataloged_names(channels)}


def swept_names(log):
    """The companies bolded in learn/rejections.md.

    That log was the store until the gate started asking a condition, and it is
    still the only record of why most of these companies are closed, so a name in
    it is a closed company until the table has its row.

    A bolded opener runs on into prose ("Cresta. Came back 2026-09-11 and is now
    in Working now"), so it is cut at the first sentence break, and what is still
    longer than a name is a sentence about the market rather than a company: four
    entries open that way, one of them "The one place a frontier lab has a
    constrained human workforce is safety".

    Two more shapes are not names either. A clause with a verb in it is a
    sentence short enough to survive the length cut, as "Lumenai is Luminai" did.
    And a parenthetical is one company under two spellings, so "Superhuman
    (Grammarly)" is asked about under the name a job board would return.
    """
    names = {}
    for bold in BOLD_OPENER.findall(log):
        name = SENTENCE_BREAK.split(bold)[0].rstrip(".,:; ")
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()
        if name and len(name.split()) <= 4 and not re.search(r"\bis\b", name):
            names.setdefault(norm(name), name)
    return list(names.values())


def answered(name, known):
    """True when the board or the table already accounts for this company.

    The log writes a company's full name where the other two files write the
    short one, so `Apella Health` in the log is the `Apella` row on the board and
    the `apella` row in the table. The match walks whole words from the left
    rather than characters, because a word boundary is what makes the shorter
    spelling the same company: `Apella` plus `Health` is one, while two companies
    that merely start with the same letters are not.
    """
    words = name.split()
    return any(norm(" ".join(words[:n])) in known
               for n in range(1, len(words) + 1))


def unrowed(board, log, companies, known_rows=frozenset()):
    """Every closed company with no row in the table, named as the board names it.

    A status of `rejected` or `passed` is the first half. The second is the
    bolded names in the log that have no board row at all, because a company with
    one is answered by the first half either way: a status that closes it is
    already listed, and any other status says it came back.

    A company with a Catalog or Companies row is not unrowed either, whatever the
    log still says about it. That is what the board row cannot answer on its own:
    Apella is boarded as `Apella` and bolded as "Apella Health", EliseAI has a
    table row and no board row at all, and Verily is a catalog row blocked on an
    unwritten fetcher whose board row reads `Verily Lightpath`.
    """
    board_statuses = tables.statuses(board)
    known = {norm(name) for name in board_statuses} | known_rows
    problems = [f"board.md: {name} is `{status}` with no row in "
                "source/channels.md's `## Companies` table"
                for name, status in board_statuses.items()
                if status in CLOSING and norm(name) not in companies]
    return problems + [
        f"{LOG} names {name}, which has no row in source/channels.md's "
        "`## Companies` table"
        for name in swept_names(log)
        if norm(name) not in companies and not answered(name, known)]


def unreadable(channels):
    """Every condition the watch language cannot read.

    Empty and `never` are read by the gate itself and never reach meets(), and
    everything else has to parse there. A bad regex raises re.error rather than
    ValueError, which is not one of its subclasses, so a cell reading
    `title ~ staff(` would crash a sweep just as surely as prose would.
    """
    problems = []
    for name, condition in sweep.company_rows(channels):
        if condition in ("", "never"):
            continue
        try:
            meets(PROBE, condition)
        except (ValueError, re.error) as reason:
            problems.append(
                f"source/channels.md: {name}'s condition reads {condition!r}, "
                f"which the sweep cannot read ({reason})")
    return problems


def check(root=ROOT):
    """The four rules, in the order a person would read them."""
    if absent_inputs(root):
        return []
    channels = (root / "source/channels.md").read_text()
    board = (root / "board.md").read_text()
    log = (root / LOG).read_text() if (root / LOG).exists() else ""
    companies = {norm(name) for name, _ in sweep.company_rows(channels)}
    return [f"board.md: {name} is `watch`, and a company with no seat is a row "
            "in source/channels.md's `## Companies` table rather than one here"
            for name in watching_rows(board)] \
        + unrowed(board, log, companies, cataloged(channels)) \
        + unreadable(channels)


def main():
    skipped = absent_inputs(ROOT)
    if skipped:
        print(f"skipped: no {' or '.join(skipped)} in this instance yet")
        return
    problems = check(ROOT)
    for problem in problems:
        print(problem)
    if problems:
        sys.exit(f"\n{len(problems)} problem(s). Give each company a row in "
                 "source/channels.md's `## Companies` table: the display name, "
                 "the endpoint if anything fetches it, what would make a posting "
                 "there matter (`never` when the thesis closed it, `band > 200` "
                 "or `title ~ staff\\|principal` when a seat would, empty when "
                 "any posting would), and one sentence naming the criteria "
                 "bullet it failed.")


if __name__ == "__main__":
    main()
