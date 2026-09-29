"""The machine lane of the sweep: fetch, dedupe, filter, digest.

    python3 -m tools.source.sweep            sweep every cataloged channel
    python3 -m tools.source.sweep audit      rerun every gate, ignoring the cache
    python3 -m tools.source.sweep probe X    find company X's ATS board and seats
    python3 -m tools.source.sweep reconcile  kept leads the newest run never judged
    python3 -m tools.source.sweep grades     what the adjudications have measured
    python3 -m tools.source.sweep rejudge    verdicts a criteria edit invalidated

Reads the catalog from source/channels.md (rows with an Endpoint cell), drops
the companies that file's `## Companies` table has closed and what earlier runs
already surfaced (.sweep-seen.json, gitignored), applies the deterministic
gates whose words live in source/gates.md, and prints only what is new.
Judgment against profile/criteria.md stays in the main thread; this prints
facts.

Every run writes learn/runs/<run-id>/, one directory per sweep instance: run.json
and sweep.csv, one row per lead, its decision the gate that fired or "kept".
The adjudication columns start empty and are what makes each gate's error
rate measurable, so fill them in rather than writing prose elsewhere.
"""

import datetime
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

from tools.core import tables
from tools.core.contract import norm
from tools.core.repo import ROOT
from tools.learn.evals import grades, reconcile, write_run
from tools.source import rejudge
from tools.source.boards import FETCHERS, ChannelError
from tools.source.gates import load as load_gates
from tools.source.watch import meets

SEEN = ROOT / ".sweep-seen.json"
RUNS = ROOT / "learn/runs"

# The gate words are source/gates.md, not this file: a search compiled into the
# engine is a search nobody but its author can see. What stays here is the
# funnel, which gate reads which field and in which direction, because an
# allowlist gap is a posting that dies unseen and a denylist gap is one that
# reaches the digest, and that asymmetry is engine behavior rather than taste.
#
# The metro list was once widened past the criteria on the strength of an
# adjudication whose fix cell claimed the criteria had been rewritten to match;
# it had not, and judgment then spent its verdicts rejecting those postings by
# hand, one at a time. Widen a list only when profile/criteria.md says so in its own
# words, and sample that gate's drops afterwards.


class Channel(NamedTuple):
    name: str
    kind: str
    arg: str
    watching: str  # a watchlist row's pass condition; "" for a catalog row


def load_catalog():
    """Rows whose Endpoint cell names a fetcher.

    A four-cell row is a company row and its third cell is the condition; a
    three-cell catalog row carries prose there instead, so cell count is what
    tells them apart.

    Read from those two sections and nowhere else in the file, because a reader
    of every table fetches whatever the next section turns out to hold, and
    `## Not worth fetching` names boards on purpose.
    """
    rows = []
    for cells in tables.rows_under((ROOT / "source/channels.md").read_text(),
                                   "Catalog", "Companies"):
        if len(cells) >= 2:
            kind, _, arg = cells[1].partition(":")
            if kind in FETCHERS:
                rows.append(Channel(cells[0], kind, arg,
                                    cells[2] if len(cells) >= 4 else ""))
    return rows


def decided_names():
    """Companies the repo has a board row or an apply/ directory for.

    Both are evidence that a company was decided rather than a record of what
    was decided, which is what the `## Companies` table holds. Names are matched
    whole and normalized, because a substring match against the pipeline text
    drops every company whose name occurs in prose ("Ada", "Remote").

    A board cell is a markdown link once its company has a file, so the link is
    stripped before the name is normalized. Without that the cell normalizes
    whole, to `abbycareapplyabbycarecompanymd`, which no posting can ever match.
    That was true for months and cost nothing, because a linked row also has the
    `apply/` directory this reads beside it, so the clean name arrived anyway.
    The board half of this function was doing nothing on its own.

    A third source stood here and took every `**bolded**` phrase on board.md,
    which is how Intercom's 27 postings were gated by its own name under
    `## Network assets, not targets`, a section whose first line says the
    company is not the point.
    """
    names = {norm(d.name) for d in (ROOT / "apply").iterdir() if d.is_dir()}
    for cells in tables.rows((ROOT / "board.md").read_text()):
        names.add(norm(tables.unlink(cells[0])))
    return names - {"", norm("Company")}


EMPLOYER_KINDS = {"ashby", "greenhouse", "lever", "smartrecruiters", "workable"}


def company_rows(channels):
    """The `## Companies` table, each row as its display name and condition.

    The condition is lowercased and stripped before anything compares it to
    `never`, because tables.rows takes off the backticks the schema writes that
    token in and leaves the spaces that were inside them. A cell reading `Never`
    or ` never ` otherwise compares unequal and reopens the company silently.

    The display name comes back with it, so a check can name the row a person
    has to go and fix.
    """
    for cells in tables.rows_under(channels, "Companies"):
        if len(cells) >= 3 and norm(cells[0]) not in ("", norm("Company")):
            yield cells[0], cells[2].strip().lower()


def company_criteria(channels, catalog):
    """Each company's condition, keyed by display name and by ATS slug.

    A lead's company comes back from the ATS as the display name or as something
    near the slug ("Acme" against flyacme), and keying on one of the two leaves
    the condition unfound. That fails in whichever direction hurts: a watched
    company's postings would reach the digest unchecked, or a closed company's
    would reopen it.

    Until 2026-09-28 this was two functions over two tables, because a watched
    company and a closed one were different kinds of thing. They are not: both
    rows say what would make a posting here worth reading, and the difference
    between them is the Endpoint cell, which says whether anyone fetches it.
    """
    criteria = {norm(name): condition for name, condition in company_rows(channels)}
    for ch in catalog:
        if ch.kind in EMPLOYER_KINDS and norm(ch.name) in criteria:
            criteria[norm(ch.arg)] = criteria[norm(ch.name)]
    return criteria


def criterion_miss(lead, ctx):
    """True when the company has a row and this posting is not what it is
    waiting for.

    An empty condition passes on any posting, `never` fails on every one, and
    anything else is the watch language, evaluated by tools/source/watch.py.
    """
    condition = ctx["companies"].get(norm(lead.company))
    if condition is None:
        return False
    return condition == "never" or (bool(condition) and not meets(lead, condition))


def fetched_companies(channels):
    """The companies something actually goes and looks at, which is a row with
    an endpoint. A row without one is still a decision; it is just nobody's job
    to check. That distinction used to be which of two tables the row was in."""
    return {norm(cells[0]) for cells in tables.rows_under(channels, "Companies")
            if len(cells) >= 2 and cells[1].strip()
            and norm(cells[0]) not in ("", norm("Company"))}


def decided_miss(lead, ctx):
    """True when the repo shut this company and nobody is watching it.

    Two ways to be shut. `## Companies` says nothing about it and the board or an
    apply/ directory has a row, which is evidence a company was decided rather
    than a record of what was decided, so there is no condition to ask. Or the
    table does carry it, nothing fetches it, and this posting is not what would
    bring it back.

    The pair with company-criterion below is the one thing the merged table had
    to keep: both gates ask the same question of the same cell, and which name
    the digest prints is whether anyone is looking, because "we already decided
    this" and "we are waiting and this is not it" read differently to a person.
    """
    name = norm(lead.company)
    if name not in ctx["companies"]:
        return name in ctx["decided"]
    return name not in ctx["fetched"] and criterion_miss(lead, ctx)


def fetch_all(catalog):
    def run(ch):
        try:
            return ch.name, FETCHERS[ch.kind](ch.arg), None
        except ChannelError as e:
            return ch.name, [], str(e)
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(run, catalog))


def sweep(audit=False):
    """audit=True reruns every gate but the seen-cache and touches nothing,
    so the prediction log covers all live postings, not just today's new."""
    catalog = load_catalog()
    if not catalog:
        sys.exit("no machine channels in source/channels.md; add Endpoint cells first")
    seen = {} if audit else (json.loads(SEEN.read_text()) if SEEN.exists() else {})
    channels = (ROOT / "source/channels.md").read_text()
    ctx = {"seen": seen, "companies": company_criteria(channels, catalog),
           "fetched": fetched_companies(channels), "decided": decided_names(),
           "gates": load_gates(ROOT)}
    started = datetime.datetime.now()
    today = started.date().isoformat()
    rows, fresh, drops, errors, channels, this_run = [], [], {}, [], {}, set()

    for name, leads, err in fetch_all(catalog):
        if err:
            errors.append(f"{name}: {err}")
        channels[name] = len(leads)
        for lead in leads:
            decision = "duplicate" if lead.key() in this_run else judge(lead, ctx)
            this_run.add(lead.key())
            seen.setdefault(lead.key(), today)
            rows.append((decision, lead))
            if decision == "kept":
                fresh.append(lead)
            else:
                drops.setdefault(decision, []).append(lead)

    if not audit:
        SEEN.write_text(json.dumps(seen, indent=0))
    run_dir = RUNS / started.strftime("%Y-%m-%dT%H%M%S")
    write_run(rows, run_dir, {
        "run": run_dir.name, "mode": "audit" if audit else "sweep",
        "started": started.isoformat(timespec="seconds"),
        "finished": datetime.datetime.now().isoformat(timespec="seconds"),
        "decisions": list(DECISIONS), "channels": channels, "errors": errors,
        "counts": {d: len(v) for d, v in sorted(drops.items())} | {"kept": len(fresh)},
    })
    # A company with a written condition gets its own digest section, because a
    # posting that met one is a company coming back rather than a new name. A
    # blank condition is the common case and reads as an ordinary new lead.
    conditions = ctx["companies"]
    hits = [(l, conditions[norm(l.company)]) for l in fresh
            if conditions.get(norm(l.company))]
    print_digest([l for l in fresh if not conditions.get(norm(l.company))],
                 drops, errors, hits, run_dir)


def keeps(ctx, slug, text):
    """A keep-list gate: does this text name something the list allows?

    An empty list keeps everything, because a person who will work anywhere
    wants no metro list rather than a metro list that matches nothing.
    """
    words = ctx["gates"][slug]
    return words is None or bool(words.search(text))


def names(ctx, slug, text):
    """A drop-list gate: does this text name something the list bars?"""
    words = ctx["gates"][slug]
    return words is not None and bool(words.search(text))


STEPS = (
    ("seen-before", lambda l, ctx: l.key() in ctx["seen"]),
    ("already-decided", decided_miss),
    ("wrong-metro", lambda l, ctx: not keeps(ctx, "wrong-metro", l.location)),
    ("title-class", lambda l, ctx: not keeps(ctx, "title-class", l.title)),
    ("ic-seat", lambda l, ctx: names(ctx, "ic-seat", l.title)),
    ("tooling-or-gtm", lambda l, ctx: names(ctx, "tooling-or-gtm", l.title)),
    # Title as well as location, because a posting that means it says so there:
    # "Forward Deployed AI Engineer (Senior/Principal) - based in Austria".
    ("foreign-remote",
        lambda l, ctx: names(ctx, "foreign-remote", l.title + " " + l.location)
        and not names(ctx, "in-us", l.title + " " + l.location)),
    ("company-criterion", criterion_miss),
)


DECISIONS = ("duplicate", *(slug for slug, _ in STEPS), "kept")

def judge(lead, ctx):
    """Walk the funnel and name what happened: the gate that fired, or kept.

    A lead dies at one gate, so one row says everything the eight per-gate
    files used to say between them, as long as run.json keeps the order.
    """
    for slug, drops_it in STEPS:
        if drops_it(lead, ctx):
            return slug
    return "kept"


def why_nothing_survived(drops):
    """The one line a run of zero leads owes whoever asked for leads.

    A heading reading "New leads (0)" over a column of counts looks like a
    quiet market, and it is almost never a quiet market: it is one gate eating
    everything, and the words that gate reads are in a file the candidate
    owns. So name the gate, name the file, and say what to do about it.
    """
    reason, leads = max(drops.items(), key=lambda kv: len(kv[1]))
    total = sum(len(v) for v in drops.values())
    line = f"\nNothing survived: {len(leads)} of {total} postings died at {reason}"
    if reason in ("wrong-metro", "title-class", "ic-seat", "tooling-or-gtm",
                  "foreign-remote"):
        return (f"{line}, which is the `## {reason}` list in source/gates.md. "
                "Change that list to change what the sweep keeps.")
    if reason == "seen-before":
        return (f"{line}, so an earlier run already showed them. "
                "`python3 -m tools.source.sweep audit` replays every live "
                "posting.")
    if reason == "already-decided":
        return (f"{line}, so each of those companies is closed: a row in "
                "source/channels.md's `## Companies` table saying what would "
                "reopen it, or a board row and an apply/ directory that stand "
                "in for one until the table has them all.")
    return line + "."


def print_digest(fresh, drops, errors, hits=(), run_dir=None):
    # "Coming back" rather than the old "Watchlist hits", because the table
    # merged: a company here is one somebody wrote a condition for, whether it
    # was being watched for a seat or closed until one appeared, and a posting
    # that met the condition is the same news either way.
    if hits:
        print(f"## Coming back ({len(hits)})\n")
        for l, criterion in sorted(hits, key=lambda h: h[0].company.lower()):
            print(f"- **{l.company}**: {l.title} | {l.band or 'no band'} | "
                  f"{l.url or ''}")
            print(f"  matched `{criterion}`")
        print()
    print(f"## New leads ({len(fresh)})\n")
    if fresh:
        print("| Company | Title | Location | Band | URL | Source |")
        print("|---|---|---|---|---|---|")
        for l in sorted(fresh, key=lambda l: l.company.lower()):
            cells = (l.company, l.title, l.location, l.band or "", l.url or "",
                     l.source)
            print("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    print("\n## Dropped")
    for reason, leads in sorted(drops.items()):
        line = f"- {len(leads)} {reason}"
        if reason == "already-decided":
            line += ": " + ", ".join(sorted({l.company for l in leads}))
        print(line)
    if not fresh and not hits and drops:
        print(why_nothing_survived(drops))
    for e in errors:
        print(f"- ERROR {e} (a dead channel is not an empty one; fix or note it "
              "in source/channels.md)")
    if run_dir:
        print(f"\nPrediction log: {run_dir}/sweep.csv. Adjudicate a row by "
              "filling its adjudication column with the decision the gate "
              "should have made.")


def probe(company):
    variants = {norm(company), norm(company).replace(" ", ""),
                re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-"),
                company.lower().replace(" ", "")}
    ats_kinds = ("ashby", "greenhouse", "lever", "smartrecruiters", "workable")
    def run(pair):
        kind, slug = pair
        try:
            return kind, slug, FETCHERS[kind](slug)
        except ChannelError:
            return kind, slug, None
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(run, [(k, s) for k in ats_kinds for s in variants])
    hit = False
    for kind, slug, leads in results:
        if leads is None:
            continue
        hit = True
        print(f"## {kind}:{slug} ({len(leads)} open)")
        for l in leads:
            print(f"- {l.title} | {l.location} | {l.band or 'no band'} | {l.url}")
    if not hit:
        print(f"no ATS board answered for {company!r}; the slug may be unusual: "
              "check the apply link on their careers page")


def reconcile_board():
    """Reconcile the newest sweep against everything the repo already knows.

    A slug is not a display name: a company is boarded under the name a person
    types and its leads arrive under the ATS slug, numeric suffix and all, so
    the criteria map keys both ways. Match on one of the two and a company that
    has sat on the board for weeks is reported unjudged, every single run.
    """
    channels = (ROOT / "source/channels.md").read_text()
    reconcile(RUNS, decided_names()
              | set(company_criteria(channels, load_catalog())))


def main(argv):
    command = argv[1] if len(argv) > 1 else ""
    if command == "probe":
        probe(" ".join(argv[2:]) or sys.exit("probe needs a company name"))
    elif command == "reconcile":
        reconcile_board()
    elif command == "grades":
        grades(RUNS)
    elif command == "rejudge":
        rejudge.report(ROOT)
    elif command in ("", "audit"):
        sweep(audit=command == "audit")
    else:
        # --help once ran a full sweep, twice: it refetched every channel,
        # wrote a junk run directory and touched the seen-cache.
        sys.exit(__doc__.strip())


if __name__ == "__main__":
    main(sys.argv)
