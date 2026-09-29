"""The count the candidate never keeps: who is read, and what the reads found.

    python3 -m tools.profile.histories next [--size 15]   the sitting's batch
    python3 -m tools.profile.histories employers          what the sweep should probe

`next` prints the friends in profile/network/friends.md that have no section
in profile/network/histories.md yet, in the file's order, and refuses when a
section is already dated today: one sitting a day is the rule gather-histories
keeps, and this is where it is kept. `employers` lists every company across
every history that board.md and `## Companies` in source/channels.md have not
already decided, with which friends were
there and when, most friends first; each name is an argument for
`python3 -m tools.source.sweep probe`, and nothing here judges a company.

Both files are this repo's own markdown, so parsing them is parsing a format
the repo controls. A missing histories.md means nobody has been read yet.
"""

import datetime
import re
import sys
from typing import NamedTuple

from tools.core import tables
from tools.core.repo import ROOT
from tools.source.sweep import company_rows, decided_names, norm

FRIENDS = ROOT / "profile/network/friends.md"
HISTORIES = ROOT / "profile/network/histories.md"

HEADER = re.compile(r"^(.+?), read (\d{4}-\d{2}-\d{2})")


class Section(NamedTuple):
    name: str
    read: str
    stints: list  # rows of (company, title, from, to)


def data_rows(text):
    """Table rows minus the header and the separator, which tables.rows
    hands back like any other."""
    for cells in tables.rows(text):
        first = cells[0].lower()
        if first and first not in ("friend", "company") and not set(first) <= set("-:"):
            yield cells


def friends():
    """Each friend as (name, profile), in the order the candidate keeps them.
    A blank profile cell is a friend with no page to load, so they are left out."""
    text = FRIENDS.read_text() if FRIENDS.exists() else ""
    return [(cells[0], cells[3]) for cells in data_rows(text)
            if len(cells) >= 4 and cells[3]]


def sections():
    """One Section per friend read; none when nobody has been."""
    text = HISTORIES.read_text() if HISTORIES.exists() else ""
    found = []
    for piece in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = piece.partition("\n")
        match = HEADER.match(head.strip())
        if match:
            found.append(Section(match[1], match[2],
                                 [c[:4] for c in data_rows(body) if len(c) >= 4]))
    return found


def next_batch(size, today):
    """The friends still unread, capped; refused outright if today already
    had a sitting, because the limit is the copilot's to keep, not the
    candidate's to remember."""
    read = sections()
    for s in read:
        if s.read == today:
            sys.exit(f"a sitting already happened today ({s.name}, read {s.read}); "
                     "one a day")
    done = {s.name for s in read}
    return [f for f in friends() if f[0] not in done][:size]


def employers():
    """Undecided companies, keyed by normalized name so two spellings of one
    employer are one row, each with the friends who were there and when.

    Closed companies come from `## Companies` as well as from the board, because
    that table is where a company-grain verdict lives now. Reading only the
    board would put a company closed on the expertise test back on this
    worklist as though nobody had ever ruled on it.
    """
    stints = {}
    for s in sections():
        for company, _, start, end in s.stints:
            row = stints.setdefault(norm(company), (company, []))
            row[1].append(f"{s.name} ({start} to {end})")
    decided = decided_names() | set(
        dict(company_rows((ROOT / "source/channels.md").read_text())))
    return sorted((v for k, v in stints.items() if k not in decided),
                  key=lambda kv: (-len(kv[1]), kv[0]))


def main(argv, today=None):
    today = today or datetime.date.today().isoformat()
    command = argv[0] if argv else ""
    if command == "next":
        size = int(argv[argv.index("--size") + 1]) if "--size" in argv else 15
        for name, profile in next_batch(size, today):
            print(name, profile)
    elif command == "employers":
        for company, friends_there in employers():
            print(f"| {company} | {'; '.join(friends_there)} |")
    else:
        sys.exit("usage: python3 -m tools.profile.histories next [--size N] "
                 "| employers")


if __name__ == "__main__":
    main(sys.argv[1:])
