"""Verdicts a criteria edit invalidated, and verdicts that were never valid.

    python3 -m tools.source.sweep rejudge

A rejection is permanent in practice and profile/criteria.md is not. Between
2026-09-20 and 2026-09-25 that file was edited four times and two of those edits
reversed a rule, and no verdict moved, because the reason a verdict gives is
prose and nothing reads it back. The `criterion` column is that reason in
values a query can group on, and this is the query.

Three sections, and it decides nothing in any of them. A verdict is the
candidate's or the copilot's in a turn they can read, and a rule that flipped
rows unattended would put companies on the board nobody reasoned about, which is
the problem this exists to fix rather than a fix for it.

Every section carries the same bound and prints it, because an unbounded
worklist is the failure of the digest it replaces: nothing is worth re-reading
unless nobody is working it, it has a posting open today, and that posting could
pay. The thesis line comes from the criteria file rather than from a list here.
A bullet under `## Role` is about what the candidate is for, so failing it is not
a fact that changes next quarter, while every other bullet is about a company or
a posting on a given day and comes back. That is the line board.md's verdict
grammar already draws by hand.
"""

import csv
import json
import re
import subprocess

from tools.core import repo, tables
from tools.core.contract import norm
from tools.source.watch import band_top

ROOT = repo.ROOT
RUNS = "learn/runs"
CLOSED_STATUSES = ("rejected", "passed")
# Only a decision that shut a company is worth a second look. A near miss is
# already an invitation to look again, so listing one would be noise, and a
# Strong standing alone is exactly what a near miss records.
CLOSING = ("reject", "rejected", "pass", "passed")
SURVIVED = ("kept", "watch-criterion", "already-decided")


def criteria_commit(root):
    """The commit that last touched this repo's criteria file, or None.

    `evals.revision()` answers the same question about the process's own tree,
    because its job is to stamp a run as that run is written. This one asks
    about a root handed in, so a check can read one repo while running in
    another, which is what every test here does.
    """
    try:
        found = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", "profile/criteria.md"],
            cwd=root, capture_output=True, text=True, check=False)
    except OSError:
        return None
    return found.stdout.strip() or None


def criteria_floor(text):
    """The salary floor the candidate's own file states, or None.

    The number is theirs and lives in their file, so this reads it rather than
    carrying a default that would be wrong for everyone else who clones the
    template. No stated floor means no band bound, which prints more rows rather
    than the wrong ones.
    """
    match = re.search(r"\$(\d[\d,]*)\s*K\b", text, re.I)
    return int(match[1].replace(",", "")) * 1000 if match else None


def thesis_bullets(text):
    """The opening words of every bullet under `## Role`, lowercased.

    A verdict resting on one of these is about the thesis and does not come
    back, so it is left out of the first section rather than queued for a
    re-read that would reach the same answer.
    """
    opens = re.findall(r"^-\s+(?:\*\*\w+:\*\*\s*)?(.{8,40})",
                       tables.body(text, "Role"), re.M)
    return [" ".join(o.split()).lower() for o in opens]


def pairs(criterion):
    """Every bullet and label force a `criterion` cell names.

    One verdict can rest on more than one rule, because criteria says two or
    three Strongs together sink a role when the verdict says so. A cell holding
    only the first of them would make every honest multi-rule rejection look
    like the invalid single-Strong kind, so the pairs are separated by a
    semicolon and the bullet from its force by the comma inside each.
    """
    found = []
    for part in criterion.split(";"):
        fields = [f.strip() for f in part.split(",") if f.strip()]
        if fields:
            found.append((fields[0].lower(),
                          fields[1].capitalize() if len(fields) > 1 else ""))
    return found


def rests_on_one_strong(criterion):
    """True when a verdict names exactly one rule and that rule is a Strong.

    Criteria says a Strong never fails a role by itself, so this is only a
    problem for a decision that closed the company. A near miss naming one
    Strong is a near miss for exactly that reason and is correct.
    """
    named = pairs(criterion)
    return len(named) == 1 and named[0][1] == "Strong"


def is_thesis(criterion, bullets):
    """True when the cell names only bullets the thesis owns.

    Matched on a shared opening rather than on equality, because the cell quotes
    a bullet's first words and a bullet gets reworded without changing which rule
    it is. Only when every bullet is the thesis is the verdict beyond re-reading:
    one bullet about a company or a posting is enough to make it worth a look.
    """
    named = [b for b, _ in pairs(criterion)]
    return bool(named) and all(
        any(b[:18] in t or t[:18] in b for t in bullets if t) for b in named)


def judgments(root):
    """The newest verdict on each company, with the criteria revision its run
    was judged under.

    Newest wins, because a company judged twice has been re-judged and the
    older row is the thing that got fixed. Reading every row instead reports a
    verdict that was already replaced: the 2026-09-15 pass ruled on 218
    companies without a reason, and a worklist that kept listing them would grow
    by 26 rows on the day those 26 were given one.

    A run written before the criteria stamp existed reports None, which is
    itself the answer: nothing says which version of the rules it used.
    """
    latest = {}
    for run in sorted((root / RUNS).glob("*/judgment.csv")):
        meta = json.loads((run.parent / "run.json").read_text())
        stamp = meta.get("revision", {}).get("criteria_commit")
        with open(run, newline="") as f:
            for row in csv.DictReader(f):
                latest[norm(row.get("company", ""))] = (run.parent.name, stamp, row)
    return list(latest.values())


def live_postings(root):
    """What is open today, keyed by normalized company, with the run's name.

    Read off the newest audit rather than the newest sweep, because an audit
    ignores the seen-cache and so answers what is open rather than what was new
    that morning. A posting the audit dropped at a gate is not a comeback, so
    only the decisions that mean the posting survived its own merits count.
    """
    audits = [d for d in sorted((root / RUNS).glob("*"))
              if (d / "sweep.csv").exists()
              and json.loads((d / "run.json").read_text())["mode"] == "audit"]
    if not audits:
        return {}, None
    found = {}
    with open(audits[-1] / "sweep.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["decision"] in SURVIVED:
                found.setdefault(norm(row["company"]), []).append(row)
    return found, audits[-1].name


def worth_reading(postings, floor):
    """The one posting to put in front of a person, or None.

    Highest band top first, because the top is what says a seat could pay. An
    unposted band is not a known miss, so it qualifies and sorts last.
    """
    fits = [p for p in postings
            if floor is None or (band_top(p["band"]) or floor) >= floor]
    return max(fits, key=lambda p: band_top(p["band"]) or 0, default=None)


def open_company(company, statuses):
    """True when nobody is working this company.

    No row on the board at all, or a row whose status says the search there is
    over. Any other status means someone is on it and a worklist entry would be
    noise.
    """
    for name, status in statuses.items():
        if norm(name) == company:
            return status in CLOSED_STATUSES
    return True


def candidates(root):
    """Every verdict worth a second look, sorted into the three sections."""
    criteria = (root / "profile/criteria.md").read_text()
    floor, bullets = criteria_floor(criteria), thesis_bullets(criteria)
    statuses = tables.statuses((root / "board.md").read_text())
    postings, audit = live_postings(root)
    now = criteria_commit(root)
    stale, single_strong, reasonless = [], [], []
    for run, stamp, row in judgments(root):
        company = norm(row.get("company", ""))
        if (row.get("decision") or "").lower() not in CLOSING:
            continue
        if not open_company(company, statuses):
            continue
        seat = worth_reading(postings.get(company, []), floor)
        if seat is None:
            continue
        criterion = (row.get("criterion") or "").strip()
        found = (run, row, criterion, seat)
        if not criterion and not (row.get("why") or "").strip():
            reasonless.append(found)
        elif criterion and rests_on_one_strong(criterion):
            single_strong.append(found)
        elif criterion and stamp != now and not is_thesis(criterion, bullets):
            stale.append(found)
    return tuple(by_band(s) for s in (stale, single_strong, reasonless)), \
        audit, floor, now


def by_band(found):
    """Best-paying seat first, so a long section is read from the top.

    Criteria asks for a band whose top clears the floor comfortably and puts no
    number on comfortably, so this orders rather than filters and leaves the
    judgment where it belongs. An unposted band sorts last, because it is an
    unknown rather than a good one.
    """
    return sorted(found, key=lambda f: band_top(f[3]["band"]) or 0, reverse=True)


def entry(run, row, criterion, seat):
    """One worklist line: what was decided, on what, and what is open now."""
    verdict = row.get("decision") or "no decision"
    rested = f", on `{criterion}`" if criterion else ", on nothing written down"
    return (f"- **{row.get('company') or 'no company'}**: {verdict} in {run}"
            f"{rested}\n  now: {seat['title']} | {seat['location']} | "
            f"{seat['band'] or 'no band'} | {seat['url']}")


def report(root=ROOT):
    """Print the three sections, or say why there is nothing to print."""
    if not (root / RUNS).is_dir():
        print(f"skipped: no {RUNS} in this instance yet")
        return
    (stale, strong, reasonless), audit, floor, now = candidates(root)
    money = f"a band topping ${floor // 1000}K" if floor else "any band"
    print(f"# Verdicts worth a second look\n\nCriteria is at "
          f"{now or 'an unknown revision'}. Bound: nobody is working the "
          f"company, it has a posting in {audit or 'no audit yet'}, and that "
          f"posting has {money}.\n")
    for title, note, rows in (
        ("Decided under older rules", "The criterion is a fact about a company "
         "or a posting rather than about the thesis, so it can have changed.",
         stale),
        ("Resting on a single Strong", "Criteria says a Strong never fails a "
         "role alone, so each of these was invalid the day it was written "
         "whatever the criteria file did afterward. A verdict that rests on two "
         "or three together is legitimate and names all of them in "
         "`criterion`, so it is not here.", strong),
        ("Decided with no reason written", "Nothing says what these failed, so "
         "nothing can say whether it still holds.", reasonless)):
        print(f"## {title} ({len(rows)})\n\n{note}\n")
        for found in rows:
            print(entry(*found))
        print()


def main():
    report(ROOT)


if __name__ == "__main__":
    main()
