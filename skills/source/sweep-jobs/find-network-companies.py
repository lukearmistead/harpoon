"""Rank the companies where LinkedIn connections currently work.

Connections.csv stores each connection's current employer, so its Company
column is a standing list of companies where a warm path already exists.
Job boards are indexed by investor or by ATS and produce no warm paths at
all; this reads the network, which produces nothing else. It is the other
direction through the file find-former-colleagues.py reads.

Run from the repo root:

    python3 skills/source/sweep-jobs/find-network-companies.py > /tmp/net.txt

Companies board.md has already decided are dropped, so the report is what
is new. Review it by hand and resolve the ones that look on-thesis with
`python3 -m tools.sweep probe <company>`, which finds the ATS board and
prints its open seats.

Nothing here is a lead. A connection at a company says a door exists, not
that a seat does, and the export carries no location, so the geography hard
line cannot be applied until the probe step. Both are why this stays a hands
lane: the report is an argument for who to ask, not a list to work through.
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, ".")  # this runs from the repo root, where tools/ sits
from tools.sweep import decided_names, norm  # noqa: E402

CONNECTIONS_CSV = "profile/network/export/Connections.csv"

# Values in the Company column that name no employer.
NOT_EMPLOYERS = {"self-employed", "freelance", "retired", "unemployed",
                 "student", "none", "n/a", "independent consultant"}


def read_connections():
    lines = open(CONNECTIONS_CSV).read().split("\n")
    header = next(i for i, l in enumerate(lines)
                  if l.startswith("First Name,Last Name,URL"))
    return list(csv.DictReader(lines[header:]))


def by_company(connections):
    """Group connections under their current employer."""
    companies = defaultdict(list)
    for person in connections:
        company = (person["Company"] or "").strip()
        if company and company.lower() not in NOT_EMPLOYERS:
            companies[company].append(person)
    return companies


def main():
    companies = by_company(read_connections())
    decided = decided_names()
    new = {c: people for c, people in companies.items() if norm(c) not in decided}

    print(f"{len(companies)} companies in the export, "
          f"{len(companies) - len(new)} already decided in board.md, "
          f"{len(new)} to review. Most connections first.\n")
    for company, people in sorted(new.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"{company} ({len(people)})")
        for person in sorted(people, key=lambda p: p["Last Name"]):
            title = (person["Position"] or "").strip()
            print(f"    {person['First Name']} {person['Last Name']} | {title}")


if __name__ == "__main__":
    main()
