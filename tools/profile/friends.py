"""Rank the network by how likely each connection is a friend.

    python3 -m tools.profile.friends              every connection, best first
    python3 -m tools.profile.friends --batch 0    rows 1 to 15; --batch 1 the next 15
    python3 -m tools.profile.friends --batch 0 --size 50    fifty a batch instead

Recall is the hard part of naming friends and recognition is easy, so the
pick-friends skill shows this ranking fifteen rows at a time and the candidate
strikes the names that are not friends rather than producing names from
memory. Each row is a markdown table row ready to paste under friends.md's
`| friend | how | connected on | profile |` header, with the how column
already guessed from the strongest signal, so it is corrected, not filled.

The signals are what the export already carries: the roster files beside
it, who works at one of the candidate's own employers, and who the
candidate has recommended, endorsed or messaged, or been recommended,
endorsed or messaged by. What the candidate did toward a person outranks
what the person did toward them, and age earns nothing: the first live run
(2026-09-21) kept 8 to 39% of connections from the candidate's first four
working years and 31 to 77% after, so ties go newest first. Seven CSVs feed
the signals, Connections.csv, Positions.csv, messages.csv, the two
Recommendations files and the two Endorsement files, with the rosters read
from roster-*.md. Names already in friends.md are left out, so each run
shows only what is still undecided.
"""

import argparse
import csv
import datetime
import re
import sys
from typing import NamedTuple

from tools.core import tables
from tools.core.contract import norm
from tools.core.repo import ROOT

NETWORK = ROOT / "profile/network"
EXPORT = ROOT / "profile/network/export"
FRIENDS = ROOT / "profile/network/friends.md"
YEAR = re.compile(r"\d{4}")
BATCH = 15


class Row(NamedTuple):
    name: str
    score: int
    how: str
    connected: datetime.date
    url: str


def read_connections():
    """Connections.csv opens with a three-line preamble, so the header row is
    found by content rather than assumed to be line one."""
    path = EXPORT / "Connections.csv"
    if not path.exists():
        sys.exit(f"no {path.relative_to(ROOT)}; unzip the LinkedIn export there first")
    lines = path.read_text(encoding="utf-8-sig").split("\n")
    header = next(i for i, line in enumerate(lines)
                  if line.startswith("First Name,Last Name,URL"))
    return list(csv.DictReader(lines[header:]))


def read_rows(csv_name):
    """Any other export CSV: header on line one, or nothing when the export
    lacks the file, which LinkedIn omits when there is nothing to put in it."""
    path = EXPORT / csv_name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def person_key(row):
    return norm(row["First Name"] + row["Last Name"])


def capped(counts, cap):
    return {key: (min(n, cap), "") for key, n in counts.items()}


def roster_members():
    """Everyone named in the first column of any roster table, with the how
    that names the roster's company and file."""
    members = {}
    for path in sorted(NETWORK.glob("roster-*.md")):
        company = path.stem.removeprefix("roster-").replace("-", " ").title()
        for cells in tables.rows(path.read_text()):
            if cells[0] and cells[0] != "person" and not cells[0].startswith("-"):
                members[norm(cells[0])] = f"{company} colleague, per {path.name}"
    return members


def roster(ctx):
    return {key: (3, how) for key, how in ctx["rosters"].items()}


def conversations(ctx):
    """One point per conversation with a connection, three at most.

    Both parties of every message are read, since the candidate starts some
    threads. A name absent from Connections.csv is dropped, which is what
    keeps recruiters out without a keyword list.
    """
    known = {person_key(row) for row in ctx["connections"]}
    threads = {}
    for message in read_rows("messages.csv"):
        for party in [message["FROM"], *message["TO"].split(",")]:
            if norm(party) in known:
                threads.setdefault(norm(party), set()).add(message["CONVERSATION ID"])
    return capped({key: len(ids) for key, ids in threads.items()}, 3)


def recommendations(ctx):
    """Three points for a recommendation either way, worded by its direction."""
    hits = {}
    for csv_name, wording in (("Recommendations_Received.csv", "recommended you"),
                              ("Recommendations_Given.csv", "you recommended")):
        for row in read_rows(csv_name):
            year = YEAR.search(row["Creation Date"])
            how = f"{wording}, {year.group()}" if year else wording
            hits.setdefault(person_key(row), (3, how))
    return hits


def employer(ctx):
    """Three points for working now at a company in Positions.csv, past or
    present: a colleague the candidate never wrote a roster line for."""
    mine = {norm(p["Company Name"]) for p in read_rows("Positions.csv")}
    return {person_key(row): (3, f"{row['Company'].strip()} colleague")
            for row in ctx["connections"] if norm(row["Company"]) in mine}


def endorsements(ctx):
    """Two points for a skill the candidate endorsed, one for one they were
    endorsed for; several endorsements of one person count once."""
    hits = {}
    for csv_name, party, points, wording in (
            ("Endorsement_Given_Info.csv", "Endorsee", 2, "you endorsed"),
            ("Endorsement_Received_Info.csv", "Endorser", 1, "endorsed you")):
        for row in read_rows(csv_name):
            key = norm(row[f"{party} First Name"] + row[f"{party} Last Name"])
            hits.setdefault(key, (points, f"{wording}, {row['Endorsement Date'][:4]}"))
    return hits


# Each signal reads the loaded export once and returns {person key: (points,
# how)}; a how of "" means the signal has no wording of its own. Order is
# the tie-break between equally strong hows.
SIGNALS = (roster, recommendations, employer, endorsements, conversations)


def connected_on(row):
    """The connection date, or the far past for a blank one, so it sorts last."""
    text = (row.get("Connected On") or "").strip()
    if not text:
        return datetime.date.min
    return datetime.datetime.strptime(text, "%d %b %Y").date()


def shown(connected):
    """The date as printed: ISO, or nothing for the blank-date sentinel."""
    return "" if connected == datetime.date.min else connected.isoformat()


def default_how(row, connected):
    company = row["Company"].strip()
    year = shown(connected)[:4]
    return f"{company}, connected {year}" if year else company


def tally(row, signals):
    """One connection's score, and the how of its strongest signal."""
    hits = [s.get(person_key(row), (0, "")) for s in signals]
    connected = connected_on(row)
    how = max(hits, key=lambda hit: hit[0])[1] if hits else ""
    how = how or default_how(row, connected)
    return Row(f"{row['First Name']} {row['Last Name']}",
               sum(points for points, _ in hits), how, connected, row["URL"])


def already_friends():
    """First-column names in friends.md, plus the bullet list under its
    Struck heading, which is a list rather than a table so that
    tools.profile.histories never reads a struck name as a friend. The file may not
    exist yet."""
    if not FRIENDS.exists():
        return set()
    text = FRIENDS.read_text()
    names = {norm(cells[0]) for cells in tables.rows(text)}
    struck = {norm(line[2:]) for line in text.splitlines()
              if line.startswith("- ")}
    return (names | struck) - {"", norm("friend")}


def rank():
    """Every connection not yet in friends.md, highest score first, newest
    connection first on ties. A nameless row, which LinkedIn exports for a
    connection who hides their data, is skipped like a picked one."""
    picked = already_friends() | {""}
    connections = [row for row in read_connections()
                   if person_key(row) not in picked]
    ctx = {"rosters": roster_members(), "connections": connections}
    signals = [signal(ctx) for signal in SIGNALS]
    rows = [tally(row, signals) for row in connections]
    return sorted(rows, key=lambda r: (r.score, r.connected), reverse=True)


def line(row):
    cells = (row.name, row.how, shown(row.connected), row.url)
    return "| " + " | ".join(c.replace("|", "/") for c in cells) + " |"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--batch", type=int, metavar="N",
                        help="print only the Nth batch, counting from zero")
    parser.add_argument("--size", type=int, default=BATCH, metavar="N",
                        help=f"rows per batch, {BATCH} unless said otherwise")
    args = parser.parse_args(argv)
    rows = rank()
    if args.batch is not None:
        rows = rows[args.size * args.batch:args.size * (args.batch + 1)]
    for row in rows:
        print(line(row))


if __name__ == "__main__":
    main()
